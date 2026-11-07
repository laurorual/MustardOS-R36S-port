#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C12 one-shot selector, recovery and public archive fault fixtures."""
from pathlib import Path
import hashlib,json,subprocess,tempfile
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'boot-order'
stage=Path(tempfile.mkdtemp(prefix='diagnostic-checks.',dir=area))
script=r'''
set -eu
pass() { echo "PASS $1"; }
refuse() { if "$@"; then echo 'unexpected success' >&2; exit 1; fi; }
. /port/device/rk-r35s-p0/boot/select-functions.sh
selector_dir=/tmp/persistent;selector_state=/tmp/selection
mkdir "$selector_dir"
selector_exec() { echo "$1" >> /tmp/events; [ "${FAIL:-}" != "$1" ]; }
reset() { rm -rf "$selector_state"; rm -f "$selector_dir/c12.once" "$selector_dir/c12.used"; : > /tmp/events; FAIL=; }
token() { printf 'MUOS-C12-ONCE\n' > "$selector_dir/c12.once"; chmod 600 "$selector_dir/c12.once"; }
reset;c12_select_start;[ "$(cat /tmp/events)" = c07 ];pass default-C07
refuse c12_select_start;[ "$(wc -l < /tmp/events)" = 1 ];pass no-second-bootstrap-in-boot
reset;token;c12_select_start
[ ! -e "$selector_dir/c12.once" ] && [ -f "$selector_dir/c12.used" ]
[ "$(tr '\n' ' ' < /tmp/events)" = 'c12-config sync c12 ' ];pass consume-before-C12
rm -rf "$selector_state";: > /tmp/events;c12_select_start;[ "$(cat /tmp/events)" = c07 ];pass next-boot-C07
reset;token;FAIL=c12;refuse c12_select_start
! grep -qx c07 /tmp/events;[ ! -e "$selector_dir/c12.once" ];pass failed-C12-never-starts-C07-same-boot
c12_select_stop;[ "$(tail -n1 /tmp/events)" = c12-stop ];pass stop-owned-C12
reset;c12_select_start;c12_select_stop;[ "$(tail -n1 /tmp/events)" = c07-stop ];pass stop-owned-C07
reset;token;FAIL=c12-config;c12_select_start;[ "$(tail -n1 /tmp/events)" = c07 ];[ -f "$selector_dir/c12.once" ];pass disabled-C12-not-selected
reset;token;chmod 666 "$selector_dir/c12.once";c12_select_start;[ "$(cat /tmp/events)" = c07 ];pass writable-token-refused
reset;ln -s /tmp/secret "$selector_dir/c12.once";c12_select_start;[ "$(cat /tmp/events)" = c07 ];pass symlink-token-refused
reset;token;printf BAD > "$selector_dir/c12.once";c12_select_start;[ "$(cat /tmp/events)" = c07 ];pass malformed-token-refused
reset;token;FAIL=sync;refuse c12_select_start;! grep -qx c12 /tmp/events;[ ! -e "$selector_dir/c12.once" ];pass sync-failure-does-not-start-C12

. /port/device/rk-r35s-p0/boot/order.sh
boot_state=/tmp/boot;recover_network=1
boot_exec() {
    echo "$1" >> "$boot_state/events"
    count=$(grep -cx "$1" "$boot_state/events")
    case " $FAIL " in *" $1:$count "*|*" $1 "*) return 1 ;; esac
    return 0
}
reset_boot() { rm -rf "$boot_state";mkdir "$boot_state";FAIL=network.start; }
reset_boot;c12_start || exit 1
[ "$(cat "$boot_state/network-mode")" = recovered ]
[ "$(grep -cx entropy.start "$boot_state/events")" = 1 ];pass recovery-current-RNG-no-reload
python3 - "$boot_state/events" <<'PY'
from pathlib import Path
import sys
e=Path(sys.argv[1]).read_text().splitlines()
assert e.index('entropy.stop')<e.index('recovery.ready')<e.index('usb.wait-remove')<e.index('usb.wait-add')<e.index('network.recover')<e.index('session.start')
PY
pass recovery-before-session-and-after-seed-stop
refuse c12_recover_network;[ "$(grep -cx usb.wait-remove "$boot_state/events")" = 1 ];pass physical-recovery-only-once
for failed in recovery.ready usb.wait-remove usb.wait-add network.recover network.status; do
    reset_boot;FAIL="network.start $failed";c12_start || exit 1
    [ "$(cat "$boot_state/network-mode")" = offline ];grep -qx session.start "$boot_state/events";pass offline-after-$failed
done
reset_boot;FAIL='network.start network.recover network.stop:3';refuse c12_start
! grep -qx session.start "$boot_state/events";pass dirty-recovery-blocks-UI

# Real archive script, with board/mount operations replaced only in this fixture.
mkdir -p /tmp/package/bin /tmp/mock /run/muos/boot-diagnostic /boot
cp /port/device/rk-r35s-p0/boot/diagnostic-save.sh /tmp/package/
sed -i 's|export PATH=/usr/sbin:/usr/bin:/sbin:/bin|export PATH=/tmp/mock:/usr/sbin:/usr/bin:/sbin:/bin|' /tmp/package/diagnostic-save.sh
cp /port/device/rk-r35s-p0/boot/native-functions.sh /tmp/package/
printf '\nc12_guard() { boot_partition=/dev/fixture; return 0; }\n' >> /tmp/package/native-functions.sh
cat > /tmp/mock/mount <<'EOF'
#!/bin/sh
echo "mount $*" >> /tmp/mount-events
[ "${MOUNT_FAIL:-}" != "$1" ]
EOF
cat > /tmp/mock/umount <<'EOF'
#!/bin/sh
echo "umount $*" >> /tmp/mount-events
exit 0
EOF
chmod 755 /tmp/package/diagnostic-save.sh /tmp/mock/*
export PATH=/tmp/mock:$PATH MOUNT_FAIL=
echo MUOS-R35S-EXT4-P4-B01 > /boot/DIAG.ID
echo 27 > /run/muos/boot-diagnostic/sequence
echo public-start > /run/muos/boot-diagnostic/START.txt
echo public-final > /run/muos/boot-diagnostic/FINAL.txt
sh /tmp/package/diagnostic-save.sh START
cmp /run/muos/boot-diagnostic/START.txt /boot/DIAG10/BOOT0027/START.TXT
[ "$(tail -n1 /tmp/mount-events)" = 'umount /boot' ];pass archive-start-unmounted
refuse sh /tmp/package/diagnostic-save.sh START
[ "$(cat /boot/DIAG10/BOOT0027/START.TXT)" = public-start ];pass original-report-not-overwritten
sh /tmp/package/diagnostic-save.sh FINAL
cmp /run/muos/boot-diagnostic/FINAL.txt /boot/DIAG10/BOOT0027/FINAL.TXT;pass separate-final-report
refuse sh /tmp/package/diagnostic-save.sh FINAL;pass final-report-not-overwritten
echo 28 > /run/muos/boot-diagnostic/sequence;echo WRONG > /boot/DIAG.ID
refuse sh /tmp/package/diagnostic-save.sh START
[ ! -e /boot/DIAG10/BOOT0028 ];[ "$(tail -n1 /tmp/mount-events)" = 'umount /boot' ];pass wrong-media-no-write-unmounted
echo MUOS-R35S-EXT4-P4-B01 > /boot/DIAG.ID
MOUNT_FAIL=-o;export MOUNT_FAIL
refuse sh /tmp/package/diagnostic-save.sh START
[ ! -e /boot/DIAG10/BOOT0028 ];[ "$(tail -n1 /tmp/mount-events)" = 'umount /boot' ];pass failed-remount-no-write-unmounted
MOUNT_FAIL=;export MOUNT_FAIL
python3 - <<'PY'
from pathlib import Path
Path('/run/muos/boot-diagnostic/START.txt').write_bytes(b'x'*65537)
PY
refuse sh /tmp/package/diagnostic-save.sh START;[ ! -e /boot/DIAG10/BOOT0028 ];pass oversized-report-refused

. /port/device/rk-r35s-p0/boot-diagnostic/install-functions.sh
install_root=/;c12_install_parents //usr/libexec/muos-boot/select.sh
pass native-double-slash-root-parent-terminates
install_root=/tmp/card;install_payload=/tmp/install-payload;mkdir -p "$install_payload/tree/usr/libexec/muos-boot"
echo original-C07 > "$install_payload/inittab.c07"
echo selected-init > "$install_payload/inittab.selected"
sha256sum "$install_payload/inittab.c07" | cut -d' ' -f1 > "$install_payload/inittab-before.sha256"
echo selector > "$install_payload/tree/usr/libexec/muos-boot/select.sh"
printf '755 usr/libexec/muos-boot/select.sh\n' > "$install_payload/MODES"
(cd "$install_payload/tree";sha256sum usr/libexec/muos-boot/select.sh > ../SHA256SUMS)
install_exec() { echo "$1" >> /tmp/install-events; [ "${INSTALL_FAIL:-}" != "$1" ]; }
reset_install() {
    rm -rf "$install_root";mkdir -p "$install_root/etc" "$install_root/var/lib/muos-diagnostic" "$install_root/usr/libexec"
    cp "$install_payload/inittab.c07" "$install_root/etc/inittab"
    echo C07-helper > "$install_root/usr/libexec/muos-c07-run"
    : > /tmp/install-events;INSTALL_FAIL=;install_rw=0
}
reset_install;c12_install_apply
[ "$(cat "$install_root/etc/inittab")" = selected-init ]
[ "$(cat "$install_root/var/lib/muos-diagnostic/c12.once")" = MUOS-C12-ONCE ];[ "$install_rw" = 0 ];pass targeted-install-arm-last
for failed in file-installed selection-installed; do
    reset_install;INSTALL_FAIL=$failed;refuse c12_install_apply;c12_install_rollback
    cmp "$install_root/etc/inittab" "$install_payload/inittab.c07"
    [ ! -e "$install_root/var/lib/muos-diagnostic/c12.once" ] && [ ! -e "$install_root/usr/libexec/muos-boot" ]
    [ "$(cat "$install_root/usr/libexec/muos-c07-run")" = C07-helper ];pass rollback-after-$failed
done
reset_install;mkdir "$install_root/usr/libexec/muos-session";refuse c12_install_apply
! grep -qx rw /tmp/install-events;pass foreign-session-install-refused
reset_install;echo CORRUPT >> "$install_payload/tree/usr/libexec/muos-boot/select.sh";refuse c12_install_apply
! grep -qx rw /tmp/install-events;pass corrupt-payload-before-rw
echo selector > "$install_payload/tree/usr/libexec/muos-boot/select.sh"
reset_install;rm -rf "$install_root/usr/libexec";mkdir /tmp/foreign-install;ln -s /tmp/foreign-install "$install_root/usr/libexec"
refuse c12_install_apply;! grep -qx rw /tmp/install-events;[ -z "$(ls -A /tmp/foreign-install)" ];pass symlink-ancestor-install-refused
'''
container=['podman','run','--rm','--network=none','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--user=0','--tmpfs','/run:rw,nosuid,nodev','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{repo}/port:/port:ro,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-c',script]
(stage/'fixture.sh').write_text(script)
r=subprocess.run(container,capture_output=True,text=True,timeout=45);(stage/'stdout').write_text(r.stdout);(stage/'stderr').write_text(r.stderr)
assert r.returncode==0,(stage,r.stdout,r.stderr)
cases=[x[5:] for x in r.stdout.splitlines() if x.startswith('PASS ')];assert len(cases)==35,cases
sources=[*sorted((repo/'port/device/rk-r35s-p0/boot').iterdir()),*sorted((repo/'port/device/rk-r35s-p0/boot-diagnostic').iterdir()),Path(__file__)]
report={'passed':True,'cases':cases,'case_count':len(cases),'real_device_power_seed_network_mount_used':False,'fixture_board_and_mount_callbacks_overridden':True,'sources':{str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources if p.is_file()}}
(stage/'report.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-diagnostic-checks').write_text(str(stage)+'\n');print('C12 selector/recovery/public archive checks passed:',len(cases),stage)
