#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Order/failure tests for the temporary8821cu unload-before-reboot experiment."""
from pathlib import Path
import subprocess,json,tempfile
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
stage=Path(tempfile.mkdtemp(prefix='unload-hooks.',dir=work/'network-tools'))
script=r'''
set -eu
mkdir -p /tmp/bin /sys/module /sys/class/block/mmcblk0p2 /usr/libexec /run/muos/c07
printf '179:2\n' > /sys/class/block/mmcblk0p2/dev
printf 'MUOS-R35S-NETWORK-P4-C07\n' > /tmp/marker
printf '0\n' > /tmp/taint
printf 'BOOT_SEQ=24 FAILED_STEP=network FAILED_RC=1\n' > /run/muos/c07/report.txt
cat > /tmp/bin/readlink <<'EOF'
#!/bin/sh
echo /bin/busybox
EOF
printf '#!/bin/sh\necho 4.4.189-muos-r35s-p4\n' > /tmp/bin/uname
cat > /tmp/bin/findmnt <<'EOF'
#!/bin/sh
case "$*" in
 '-rn -o OPTIONS /') echo "${MOCK_ROOT:-ro}" ;;
 '-rn -o MAJ:MIN /') echo 179:2 ;;
 *) exit 1 ;;
esac
EOF
printf '#!/bin/sh\n[ "${MOCK_UI:-0}" = 1 ]\n' > /tmp/bin/pidof
printf '#!/bin/sh\nexit 1\n' > /tmp/bin/mountpoint
cat > /tmp/bin/mount <<'EOF'
#!/bin/sh
echo "mount:$*" >> /tmp/events
[ "${MOCK_MOUNT_FAIL:-0}" != 1 ]
EOF
printf '#!/bin/sh\necho umount >> /tmp/events\n' > /tmp/bin/umount
cat > /tmp/bin/rmmod <<'EOF'
#!/bin/sh
[ "$*" = 8821cu ] || exit 1
echo rmmod >> /tmp/events
[ "${MOCK_BUSY:-0}" = 0 ] || exit 1
rmdir /sys/module/8821cu
EOF
printf '#!/bin/sh\necho modprobe >> /tmp/events\nmkdir -p /sys/module/8821cu\n' > /tmp/bin/modprobe
printf '#!/bin/sh\necho reboot >> /tmp/events\n' > /tmp/bin/reboot
printf '#!/bin/sh\nshift\nexec "$@"\n' > /usr/libexec/muos-run-bounded
printf '#!/bin/sh\nexit 0\n' > /usr/libexec/muos-rng-ready
printf 'diag_card() { echo /dev/mmcblk0p1; }\n' > /usr/libexec/muos-diag-card-guard
cat > /usr/libexec/muos-c07-network <<'EOF'
#!/bin/sh
echo "network:$1" >> /tmp/events
if [ "$1" = stop ] && [ "${MOCK_STOP_FAIL:-0}" = 1 ]; then exit 1; fi
EOF
chmod 755 /tmp/bin/* /usr/libexec/*
new_case() {
 pkg=/tmp/pkg-$1; mkdir "$pkg"
 mkdir -p /sys/module/8821cu /boot/DIAG09/BOOT0024
 rm -f /boot/DIAG09/BOOT0024/PREBOOT.TXT
 printf 'MUOS-R35S-EXT4-P4-B01\n' > /boot/DIAG.ID
 printf '0\n' > /tmp/taint
 : > /tmp/events
 printf test > "$pkg/public-file"
 sha256sum "$pkg/public-file" > "$pkg/prerequisites.sha256"
 sed -e 's@export PATH=.*@export PATH=/tmp/bin:/usr/sbin:/usr/bin:/sbin:/bin@' \
     -e 's@/etc/muos-network-diagnostic@/tmp/marker@g' \
     -e 's@/proc/sys/kernel/tainted@/tmp/taint@g' \
     -e 's@/sbin/reboot@/tmp/bin/reboot@g' \
     -e 's@> /dev/tty0@> /tmp/screen@g' \
     /port/device/rk-r35s-p0/network-driver-diagnostic/run.sh > "$pkg/run.sh"
}
new_case success
sh "$pkg/run.sh"
[ "$(tail -1 /tmp/events)" = reboot ]
grep -q MODULE_UNLOADED=8821cu /boot/DIAG09/BOOT0024/PREBOOT.TXT
[ "$(cat /tmp/events)" = "$(printf 'network:status\nnetwork:stop\nrmmod\nmount:-t vfat -o ro,nosuid,nodev,noexec /dev/mmcblk0p1 /boot\nmount:-o remount,rw,nosuid,nodev,noexec /boot\numount\nreboot')" ]
new_case busy
if MOCK_BUSY=1 sh "$pkg/run.sh"; then exit 1; fi
! grep -q '^reboot$' /tmp/events
grep -q 'network:recover' /tmp/events
new_case mount-fail
if MOCK_MOUNT_FAIL=1 sh "$pkg/run.sh"; then exit 1; fi
! grep -q '^reboot$' /tmp/events
grep -q 'network:recover' /tmp/events
new_case stop-fail
if MOCK_STOP_FAIL=1 sh "$pkg/run.sh"; then exit 1; fi
! grep -Eq 'rmmod|^reboot$' /tmp/events
grep -q 'network:recover' /tmp/events
new_case rw-root
if MOCK_ROOT=rw sh "$pkg/run.sh"; then exit 1; fi
[ ! -s /tmp/events ]
new_case active-ui
if MOCK_UI=1 sh "$pkg/run.sh"; then exit 1; fi
! grep -Eq 'network:stop|rmmod|^reboot$' /tmp/events
new_case tainted
printf '1\n' > /tmp/taint
if sh "$pkg/run.sh"; then exit 1; fi
[ ! -s /tmp/events ]
printf 'PASS unload order, clean reboot, stop/busy/archive aborts and root/UI/taint guards\n'
'''
args=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--user=0',
 '--tmpfs','/tmp:rw,nosuid,nodev','--tmpfs','/run:rw,nosuid,nodev','--tmpfs','/sys:rw,nosuid,nodev','--tmpfs','/usr/libexec:rw,nosuid,nodev','--tmpfs','/boot:rw,nosuid,nodev',
 '-v',f'{repo}/port:/port:ro,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-c',script]
r=subprocess.run(args,capture_output=True,text=True,timeout=40)
(stage/'stdout.txt').write_text(r.stdout);(stage/'stderr.txt').write_text(r.stderr)
record={'passed':r.returncode==0,'exit':r.returncode,'hardware_tested':False,'cases':['successful stop/unload/archive/unmount/reboot order','module busy aborts and restores network','archive failure aborts and restores network','stop failure prevents removal/reboot','RW root refused','UI active refused','tainted kernel refused']}
(stage/'report.json').write_text(json.dumps(record,indent=2)+'\n');assert r.returncode==0,(stage,r.stderr)
(work/'network-tools/latest-unload-hooks').write_text(str(stage)+'\n');print('Unload-before-reboot fixtures passed:',stage)
