#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Explicit steps for the authorized C12 durable-reboot qualification on test128."""
from pathlib import Path
import argparse, hashlib, ipaddress, json, subprocess

repo = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('action', choices=['arm', 'boot', 'request', 'return'])
p.add_argument('stage', type=Path); p.add_argument('--host', required=True, type=ipaddress.IPv4Address)
a = p.parse_args(); stage = a.stage.resolve()
assert stage.is_relative_to(repo/'build/phase4/boot-order')
meta = json.loads((stage/'manifest.json').read_text())
assert json.loads((stage/'install-analysis.json').read_text())['passed']
ssh = ['ssh', '-p', '2222', '-i', str(repo/'build/phase4/private/c07-client'),
       '-oIdentitiesOnly=yes', '-oStrictHostKeyChecking=yes', '-oHostKeyAlias=[192.168.15.17]:2222',
       '-oUserKnownHostsFile='+str(repo/'build/phase4/private/c07-known_hosts'), '-oBatchMode=yes',
       '-oConnectTimeout=8', 'root@'+str(a.host)]
def remote(label, code, timeout=35):
    (stage/(label+'.sh')).write_text(code)
    r = subprocess.run(ssh+['sh -s'], input=code, text=True, capture_output=True, timeout=timeout)
    for suffix, value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:
        (stage/(label+'.'+suffix)).write_text(value)
    assert r.returncode == 0, (label,r.stdout,r.stderr)
    return r.stdout
sums = ''.join(v['sha256']+'  /'+n+'\n' for n,v in sorted(meta['installed_files'].items()))
guard = '''set -eu
boot_package=/usr/libexec/muos-boot
. "$boot_package/native-functions.sh"
c12_guard;c12_read_config;c12_root_ro
[ "$allow_power" = 0 ]
sha256sum -c /usr/libexec/muos-session/prerequisites.sha256 >/dev/null
sha256sum -c - <<'PUBLIC_POWER_SUMS'
'''+sums+'''PUBLIC_POWER_SUMS
'''
if a.action == 'arm':
    with (stage/'arm-attempted').open('x') as f: f.write('explicit single test\n')
    out = remote('arm', guard+'''
[ "$(cat /run/muos/selection/mode)" = c07 ]
[ ! -e /run/muos/boot ] && [ ! -e /run/muos/session ]
[ ! -e /var/lib/muos-diagnostic/c12.once ] && [ ! -L /var/lib/muos-diagnostic/c12.once ]
[ ! -e /var/lib/muos-diagnostic/c12.power-tmp ] && [ ! -L /var/lib/muos-diagnostic/c12.power-tmp ]
/usr/libexec/muos-c07-network status
printf 'BASELINE_SEQUENCE=';cat /var/lib/muos-diagnostic/boot-seq
trap 'mount -o remount,ro /' EXIT
mount -o remount,rw /
umask 077
printf 'MUOS-C12-ONCE\n' > /var/lib/muos-diagnostic/c12.power-tmp
chmod 600 /var/lib/muos-diagnostic/c12.power-tmp
mv /var/lib/muos-diagnostic/c12.power-tmp /var/lib/muos-diagnostic/c12.once
sync
mount -o remount,ro /;c12_root_ro;trap - EXIT
[ "$(stat -c '%u:%g:%a:%h:%s' /var/lib/muos-diagnostic/c12.once)" = 0:0:600:1:14 ]
echo ONE_SHOT_ARMED_FOR_DURABLE_POWER_TEST_NO_REBOOT_YET
''')
    sequence = int(next(s.split('=')[1] for s in out.splitlines() if s.startswith('BASELINE_SEQUENCE=')))
    (stage/'baseline-sequence').write_text(str(sequence)+'\n')
