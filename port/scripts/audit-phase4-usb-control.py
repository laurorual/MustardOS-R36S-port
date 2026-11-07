#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""One-shot C16 fixed USB control observation and public evidence; restores all public originals."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
from usb_control_actions import observer_actions
import argparse,hashlib,ipaddress,json,shutil,subprocess,tarfile,tempfile
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'network-warm'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('action',choices=['install','baseline','boot','collect','cleanup'])
p.add_argument('--stage',type=Path);p.add_argument('--host',required=True,type=ipaddress.IPv4Address)
a=p.parse_args();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=repo/'port/device/rk-r35s-p0/network-warm-diagnostic'
targets=['usr/libexec/muos-c07-usb-mode','usr/libexec/muos-session/prerequisites.sha256','usr/libexec/muos-session/SHA256SUMS']
if a.action=='install':
    assert a.stage is None
    checked=Path((area/'latest-control-build').read_text().strip());checks=json.loads((checked/'manifest.json').read_text())
    assert checks['host_passed']
    for n,d in checks['sources'].items():assert sha(repo/n)==d,n
    assert sha(checked/'usb-control-probe')==checks['binary_sha256']
    wrapper_checked=Path((area/'latest-control-checks').read_text().strip())
    wrapper_checks=json.loads((wrapper_checked/'manifest.json').read_text());assert wrapper_checks['passed']
    for n,d in wrapper_checks['sources'].items():assert sha(repo/n)==d,n
    stage=Path(tempfile.mkdtemp(prefix='control.',dir=area));payload=stage/'payload'
    old=payload/'old';new=payload/'new';old.mkdir(parents=True);new.mkdir()
    baseline=work/'boot-order/power-test.feak98w7'
    before=json.loads((baseline/'manifest.json').read_text())['installed_files']
    initial=work/'boot-order/boot-test.mp19ei2w/payload/tree'
    approved=work/'linux-diagnostic/network-recovery.zz7sq2ve/extracted/usr/libexec/muos-c07-usb-mode'
    originals=[approved,initial/targets[1],initial/targets[2]]
    for n,src in zip(['usb-mode','prerequisites','session-sums'],originals):shutil.copyfile(src,old/n)
    (old/'usb-mode').chmod(0o755)
    prereq=(old/'prerequisites').read_text().splitlines()
    match=[line for line in prereq if line.endswith('  /'+targets[0])];assert len(match)==1
    assert sha(approved)==match[0].split('  ')[0]
    before={**before,targets[0]:{'sha256':sha(approved),'mode':'755'}}
    assert sha(old/'prerequisites')==before[targets[1]]['sha256']
    assert sha(old/'session-sums')==before[targets[2]]['sha256']
    helper=new/'usr/libexec/muos-c16';helper.mkdir(parents=True)
    shutil.copyfile(approved,helper/'usb-mode.original')
    shutil.copyfile(checked/'usb-control-probe',helper/'usb-control-probe')
    wrapper=new/targets[0];shutil.copyfile(source/'usb-control-trial.sh',wrapper)
    session=new/'usr/libexec/muos-session';session.mkdir()
    (session/'prerequisites.sha256').write_text('\n'.join(sha(wrapper)+'  /'+targets[0] if line in match else line for line in prereq)+'\n')
    sums=(old/'session-sums').read_text().splitlines();assert sum(l.endswith('  prerequisites.sha256') for l in sums)==1
    (session/'SHA256SUMS').write_text('\n'.join(sha(session/'prerequisites.sha256')+'  prerequisites.sha256' if l.endswith('  prerequisites.sha256') else l for l in sums)+'\n')
    after={**before}
    for f in new.rglob('*'):
        if f.is_file():
            name=str(f.relative_to(new));mode='644' if name in targets[1:] else '755';f.chmod(int(mode,8))
            after[name]={'sha256':sha(f),'mode':mode}
    def text_sums(files):return ''.join(v['sha256']+'  /'+n+'\n' for n,v in sorted(files.items()))
    (payload/'before.sha256').write_text(text_sums(before));(payload/'after.sha256').write_text(text_sums(after))
    (payload/'new.sha256').write_text(''.join(sha(f)+'  '+str(f.relative_to(new))+'\n' for f in sorted(new.rglob('*')) if f.is_file()))
    root=work/'linux-diagnostic/network-recovery.zz7sq2ve/extracted';rel=lambda p:'/work/'+str(p.relative_to(work))
    code='set -eu\n'+''.join(f'qemu-aarch64 -cpu cortex-a35 -L {rel(root)} {rel(root/"bin/busybox")} sh -n {rel(f)}\n' for f in [wrapper,helper/'usb-mode.original'])
    r=subprocess.run(['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','-v',f'{work}:/work:ro,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-c',code],text=True,capture_output=True,timeout=25)
    (stage/'shell.stdout').write_text(r.stdout);(stage/'shell.stderr').write_text(r.stderr);assert r.returncode==0,r.stderr
    with tarfile.open(stage/'deployment.tar','w') as archive:archive.add(payload,arcname='payload')
    meta={'experiment':'C16 one-shot fixed IN-only USB control observation','installed_before':before,'installed_after':after,
          'deployment_sha256':sha(stage/'deployment.tar'),'checks_stage':str(checked),'checks':checks,'wrapper_checks_stage':str(wrapper_checked),'wrapper_checks':wrapper_checks,
          'source_sha256':sha(Path(__file__)),'actions_sha256':sha(repo/'port/scripts/usb_control_actions.py'),'kernel_DTB_modules_libs_init_changed':False,
          'token':'MUOS-C16-ONCE','original_driver_binary_preserved':True,'native_qualified':False}
    (stage/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
    shutil.copyfile(Path(__file__),stage/Path(__file__).name)
    shutil.copyfile(repo/'port/scripts/usb_control_actions.py',stage/'usb_control_actions.py')
    (area/'latest-control').write_text(str(stage)+'\n')
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
def sums(files):return ''.join(v['sha256']+'  /'+n+'\n' for n,v in sorted(files.items()))
baseguard='''set -eu
boot_package=/usr/libexec/muos-boot
. "$boot_package/native-functions.sh"
c12_guard;c12_read_config;c12_root_ro
c12_session_quiescent || exit 1
[ "$(cat /run/muos/selection/mode)" = c07 ]
[ ! -e /var/lib/muos-diagnostic/c12.once ]
[ "$allow_power" = 0 ]
[ ! -e /etc/modprobe.d/muos-c13-warm-probe.conf ]
[ "$(cat /sys/module/8821cu/parameters/rtw_drv_log_level)" = 3 ]
/usr/libexec/muos-c07-network status
'''
def guard(which):
    return baseguard+"sha256sum -c /usr/libexec/muos-session/prerequisites.sha256 >/dev/null\nsha256sum -c - <<'C16_PUBLIC_SUMS' >/dev/null\n"+sums(meta[which])+"C16_PUBLIC_SUMS\n"
if a.action=='install':
    before=guard('installed_before')
    directory=remote('allocate',before+'[ ! -e /usr/libexec/muos-c16 ] && [ ! -L /usr/libexec/muos-c16 ]\n[ ! -e /var/lib/muos-diagnostic/c16.once ] && [ ! -L /var/lib/muos-diagnostic/c16.once ]\n[ ! -e /var/lib/muos-diagnostic/c16.used ] && [ ! -L /var/lib/muos-diagnostic/c16.used ]\nmktemp -d /run/muos-c16.XXXXXX\n').strip()
    import re
    assert re.fullmatch(r'/run/muos-c16\.[A-Za-z0-9]{6}',directory)
    (stage/'remote-directory').write_text(directory+'\n')
    r=subprocess.run(ssh+['cat > '+directory+'/deployment.tar'],input=(stage/'deployment.tar').read_bytes(),capture_output=True,timeout=25);assert r.returncode==0,r.stderr
    remote('unpack',f'set -eu\n[ "$(sha256sum {directory}/deployment.tar | cut -d" " -f1)" = {meta["deployment_sha256"]} ]\ntar -xf {directory}/deployment.tar -C {directory}\n')
    prepare=before+f'''
payload={directory}/payload
(cd "$payload/new";sha256sum -c ../new.sha256 >/dev/null)
for target in {' '.join('/'+n for n in targets)};do
 [ ! -L "$target" ] && [ ! -e "$target.c16tmp" ] && [ ! -L "$target.c16tmp" ]
done
[ ! -L /usr/libexec ] && [ ! -L /usr/libexec/muos-session ]
[ ! -e /var/lib/muos-diagnostic/c16.tmp ] && [ ! -L /var/lib/muos-diagnostic/c16.tmp ]
printf 'BASELINE_SEQUENCE=';cat /var/lib/muos-diagnostic/boot-seq
rw=0;committed=0
finish() {{
 trap - EXIT
 if [ "$rw" = 1 ];then
  if [ "$committed" = 0 ];then
   mount -o remount,rw /
   cp -p "$payload/old/usb-mode" /usr/libexec/muos-c07-usb-mode
   cp -p "$payload/old/prerequisites" /usr/libexec/muos-session/prerequisites.sha256
   cp -p "$payload/old/session-sums" /usr/libexec/muos-session/SHA256SUMS
   chmod 755 /usr/libexec/muos-c07-usb-mode
   chmod 644 /usr/libexec/muos-session/prerequisites.sha256 /usr/libexec/muos-session/SHA256SUMS
   chown 0:0 /usr/libexec/muos-c07-usb-mode /usr/libexec/muos-session/prerequisites.sha256 /usr/libexec/muos-session/SHA256SUMS
   rm -f /usr/libexec/muos-c07-usb-mode.c16tmp /usr/libexec/muos-session/prerequisites.sha256.c16tmp /usr/libexec/muos-session/SHA256SUMS.c16tmp
   rm -rf /usr/libexec/muos-c16
   rm -f /var/lib/muos-diagnostic/c16.once /var/lib/muos-diagnostic/c16.tmp
  fi
  sync;mount -o remount,ro /
 fi
}}
trap finish EXIT
mount -o remount,rw /;rw=1
mkdir -m 755 /usr/libexec/muos-c16
cp -p "$payload/new/usr/libexec/muos-c16/"* /usr/libexec/muos-c16/
'''
    for target in targets:
        prepare+=f'cp -p "$payload/new/{target}" /{target}.c16tmp\nchown 0:0 /{target}.c16tmp\nmv /{target}.c16tmp /{target}\n'
    prepare+=f'''
chown -R 0:0 /usr/libexec/muos-c16
sha256sum -c "$payload/after.sha256" >/dev/null
sha256sum -c /usr/libexec/muos-session/prerequisites.sha256 >/dev/null
umask 077
printf 'MUOS-C16-ONCE\\n' > /var/lib/muos-diagnostic/c16.tmp
chmod 600 /var/lib/muos-diagnostic/c16.tmp
mv /var/lib/muos-diagnostic/c16.tmp /var/lib/muos-diagnostic/c16.once
sync;mount -o remount,ro /;c12_root_ro
committed=1;rw=0;trap - EXIT
echo C16_TRIAL_INSTALLED_ROOT_RO_TOKEN_ARMED_NO_REBOOT
'''
    out=remote('install',prepare,timeout=60)
    seq=int(next(l.split('=')[1] for l in out.splitlines() if l.startswith('BASELINE_SEQUENCE=')))
    (stage/'baseline-sequence').write_text(str(seq)+'\n')
elif a.action=='boot':
    assert json.loads((stage/'baseline-analysis.json').read_text())['passed']
    with (stage/'reboot-attempted').open('x') as f:f.write('One C16 trial only\n')
    remote('boot-request',guard('installed_after')+'''
[ "$(cat /var/lib/muos-diagnostic/c16.once)" = MUOS-C16-ONCE ]
[ "$(stat -c '%u:%g:%a:%h:%s' /var/lib/muos-diagnostic/c16.once)" = 0:0:600:1:14 ]
(trap '' HUP;sleep 2;exec /sbin/reboot) </dev/null >/run/c16-reboot.log 2>&1 &
echo C16_ONE_SHOT_REBOOT_SCHEDULED
''')
elif a.action in ['baseline','collect']:
    observer_actions(a.action,stage,meta,guard,remote)

else:
    assert (stage/'analysis.json').exists() or (stage/'baseline-analysis.json').exists()
    directory=(stage/'remote-directory').read_text().strip()
    # RAM upload directory from the prior boot no longer exists. Upload only the
    # three verified public originals; no private or whole-rootfs backup.
    current=remote('allocate-cleanup',guard('installed_after')+'mktemp -d /run/muos-c16restore.XXXXXX\n').strip()
    import re
    assert re.fullmatch(r'/run/muos-c16restore\.[A-Za-z0-9]{6}',current)
    for n in ['usb-mode','prerequisites','session-sums']:
        r=subprocess.run(ssh+['cat > '+current+'/'+n],input=(stage/'payload/old'/n).read_bytes(),capture_output=True,timeout=20);assert r.returncode==0
    code=guard('installed_after')
    for n in ['usb-mode','prerequisites','session-sums']:
        code+=f'[ "$(sha256sum {current}/{n} | cut -d" " -f1)" = {sha(stage/"payload/old"/n)} ]\n'
    code+='trap \'mount -o remount,ro /\' EXIT\nmount -o remount,rw /\n'
    for n,t in zip(['usb-mode','prerequisites','session-sums'],targets):
        mode=meta['installed_before'][t]['mode']
        code+=f'cp {current}/{n} /{t}.c16tmp\nchmod {mode} /{t}.c16tmp\nchown 0:0 /{t}.c16tmp\nmv /{t}.c16tmp /{t}\n'
    code+='rm -rf /usr/libexec/muos-c16\nrm -f /var/lib/muos-diagnostic/c16.used /var/lib/muos-diagnostic/c16.once\nsync;mount -o remount,ro /;c12_root_ro;trap - EXIT\n'
    # Same shell already sourced the baseline guard; verify all originals now.
    code+="sha256sum -c - <<'C16_RESTORED_SUMS' >/dev/null\n"+sums(meta['installed_before'])+"C16_RESTORED_SUMS\nsha256sum -c /usr/libexec/muos-session/prerequisites.sha256 >/dev/null\n"
    code+='/usr/libexec/muos-c07-network status\necho C16_ORIGINALS_RESTORED_ROOT_RO_NO_TOKEN\n'
    remote('cleanup',code,timeout=45)
    (stage/'cleanup-analysis.json').write_text(json.dumps({'passed':True,'all_original_hashes_and_55_prerequisites_restored':True,
      'trial_scripts_tokens_removed':True,'root_readonly_FAT_unmounted_taint0':True,'network_ready':True},indent=2)+'\n')
print('C16 action completed:',a.action,stage)
