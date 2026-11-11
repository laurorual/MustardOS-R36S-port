#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# T1: the init shim (/sbin/muos-ext4-diag) in a throwaway container.
# mount/umount/pivot_root/chroot/sync are logging stubs, so each branch can
# be driven: no marker, trial root OK, and failures at every step before
# pivot_root (each must fall back to /sbin/init on p2 with the marker gone).
# The shim's syntax is also checked by the target's AArch64 BusyBox (qemu).
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
shim=$repo/port/device/rk-r35s-p0/rootfs/sbin/muos-ext4-diag
sysroot=$repo/build/phase4/graphics-config/output/target
podman run --rm --network=none -v "$shim:/shim:ro,z" -v "$sysroot:/sysroot:ro,z" \
    "$(cat "$repo/build/phase4/rootfs-container.iid")" bash -euc '
qemu-aarch64 -L /sysroot /sysroot/bin/busybox sh -n /shim && echo "ok busybox ash syntax"
mkdir -p /stub /sbin /etc
cat > /stub/mount <<"EOF"
#!/bin/sh
echo "mount $*" >> /log
case " $* " in
  *" -t proc "*|*" -t sysfs "*) exit 0 ;;
  *remount,rw*) [ "${FAIL:-}" = rw ] && exit 1 ;;
  *remount,ro*) [ "${FAIL:-}" = ro ] && exit 1 ;;
  *" -t tmpfs "*) [ "${FAIL:-}" = tmpfs ] && exit 1 ;;
  *mmcblk0p3*) [ "${FAIL:-}" = p3 ] && exit 1 ;;
  *loop,ro*) [ "${FAIL:-}" = loop ] && exit 1
     r=/tmp/root; mkdir -p $r/sbin $r/media $r/dev $r/proc $r/sys
     [ "${FAIL:-}" = layout ] || mkdir -p $r/userdata
     printf "#!/bin/sh\n" > $r/sbin/muos-ext4-diag; printf "#!/bin/sh\n" > $r/sbin/init
     chmod +x $r/sbin/muos-ext4-diag $r/sbin/init ;;
  *"--move /tmp/p3 "*) [ "${FAIL:-}" = move ] && exit 1 ;;
esac
exit 0
EOF
printf "#!/bin/sh\necho \"umount \$*\" >> /log\n" > /stub/umount
printf "#!/bin/sh\necho \"pivot_root \$*\" >> /log\n[ \"\${FAIL:-}\" = pivot ] && exit 1\nexit 0\n" > /stub/pivot_root
printf "#!/bin/sh\necho \"chroot \$*\" >> /log\necho TRIAL >> /log\n" > /stub/chroot
printf "#!/bin/sh\n:\n" > /stub/sync
printf "#!/bin/sh\necho \"init \$*\" >> /log\necho P2 >> /log\n" > /sbin/init
chmod +x /stub/* /sbin/init
run() { # run NAME MARKER FAIL EXPECT
    rm -rf /tmp/p3 /tmp/root /log; : > /log
    if [ "$2" = 1 ]; then : > /etc/muos-root-trial; else rm -f /etc/muos-root-trial; fi
    (cd / && PATH=/stub:$PATH FAIL=$3 sh /shim quiet) 2>/dev/null || :
    last=$(tail -1 /log)
    [ "$last" = "$4" ] || { echo "FAIL $1: ended $last, want $4"; cat /log; exit 1; }
    if [ "$2" = 1 ] && [ "$3" != rw ] && [ -e /etc/muos-root-trial ]; then echo "FAIL $1: marker kept"; exit 1; fi
    echo "ok $1 -> $last"
}
run no-marker 0 "" P2
run trial 1 "" TRIAL
grep -q "^pivot_root . media$" /log && grep -q "^chroot . /sbin/muos-ext4-diag quiet$" /log && echo "ok trial pivots into media and keeps args"
for f in rw ro tmpfs p3 loop layout move pivot; do run "fail-$f" 1 "$f" P2; done
run fail-pivot 1 pivot P2
grep -q "^mount --move /tmp/root/userdata /tmp/p3$" /log && grep -q "^umount /tmp/root$" /log && echo "ok pivot failure undoes the mounts"
echo PASS'
