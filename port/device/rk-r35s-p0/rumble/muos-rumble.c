// SPDX-License-Identifier: MIT
/*
 * muos-rumble (M4e): the joypad's rumble motor on RK3326 R36S-family boards.
 *
 *   muos-rumble pulse MS [PERCENT]   play FF_RUMBLE on the gamepad for MS ms
 *   muos-rumble probe [CYCLES]       is a motor fitted? prints per-cycle
 *                                    current deltas and a verdict line:
 *                                    "rumble: present|absent|unknown ..."
 *
 * Every R36S-family device tree (dArkOSen, ROCKNIX, the port's) declares the
 * rumble PWM whether or not a motor is soldered on (the R35S has none), so
 * the probe measures it: battery current from the RK817 fuel gauge's
 * averaging ADC (registers 0x7A/0x7B, ~0.7 s update, read over /dev/i2c-0
 * with I2C_SLAVE_FORCE; the kernel driver owns the chip, reads are
 * harmless) with the motor off, then on, CYCLES times. A coin motor draws
 * 60-100 mA; the menu idles at ~420 mA with +-20 mA of noise between
 * updates. Exit status: 0 present, 1 absent, 2 unknown (e.g. charging), 3
 * error.
 */
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <linux/i2c-dev.h>
#include <linux/i2c.h>
#include <linux/input.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <time.h>
#include <unistd.h>

#define BITS_PER_LONG (sizeof(long) * 8)
#define TEST_BIT(bit, array) (((array)[(bit) / BITS_PER_LONG] >> ((bit) % BITS_PER_LONG)) & 1)

/* The gamepad's event node: muinput hides the physical nodes from
   /dev/input, so open a private char node made from sysfs (as muos-press
   does; /run is nodev) and remove it again. */
static int open_pad(void) {
    DIR *dir = opendir("/sys/class/input");
    if (!dir) return -1;
    struct dirent *entry;
    int found = -1;
    while (found < 0 && (entry = readdir(dir))) {
        if (strncmp(entry->d_name, "event", 5) != 0) continue;
        char path[300];
        snprintf(path, sizeof(path), "/sys/class/input/%s/dev", entry->d_name);
        FILE *f = fopen(path, "r");
        unsigned major = 0, minor = 0;
        const int ok = f && fscanf(f, "%u:%u", &major, &minor) == 2;
        if (f) fclose(f);
        if (!ok) continue;
        snprintf(path, sizeof(path), "/dev/.muos-rumble-%s", entry->d_name);
        unlink(path);
        if (mknod(path, S_IFCHR | 0600, makedev(major, minor)) < 0) continue;
        const int fd = open(path, O_RDWR | O_CLOEXEC);
        unlink(path);
        if (fd < 0) continue;
        unsigned long ff[(FF_MAX + BITS_PER_LONG) / BITS_PER_LONG] = {0};
        if (ioctl(fd, EVIOCGBIT(EV_FF, sizeof(ff)), ff) >= 0 && TEST_BIT(FF_RUMBLE, ff)) {
            found = fd;
        } else {
            close(fd);
        }
    }
    closedir(dir);
    return found;
}

static void sleep_ms(const long ms) {
    struct timespec ts = {ms / 1000, (ms % 1000) * 1000000L};
    while (nanosleep(&ts, &ts) < 0 && errno == EINTR) {
    }
}

/* Upload a rumble effect and start it; returns the effect id or -1. */
static int rumble_start(const int pad, const int percent, const int ms) {
    struct ff_effect effect;
    memset(&effect, 0, sizeof(effect));
    effect.type = FF_RUMBLE;
    effect.id = -1;
    const unsigned magnitude = (unsigned) (0xFFFFu * (unsigned) percent / 100u);
    effect.u.rumble.strong_magnitude = (unsigned short) magnitude;
    effect.u.rumble.weak_magnitude = (unsigned short) magnitude;
    effect.replay.length = (unsigned short) (ms > 0xFFFF ? 0xFFFF : ms);
    if (ioctl(pad, EVIOCSFF, &effect) < 0) return -1;
    struct input_event play;
    memset(&play, 0, sizeof(play));
    play.type = EV_FF;
    play.code = (unsigned short) effect.id;
    play.value = 1;
    if (write(pad, &play, sizeof(play)) != (ssize_t) sizeof(play)) return -1;
    return effect.id;
}

