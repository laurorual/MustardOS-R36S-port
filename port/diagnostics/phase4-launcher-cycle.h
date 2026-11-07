/* SPDX-License-Identifier: MIT
 * Explicit opt-in diagnostic hook; uses the real presentation/input loop.
 */
#ifndef PHASE4_LAUNCHER_CYCLE_H
#define PHASE4_LAUNCHER_CYCLE_H
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static int port_cycle_phase;
static unsigned port_cycle_wait;
static uint32_t port_cycle_started;
static int port_cycle_painted;
static int port_cycle_finished;
static uint64_t port_cycle_first_serial;
static int port_cycle_configure(const char *phase, const char *wait) {
    port_cycle_phase = port_cycle_painted = port_cycle_finished = 0;
    if (!phase) return wait ? -1 : 0;
    if (!strcmp(phase, "dispatch")) port_cycle_phase = 1;
    else if (!strcmp(phase, "return")) port_cycle_phase = 2;
    else return -1;
    char *end = NULL;
    if (!wait || *wait < '1' || *wait > '9') return -1;
    unsigned long n = strtoul(wait, &end, 10);
    if (!end || *end || !n || n > 30) return -1;
    port_cycle_wait = (unsigned)n;
    return 1;
}
static void port_cycle_tick(void) {
    /* init_input normally supplies this handler; retain its LVGL/render work. */
    ui_common_handle_idle();
    if (!port_cycle_phase || port_cycle_finished) return;
    const uint64_t serial = display_present_serial();
    if (!serial) return;
    if (!port_cycle_painted) {
        port_cycle_started = lv_tick_get();
        port_cycle_first_serial = serial;
        port_cycle_painted = 1;
        printf("C45_LAUNCHER_PRESENT phase=%s serial=%llu\n",
               port_cycle_phase == 1 ? "dispatch" : "return", (unsigned long long)serial);
        fflush(stdout);
    }
    if ((uint32_t)(lv_tick_get() - port_cycle_started) < port_cycle_wait * 1000U) return;
    const char *action = port_cycle_phase == 1 ? "port-retro-diagnostic" : "port-cycle-done";
    printf("C45_LAUNCHER_PROGRESS first=%llu last=%llu\n",
           (unsigned long long)port_cycle_first_serial, (unsigned long long)serial);
    load_mux(action);
    safe_quit(0);
    mux_input_stop();
    port_cycle_finished = 1;
    printf("C45_LAUNCHER_EXIT action=%s\n", action);
    fflush(stdout);
}
#endif
