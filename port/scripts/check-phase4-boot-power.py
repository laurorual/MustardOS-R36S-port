#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Power transaction fault tests; real controller/archive, disposable container only."""
from pathlib import Path
import hashlib, json, subprocess, tempfile

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
area = work / 'boot-order'
stage = Path(tempfile.mkdtemp(prefix='power-checks.', dir=area))
script = r'''
set -eu
mkdir -p /tmp/package/bin /tmp/mock /run/muos /boot
cp /port/device/rk-r35s-p0/boot/*.sh /tmp/package/
# Board and mount operations replaced only in this isolated fixture.
printf '\nc12_guard() { boot_partition=/dev/fixture; [ ! -e /tmp/mounted ]; }\n' >> /tmp/package/native-functions.sh
sed -i 's|export PATH=/usr/sbin:/usr/bin:/sbin:/bin|export PATH=/tmp/mock:/usr/sbin:/usr/bin:/sbin:/bin|' /tmp/package/diagnostic-save.sh
cat > /tmp/package/bin/muos-run-bounded <<'EOF'
#!/bin/sh
shift
exec "$@"
EOF
cat > /tmp/package/step.sh <<'EOF'
#!/bin/sh
echo "$1" >> /tmp/events
case "$1" in
  power.check) [ "$MODE" = c12 ] && [ ! -e /run/muos/boot/stopped ] || exit 64 ;;
  power.sealed)
    [ -e /run/muos/boot/stopped ] || exit 1
    [ ! -e /tmp/mounted ] || exit 1
    count=$(grep -cx power.sealed /tmp/events)
    [ "$FAIL" != "sealed:$count" ] || exit 1 ;;
esac
[ "$FAIL" != "$1" ]
EOF
cat > /tmp/mock/mount <<'EOF'
#!/bin/sh
echo "mount $*" >> /tmp/events
phase=$(ls /run/muos/boot-diagnostic/P*.txt 2>/dev/null | sort | tail -n1)
if [ "${ARCHIVE_FAIL:-}" = "$phase" ] && [ ! -e /tmp/archive-failed ]; then touch /tmp/archive-failed; exit 1; fi
touch /tmp/mounted
EOF
cat > /tmp/mock/umount <<'EOF'
#!/bin/sh
echo umount >> /tmp/events
[ "$FAIL" != unmount ] || exit 1
rm -f /tmp/mounted
EOF
cat > /tmp/mock/sync <<'EOF'
#!/bin/sh
echo sync >> /tmp/events
[ "$FAIL" != sync ]
EOF
for action in reboot poweroff; do
    rm -f /sbin/$action
    printf '#!/bin/sh\necho request-%s >> /tmp/events\n' "$action" > /sbin/$action
    chmod 755 /sbin/$action
done
chmod 755 /tmp/package/*.sh /tmp/package/bin/* /tmp/mock/*
export MUOS_BOOT_CONFIG=/tmp/config MODE=c12 FAIL= ARCHIVE_FAIL=
printf 'enabled=1\nallow_power=1\n' > /tmp/config
chmod 600 /tmp/config
pass() { echo "PASS $1"; }
refuse() { if "$@"; then echo unexpected-success >&2; exit 1; fi; }
reset() {
    rm -rf /run/muos/boot /run/muos/boot-diagnostic /boot/DIAG10
    mkdir -p /run/muos/boot/start-once /run/muos/boot-diagnostic /boot/DIAG10/BOOT0030
    echo 30 > /run/muos/boot-diagnostic/sequence
    echo public-final > /run/muos/boot-diagnostic/FINAL.txt
    cp /run/muos/boot-diagnostic/FINAL.txt /boot/DIAG10/BOOT0030/FINAL.TXT
    echo public-start > /boot/DIAG10/BOOT0030/START.TXT
    echo MUOS-R35S-EXT4-P4-B01 > /boot/DIAG.ID
    rm -f /tmp/mounted /tmp/archive-failed
    : > /tmp/events
    FAIL=; ARCHIVE_FAIL=; MODE=c12
}
no_request() { ! grep -q '^request-' /tmp/events; [ ! -e /run/muos/boot/power-request ]; }
reset;MODE=c07;refuse /tmp/package/service.sh reboot
no_request;[ ! -e /run/muos/boot/power ];pass C07-no-transaction
for action in reboot poweroff; do
    reset;/tmp/package/service.sh "$action"
    [ "$(tail -n1 /tmp/events)" = "request-$action" ]
    [ ! -e /tmp/mounted ]
    for phase in PBEGIN PREADY; do
        cmp /run/muos/boot-diagnostic/$phase.txt /boot/DIAG10/BOOT0030/$phase.TXT
    done
    [ "$(grep -c '^STEP=' /boot/DIAG10/BOOT0030/PREADY.TXT)" = 6 ]
    grep -qx OUTCOME=preflight-complete /boot/DIAG10/BOOT0030/PREADY.TXT
    python3 - <<'PY'
from pathlib import Path
e=Path('/tmp/events').read_text().splitlines()
stop=['session.stop','session.quiescent','network.stop','udev.stop','root.sync','root.seal']
assert [x for x in e if x in stop] == stop
assert e.index('umount') < e.index('session.stop')
assert e[-3:] == ['umount','power.sealed',e[-1]] and e[-1].startswith('request-')
PY
    pass durable-six-steps-before-$action
    cp /boot/DIAG10/BOOT0030/PREADY.TXT /tmp/approved
    refuse /tmp/package/service.sh "$action"
    cmp /tmp/approved /boot/DIAG10/BOOT0030/PREADY.TXT
    [ "$(grep -c '^request-' /tmp/events)" = 1 ];pass no-repeat-$action
done
for failed in session.stop session.quiescent network.stop udev.stop root.sync root.seal; do
    reset;FAIL=$failed;refuse /tmp/package/service.sh reboot
    no_request
    grep -qx "STEP=$failed LIMIT=[0-9]* RC=1" /boot/DIAG10/BOOT0030/PFAIL.TXT
    [ ! -e /boot/DIAG10/BOOT0030/PREADY.TXT ]
    pass durable-abort-$failed
done
for phase in PBEGIN PREADY; do
    reset;ARCHIVE_FAIL=/run/muos/boot-diagnostic/$phase.txt
    refuse /tmp/package/service.sh poweroff;no_request
    if [ "$phase" = PBEGIN ]; then ! grep -qx session.stop /tmp/events
    else grep -qx OUTCOME=archive-failed /boot/DIAG10/BOOT0030/PFAIL.TXT;fi
    pass archive-failure-blocks-$phase
done
for failed in sealed:1 sealed:2; do
    reset;FAIL=$failed;refuse /tmp/package/service.sh reboot;no_request
    [ -f /boot/DIAG10/BOOT0030/PFAIL.TXT ];pass recheck-blocks-$failed
done
for failed in sync unmount; do
    reset;FAIL=$failed;refuse /tmp/package/service.sh reboot;no_request
    ! grep -qx session.stop /tmp/events;pass archive-$failed-blocks-before-network
done
reset;echo mismatch > /boot/DIAG10/BOOT0030/FINAL.TXT
refuse /tmp/package/service.sh reboot;no_request
! grep -qx session.stop /tmp/events;pass incomplete-durable-final-blocks-stop
reset;echo immutable > /boot/DIAG10/BOOT0030/PBEGIN.TXT
refuse /tmp/package/service.sh reboot;no_request
[ "$(cat /boot/DIAG10/BOOT0030/PBEGIN.TXT)" = immutable ];pass previous-proof-never-overwritten
reset;ln -s /tmp/foreign /run/muos/boot/power
refuse /tmp/package/service.sh reboot;no_request
[ ! -e /tmp/foreign ];pass foreign-power-state-refused

# Directed update and rollback on a synthetic card tree, no remount/device calls.
. /port/device/rk-r35s-p0/boot-diagnostic/install-functions.sh
. /port/device/rk-r35s-p0/boot-diagnostic/power-update-functions.sh
update_root=/tmp/card;update_payload=/tmp/update
update_exec() {
    echo "$1" >> /tmp/update-events
    if [ "$1" = file-installed ] && [ "$UPDATE_FAIL" = "$2" ]; then return 1; fi
    return 0
}
reset_update() {
    rm -rf "$update_root" "$update_payload"
    mkdir -p "$update_root/usr/libexec/muos-boot" "$update_payload/new"
    for name in order.sh native-functions.sh diagnostic-save.sh service.sh; do
        echo "old-$name" > "$update_root/usr/libexec/muos-boot/$name"
    done
    for name in power-functions.sh order.sh native-functions.sh diagnostic-save.sh service.sh; do
        echo "new-$name" > "$update_payload/new/$name"
    done
    (cd "$update_root";sha256sum usr/libexec/muos-boot/* > "$update_payload/installed-before.sha256")
    (cd "$update_payload/new";sha256sum * > ../new.sha256)
    : > /tmp/update-events;UPDATE_FAIL=;update_rw=0
}
reset_update;c12_update_apply
[ "$update_rw" = 0 ]
[ "$(cat "$update_root/usr/libexec/muos-boot/service.sh")" = new-service.sh ];pass directed-update-five-public-files
for failed in power-functions.sh order.sh native-functions.sh diagnostic-save.sh service.sh; do
    reset_update;UPDATE_FAIL=$failed;refuse c12_update_apply;c12_update_rollback
    (cd "$update_root";sha256sum -c "$update_payload/installed-before.sha256" >/dev/null)
    [ ! -e "$update_root/usr/libexec/muos-boot/power-functions.sh" ];[ "$update_rw" = 0 ]
    pass rollback-after-$failed
done
reset_update;echo corrupt >> "$update_payload/new/service.sh"
refuse c12_update_apply;! grep -qx rw /tmp/update-events;pass corrupt-update-refused-before-rw
reset_update;mv "$update_root/usr/libexec" /tmp/foreign-libexec;ln -s /tmp/foreign-libexec "$update_root/usr/libexec"
refuse c12_update_apply;! grep -qx rw /tmp/update-events;pass symlink-update-ancestor-refused

# Run the actual wrapper's originals branch from a foreign cwd. Relative public
# manifests must resolve from /, not the upload directory used by Dropbear.
mkdir -p /usr/libexec/muos-session /tmp/cwd-regression
printf public > /tmp/cwd-public
(cd /;sha256sum tmp/cwd-public > /tmp/cwd-regression/unchanged.sha256)
sha256sum /tmp/cwd-public > /usr/libexec/muos-session/prerequisites.sha256
update_payload=/tmp/cwd-regression
originals_command=$(sed -n 's/^      originals) \(.*\) ;;$/\1/p' /port/device/rk-r35s-p0/boot-diagnostic/power-update.sh)
[ -n "$originals_command" ]
(cd /tmp;eval "$originals_command" >/dev/null)
pass actual-wrapper-originals-independent-of-cwd
'''
command = ['podman', 'run', '--rm', '--network=none', '--cap-drop=all',
           '--security-opt=no-new-privileges', '--userns=keep-id', '--user=0',
           '--tmpfs', '/run:rw,nosuid,nodev', '--tmpfs', '/tmp:rw,nosuid,nodev',
           '-v', f'{repo}/port:/port:ro,z', (work/'rootfs-container.iid').read_text().strip(),
           'sh', '-c', script]
(stage/'fixture.sh').write_text(script)
r = subprocess.run(command, capture_output=True, text=True, timeout=60)
(stage/'stdout').write_text(r.stdout); (stage/'stderr').write_text(r.stderr)
assert r.returncode == 0, (stage, r.stdout, r.stderr)
cases = [line[5:] for line in r.stdout.splitlines() if line.startswith('PASS ')]
assert len(cases) == 29, cases
sources = [*sorted((repo/'port/device/rk-r35s-p0/boot').glob('*')),
           *sorted((repo/'port/device/rk-r35s-p0/boot-diagnostic').glob('*')), Path(__file__)]
report = {'passed': True, 'case_count': len(cases), 'cases': cases,
          'device_or_real_power_executed': False, 'mount_board_steps_mocked': True,
          'sources': {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in sources if p.is_file()}}
(stage/'report.json').write_text(json.dumps(report, indent=2)+'\n')
(area/'latest-power-checks').write_text(str(stage)+'\n')
print('C12 durable power preflight:', len(cases), 'cases passed;', stage)