static void rumble_stop(const int pad, const int id) {
    struct input_event stop;
    memset(&stop, 0, sizeof(stop));
    stop.type = EV_FF;
    stop.code = (unsigned short) id;
    stop.value = 0;
    if (write(pad, &stop, sizeof(stop)) < 0) {
    }
    ioctl(pad, EVIOCRMFF, id);
}

static int smbus_read(const int bus, const unsigned char reg) {
    union i2c_smbus_data data;
    struct i2c_smbus_ioctl_data args = {I2C_SMBUS_READ, reg, I2C_SMBUS_BYTE_DATA, &data};
    if (ioctl(bus, I2C_SMBUS, &args) < 0) return -1;
    return data.byte;
}

/* Battery current in mA (positive = discharging), or a value < -100000. */
static int gauge_ma(const int bus) {
    const int high = smbus_read(bus, 0x7A), low = smbus_read(bus, 0x7B);
    if (high < 0 || low < 0) return -1000000;
    int raw = (high << 8) | low;
    if (raw & 0x8000) raw -= 0x10000;
    return -(raw * 172 / 1000); /* rk817_battery.c ADC_TO_CURRENT, res_div 1 */
}

/* Mean of the gauge readings over MS ms (sampled every 50 ms). */
static int mean_ma(const int bus, const int ms) {
    long sum = 0;
    int count = 0;
    for (int t = 0; t < ms; t += 50) {
        const int ma = gauge_ma(bus);
        if (ma > -100000) {
            sum += ma;
            count++;
        }
        sleep_ms(50);
    }
    return count ? (int) (sum / count) : -1000000;
}

static int cmp_int(const void *a, const void *b) {
    return *(const int *) a - *(const int *) b;
}

static int probe(const int pad, const int cycles) {
    const int bus = open("/dev/i2c-0", O_RDWR | O_CLOEXEC);
    if (bus < 0 || ioctl(bus, I2C_SLAVE_FORCE, 0x20) < 0) {
        perror("muos-rumble: /dev/i2c-0");
        return 3;
    }
    int deltas[16];
    int n = 0, base_sum = 0;
    for (int c = 0; c < cycles && c < 16; c++) {
        sleep_ms(600); /* let the previous phase leave the averaging ADC */
        const int off = mean_ma(bus, 1200);
        const int id = rumble_start(pad, 100, 2000);
        if (id < 0) {
            perror("muos-rumble: rumble");
            close(bus);
            return 3;
        }
        sleep_ms(600);
        const int on = mean_ma(bus, 1200);
        rumble_stop(pad, id);
        if (off < -100000 || on < -100000) continue;
        if (off < 50) {
            printf("cycle %d: %d mA: not discharging\n", c + 1, off);
            close(bus);
            puts("rumble: unknown (not discharging)");
            return 2;
        }
        deltas[n++] = on - off;
        base_sum += off;
        printf("cycle %d: off %d mA, on %d mA, delta %+d mA\n", c + 1, off, on, on - off);
    }
    close(bus);
    if (n < 3) {
        puts("rumble: unknown (too few readings)");
        return 2;
    }
    qsort(deltas, (size_t) n, sizeof(int), cmp_int);
    const int median = deltas[n / 2], low = deltas[0];
    const char *verdict = median >= 35 && low >= 15 ? "present" : median < 15 ? "absent" : "unknown";
    printf("rumble: %s (median %+d mA, min %+d mA, base %d mA, %d cycles)\n", verdict, median, low, base_sum / n, n);
    return verdict[0] == 'p' ? 0 : verdict[0] == 'a' ? 1 : 2;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fputs("usage: muos-rumble pulse MS [PERCENT] | probe [CYCLES]\n", stderr);
        return 3;
    }
    const int pad = open_pad();
    if (pad < 0) {
        fputs("muos-rumble: no gamepad with FF_RUMBLE\n", stderr);
        return 3;
    }
    if (strcmp(argv[1], "pulse") == 0 && argc >= 3) {
        const int ms = atoi(argv[2]), percent = argc >= 4 ? atoi(argv[3]) : 100;
        if (ms <= 0 || percent <= 0 || percent > 100) return 3;
        const int id = rumble_start(pad, percent, ms);
        if (id < 0) {
            perror("muos-rumble: rumble");
            return 3;
        }
        sleep_ms(ms);
        rumble_stop(pad, id);
        return 0;
    }
    if (strcmp(argv[1], "probe") == 0) return probe(pad, argc >= 3 ? atoi(argv[2]) : 4);
    fputs("usage: muos-rumble pulse MS [PERCENT] | probe [CYCLES]\n", stderr);
    return 3;
}
