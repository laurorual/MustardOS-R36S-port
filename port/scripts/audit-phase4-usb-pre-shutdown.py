#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C17 RAM-only DWC2 retirement before PID1, using the frozen C16 observer."""
from pathlib import Path
import argparse,hashlib,ipaddress,json,shutil,subprocess,sys,tarfile,tempfile
sys.dont_write_bytecode=True
from usb_control_actions import observer_actions
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'network-warm'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('action',choices=['prepare','launch','collect','cleanup'])
p.add_argument('--stage',type=Path);p.add_argument('--observer-stage',type=Path)
p.add_argument('--host',required=True,type=ipaddress.IPv4Address);a=p.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if a.action=='prepare':
    assert a.stage is None and a.observer_stage is not None
    observer=a.observer_stage.resolve();assert observer.is_relative_to(area)
    assert json.loads((observer/'analysis.json').read_text())['collected']
    original=json.loads((observer/'manifest.json').read_text())
    checked=Path((area/'latest-pre-shutdown-checks').read_text().strip())
    checks=json.loads((checked/'manifest.json').read_text());assert checks['passed']
    for n,d in checks['sources'].items():assert sha(repo/n)==d,n
    stage=Path(tempfile.mkdtemp(prefix='pre-shutdown.',dir=area))
    package=stage/'package';package.mkdir()
    for n in ['pre-shutdown.sh','pre-shutdown-functions.sh']:
        shutil.copyfile(repo/'port/device/rk-r35s-p0/network-warm-diagnostic'/n,package/n)
    meta={**original,'experiment':'C17 DWC2 retirement BEFORE reboot','observer_stage':str(observer),
          'checks_stage':str(checked),'checks':checks,'source_sha256':sha(Path(__file__)),
          'actions_sha256':sha(repo/'port/scripts/usb_control_actions.py'),'native_trial_completed':False}
    (stage/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
    shutil.copyfile(Path(__file__),stage/Path(__file__).name)
    shutil.copyfile(repo/'port/scripts/usb_control_actions.py',stage/'usb_control_actions.py')
    (area/'latest-pre-shutdown').write_text(str(stage)+'\n')
else:
    assert a.stage is not None;stage=a.stage.resolve();assert stage.is_relative_to(area)
    meta=json.loads((stage/'manifest.json').read_text())
assert sha(Path(__file__))==meta['source_sha256']
assert sha(repo/'port/scripts/usb_control_actions.py')==meta['actions_sha256']
ssh=['ssh','-p','2222','-i',str(work/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes',
     '-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(work/'private/c07-known_hosts'),
     '-oBatchMode=yes','-oConnectTimeout=8','root@'+str(a.host)]
def remote(label,code,timeout=40):
    (stage/(label+'.sh')).write_text(code)
    r=subprocess.run(ssh+['sh -s'],input=code,text=True,capture_output=True,timeout=timeout)
    for suffix,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:
        (stage/(label+'.'+suffix)).write_text(value)
    assert r.returncode==0,(label,r.stdout,r.stderr)
    return r.stdout
sums=''.join(v['sha256']+'  /'+n+'\n' for n,v in sorted(meta['installed_after'].items()))
baseguard='''set -eu
boot_package=/usr/libexec/muos-boot
. "$boot_package/native-functions.sh"
c12_guard;c12_read_config;c12_root_ro
c12_session_quiescent || exit 1
[ "$(cat /run/muos/selection/mode)" = c07 ]
[ ! -e /var/lib/muos-diagnostic/c12.once ]
[ "$allow_power" = 0 ]
/usr/libexec/muos-c07-network status
sha256sum -c /usr/libexec/muos-session/prerequisites.sha256 >/dev/null
sha256sum -c - <<'C17_INSTALLED_PUBLIC_SUMS' >/dev/null
'''+sums+'''C17_INSTALLED_PUBLIC_SUMS
'''
def guard(_):return baseguard
if a.action=='prepare':
    seq=int(remote('sequence',baseguard+'cat /var/lib/muos-diagnostic/boot-seq\n').strip())
    (stage/'baseline-sequence').write_text(str(seq)+'\n')
    observer_actions('baseline',stage,meta,guard,remote)
    package=stage/'package'
    (package/'sequence').write_text(str(seq)+'\n');(package/'installed.sha256').write_text(sums)
    (package/'SHA256SUMS').write_text(''.join(sha(f)+'  '+f.name+'\n' for f in sorted(package.iterdir())))
    root=work/'linux-diagnostic/network-recovery.zz7sq2ve/extracted';rel=lambda f:'/work/'+str(f.relative_to(work))
    code='set -eu\n'+''.join(f'qemu-aarch64 -cpu cortex-a35 -L {rel(root)} {rel(root/"bin/busybox")} sh -n {rel(f)}\n' for f in package.glob('*.sh'))
    r=subprocess.run(['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','-v',f'{work}:/work:ro,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-c',code],text=True,capture_output=True,timeout=20)
    (stage/'shell.stdout').write_text(r.stdout);(stage/'shell.stderr').write_text(r.stderr);assert r.returncode==0,r.stderr
    with tarfile.open(stage/'deployment.tar','w') as archive:archive.add(package,arcname='package')
    directory=remote('allocate',baseguard+'mktemp -d /run/muos-c17.XXXXXX\n').strip()
    import re
    assert re.fullmatch(r'/run/muos-c17\.[A-Za-z0-9]{6}',directory)
    (stage/'remote-directory').write_text(directory+'\n')
    r=subprocess.run(ssh+['cat > '+directory+'/deployment.tar'],input=(stage/'deployment.tar').read_bytes(),capture_output=True,timeout=20);assert r.returncode==0
    remote('unpack',baseguard+f'[ "$(sha256sum {directory}/deployment.tar | cut -d" " -f1)" = {sha(stage/"deployment.tar")} ]\ntar -xf {directory}/deployment.tar -C {directory}\ncd {directory}/package;sha256sum -c SHA256SUMS >/dev/null\n')
elif a.action=='launch':
    assert json.loads((stage/'baseline-analysis.json').read_text())['passed']
    directory=(stage/'remote-directory').read_text().strip()
    seq=int((stage/'baseline-sequence').read_text())
    with (stage/'launch-attempted').open('x') as f:f.write('One preventive DWC2 retirement before reboot\n')
    remote('launch',baseguard+f'''
[ "$(cat /var/lib/muos-diagnostic/boot-seq)" = {seq} ]
cd {directory}/package;sha256sum -c SHA256SUMS >/dev/null
[ ! -e /var/lib/muos-diagnostic/c16.once ] && [ ! -L /var/lib/muos-diagnostic/c16.once ]
[ ! -e /var/lib/muos-diagnostic/c17.c16-used ] && [ ! -L /var/lib/muos-diagnostic/c17.c16-used ]
[ ! -L /var/lib/muos-diagnostic/c16.used ] && [ "$(stat -c '%u:%g:%a:%h:%s' /var/lib/muos-diagnostic/c16.used)" = 0:0:600:1:14 ]
[ "$(cat /var/lib/muos-diagnostic/c16.used)" = MUOS-C16-ONCE ]
trap 'mount -o remount,ro /' EXIT
mount -o remount,rw /
mv /var/lib/muos-diagnostic/c16.used /var/lib/muos-diagnostic/c17.c16-used
umask 077
printf 'MUOS-C16-ONCE\\n' > /var/lib/muos-diagnostic/c16.once
chmod 600 /var/lib/muos-diagnostic/c16.once
sync;mount -o remount,ro /;c12_root_ro;trap - EXIT
(trap '' HUP;sleep 2;exec sh {directory}/package/pre-shutdown.sh) </dev/null >{directory}/runner.log 2>&1 &
echo C17_ABORTABLE_PRE_SHUTDOWN_SCHEDULED
''')
elif a.action=='collect':
    observer_actions('collect',stage,meta,guard,remote)
    seq=int((stage/'baseline-sequence').read_text())
    out=remote('pre-shutdown-proof',baseguard+f'''
[ "$(cat /var/lib/muos-diagnostic/boot-seq)" = {seq+1} ]
trap 'umount /boot' EXIT
mount -t vfat -o ro,nosuid,nodev,noexec "$boot_partition" /boot
[ "$(cat /boot/DIAG.ID)" = MUOS-R35S-EXT4-P4-B01 ]
cat /boot/DIAG09/BOOT{seq:04d}/C17PRE.TXT
umount /boot;trap - EXIT
c12_guard;c12_root_ro
''')
    assert out.startswith('MUOS-C17-PRE-SHUTDOWN\n') and f'BOOT_SEQ={seq} NORMAL_REBOOT_INTENT=1' in out
    for step in ['baseline','network-stop','controller-unbind','controller-absent']:
        assert 'C17_STEP='+step+' RC=0\n' in out
    (stage/'pre-shutdown-public.txt').write_text(out)
    analysis=json.loads((stage/'analysis.json').read_text())
    report=(stage/'initial-report.txt').read_text();recovery=(stage/'recovery.txt').read_text()
    parsed=analysis['observations']['after']
    success='STATUS=0 ROOT_RO=1' in report and not recovery.strip() and parsed['complete'] and all(v['match']==1 and v['rc']==v['expected'] for v in parsed['reads'].values())
    analysis.update({'pre_shutdown_DWC2_retirement_executed':True,'durable_public_pre_PID1_proof':True,
                     'preventive_recovery_qualified':success,'observer_stage':meta['observer_stage']})
    (stage/'analysis.json').write_text(json.dumps(analysis,indent=2)+'\n')
    print('C17 preventive recovery qualified:',success)
else:
    assert json.loads((stage/'analysis.json').read_text())['collected']
    remote('retired-token-cleanup',baseguard+'''
[ ! -L /var/lib/muos-diagnostic/c17.c16-used ]
[ "$(stat -c '%u:%g:%a:%h:%s' /var/lib/muos-diagnostic/c17.c16-used)" = 0:0:600:1:14 ]
[ "$(cat /var/lib/muos-diagnostic/c17.c16-used)" = MUOS-C16-ONCE ]
trap 'mount -o remount,ro /' EXIT
mount -o remount,rw /
rm /var/lib/muos-diagnostic/c17.c16-used
sync;mount -o remount,ro /;c12_root_ro;trap - EXIT
''')
    command=['python3',str(repo/'port/scripts/audit-phase4-usb-control.py'),'cleanup','--stage',meta['observer_stage'],'--host',str(a.host)]
    r=subprocess.run(command,text=True,capture_output=True,timeout=90)
    (stage/'observer-cleanup.stdout').write_text(r.stdout);(stage/'observer-cleanup.stderr').write_text(r.stderr);assert r.returncode==0,r.stderr
    (stage/'cleanup-analysis.json').write_text(json.dumps({'passed':True,'all_C16_originals_restored':True,'C16_C17_tokens_and_helpers_removed':True,'root_readonly_FAT_unmounted_taint0':True},indent=2)+'\n')
print('C17 action completed:',a.action,stage)