elif a.action == 'boot':
    assert (stage/'baseline-sequence').exists()
    with (stage/'boot-request-attempted').open('x') as f: f.write('C07 to planned C12\n')
    remote('boot-request', guard+'''
[ "$(cat /run/muos/selection/mode)" = c07 ]
[ "$(cat /var/lib/muos-diagnostic/c12.once)" = MUOS-C12-ONCE ]
(trap '' HUP; sleep 2; exec /sbin/reboot) </dev/null >/run/c12-power-boot-request.log 2>&1 &
echo C07_TO_C12_REBOOT_SCHEDULED
''')
elif a.action == 'request':
    boot = json.loads((stage/'boot-analysis.json').read_text()); assert boot['passed']
    assert boot['boot_sequence'] == int((stage/'baseline-sequence').read_text())+1
    for n in meta['updated_public_files']:
        assert hashlib.sha256((repo/'port/device/rk-r35s-p0/boot'/n).read_bytes()).hexdigest() == meta['installed_files']['usr/libexec/muos-boot/'+n]['sha256']
    with (stage/'power-request-attempted').open('x') as f: f.write('explicit reboot; no physical poweroff\n')
    remote('power-request', guard+f'''
[ "$(cat /run/muos/selection/mode)" = c12 ]
[ "$(cat /run/muos/boot-diagnostic/sequence)" = {boot['boot_sequence']} ]
[ ! -e /run/muos/boot/power ] && [ ! -e /run/muos/boot/stopped ]
/usr/libexec/muos-boot/service.sh check-stop
umask 077
[ ! -e /run/c12-power.conf ] && [ ! -L /run/c12-power.conf ]
sed 's/^allow_power=0$/allow_power=1/' /etc/default/muos-boot > /run/c12-power.conf
chmod 600 /run/c12-power.conf
MUOS_BOOT_CONFIG=/run/c12-power.conf /usr/libexec/muos-boot/step.sh power.check
(trap '' HUP; sleep 2; exec env MUOS_BOOT_CONFIG=/run/c12-power.conf /usr/libexec/muos-boot/service.sh reboot) </dev/null >/run/c12-power-request.log 2>&1 &
echo C12_DURABLE_PREFLIGHT_THEN_REBOOT_SCHEDULED
''')
else:
    boot = json.loads((stage/'boot-analysis.json').read_text()); seq = boot['boot_sequence']
    out = remote('return-health', guard+f'''
[ "$(cat /run/muos/selection/mode)" = c07 ]
[ "$(cat /var/lib/muos-diagnostic/boot-seq)" = {seq+1} ]
[ ! -e /var/lib/muos-diagnostic/c12.once ]
[ ! -e /run/muos/session ] && [ ! -e /run/muos/boot ]
c12_session_quiescent || exit 1
/usr/libexec/muos-c07-network status
trap 'umount /boot' EXIT
mount -t vfat -o ro,nosuid,nodev,noexec "$boot_partition" /boot
[ "$(cat /boot/DIAG.ID)" = MUOS-R35S-EXT4-P4-B01 ]
for phase in START FINAL PBEGIN PREADY; do
echo REPORT_BEGIN=$phase
cat /boot/DIAG10/BOOT{seq:04d}/$phase.TXT
echo REPORT_END=$phase
done
[ ! -e /boot/DIAG10/BOOT{seq:04d}/PFAIL.TXT ]
umount /boot;trap - EXIT
c12_guard;c12_root_ro
echo RETURN_C07_ROOT_RO_FAT_UNMOUNTED_TAINT0
dmesg | awk '/Kernel panic|BUG:|Oops:|EXT4-fs error|I\\/O error|mmc.*timeout/ {{n++}} END{{printf "KERNEL_ERROR_SIGNATURES=%d\\n",n}}'
''')
    reports = {}
    for phase in ['START','FINAL','PBEGIN','PREADY']:
        value = out.split('REPORT_BEGIN='+phase+'\n')[1].split('REPORT_END='+phase+'\n')[0]
        reports[phase] = value; (stage/('durable-'+phase+'.txt')).write_text(value)
    d = stage/'native/run/muos/boot-diagnostic'
    for phase in ['START','FINAL']: assert reports[phase] == (d/(phase+'.txt')).read_text()
    ready = reports['PREADY']
    expected = ['session.stop LIMIT=110','session.quiescent LIMIT=5','network.stop LIMIT=20',
                'udev.stop LIMIT=20','root.sync LIMIT=10','root.seal LIMIT=10']
    assert [l for l in ready.splitlines() if l.startswith('STEP=')] == ['STEP='+v+' RC=0' for v in expected]
    assert f'BOOT_SEQ={seq} PHASE=PREADY ACTION=reboot' in ready
    assert 'OUTCOME=preflight-complete' in ready and 'PID1_REQUEST_NOT_YET_ATTEMPTED=1' in ready
    assert 'RETURN_C07_ROOT_RO_FAT_UNMOUNTED_TAINT0' in out and 'KERNEL_ERROR_SIGNATURES=0' in out
    result = {'passed':True, 'C12_sequence':seq, 'C07_return_sequence':seq+1,
              'durable_six_shutdown_steps_zero':True, 'START_FINAL_survived_identical':True,
              'PBEGIN_PREADY_survived_reboot_no_PFAIL':True, 'persistent_allow_power':False,
              'token_pending':False, 'hardware_reboot_tested':True, 'physical_poweroff_tested':False,
              'power_button_suspend_tested':False, 'offline_fsck_performed':False,
              'root_readonly_FAT_unmounted_taint0':True, 'all_installed_hashes_55_prerequisites_passed':True}
    (stage/'power-analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print('C12 durable power action completed:', a.action)
