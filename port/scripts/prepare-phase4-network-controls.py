#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C09 RAM package: C08 lifecycle plus C06 hotkeys and control restoration."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,tarfile,tempfile
parser=argparse.ArgumentParser()
parser.add_argument('--window-seconds',type=int,choices=[60,120],default=120)
options=parser.parse_args()
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
subprocess.run(['python3',str(repo/'port/scripts/check-phase4-network-controls.py')],capture_output=True,text=True,check=True)
control_fixture=Path((work/'network-tools/latest-controls-hooks').read_text().strip())
control_checks=json.loads((control_fixture/'report.json').read_text());assert control_checks['passed'] and len(control_checks['cases'])==9
# Rebuild the unchanged C08 package to exercise its actual lifecycle fixtures.
r=subprocess.run(['python3',str(repo/'port/scripts/prepare-phase4-network-frontend.py')],capture_output=True,text=True,check=True)
base=Path((work/'linux-diagnostic/latest-network-frontend').read_text().strip());meta=json.loads((base/'manifest.json').read_text());assert meta['host_audit_passed']
stage=Path(tempfile.mkdtemp(prefix='network-controls.',dir=work/'linux-diagnostic'));pkg=stage/'package';shutil.copytree(base/'package',pkg)
root=Path((work/'linux-diagnostic/latest-network-recovery').read_text().strip())/'extracted'
script=(root/'usr/libexec/muos-c06-session').read_text()
def replace_one(s,old,new):
 assert s.count(old)==1,old
 return s.replace(old,new)
script=replace_one(script,'c06_before_core() {','c09_orig_before_core() {')
script=replace_one(script,'c06_frontend() {','c09_orig_frontend() {')
script=replace_one(script,"printf 'enabled=1\\nhotkeys=0\\n'", "printf 'enabled=1\\nhotkeys=1\\n'")
script=replace_one(script,'deadline=$((${now%%.*} + 90))','deadline=$((${now%%.*} + '+str(options.window_seconds)+'))')
# The reference groups remain unity; control checks allow the user's 0..100%.
start=script.index('c06_audio_check() {');end=script.index('c06_reference_group()',start)
part=script[start:end];part=replace_one(part,"grep -Eq '^Volume: 1\\.0+$'", "grep -Eq '^Volume: (0\\.[0-9]+|1\\.0+)$'");script=script[:start]+part+script[end:]
(pkg/'c06-session.sh').write_text(script)
shutil.copyfile(repo/'port/device/rk-r35s-p0/network-controls-diagnostic/extension.sh',pkg/'extension.sh')
run=(pkg/'run.sh').read_text();run=replace_one(run,'. /usr/libexec/muos-c06-session','. "$package/c06-session.sh"\n. "$package/extension.sh"')
run=replace_one(run,'c06_ui_stop >> "$state/cleanup.log" 2>&1 || c08_result=1','c06_ui_stop >> "$state/cleanup.log" 2>&1 || c08_result=1\n        c09_stop_monitor')
run=replace_one(run,'c06_audio_cleanup >> "$state/cleanup.log" 2>&1 || c08_result=1','c06_audio_cleanup >> "$state/cleanup.log" 2>&1 || c08_result=1\n        c09_restore >> "$state/cleanup.log" 2>&1 || c08_result=1')
run=run.replace('C08: FRONTEND / AUDIO / INPUT / SSH OK','C09: CONTROLS / FRONTEND / AUDIO / SSH OK').replace('MUOS-R35S-NETWORK-FRONTEND-P4-C08','MUOS-R35S-NETWORK-CONTROLS-P4-C09');(pkg/'run.sh').write_text(run)
# No power action/hotkey profile is introduced. Only the established four combos.
hotkeys=json.loads((root/'opt/muos/share/hotkey/r35s-bringup.json').read_text());assert set(hotkeys)=={'devices','VOL_DOWN','VOL_UP','BRIGHT_DOWN','BRIGHT_UP'}
assert hotkeys['VOL_DOWN']['negate']==['MENU'] and hotkeys['VOL_UP']['negate']==['MENU']
for name in ['run.sh','c06-session.sh','extension.sh']:
 args=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','-v',f'{work}:/work:ro,z',(work/'rootfs-container.iid').read_text().strip(),'qemu-aarch64','-cpu','cortex-a35','-L','/work/'+str(root.relative_to(work)),'/work/'+str((root/'bin/busybox').relative_to(work)),'sh','-n','/work/'+str((pkg/name).relative_to(work))]
 r=subprocess.run(args,capture_output=True,text=True,timeout=20);(stage/(name+'.shell.stderr')).write_text(r.stderr);assert r.returncode==0,r.stderr
(pkg/'SHA256SUMS').unlink();(pkg/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(pkg.iterdir()) if p.is_file()))
with tarfile.open(stage/'deployment.tar','w') as t:
 for p in pkg.iterdir():t.add(p,arcname=p.name)
record={'experiment':'MUOS-R35S-NETWORK-CONTROLS-P4-C09','host_passed':True,'control_cases':control_checks,'control_fixture_report_sha256':sha(control_fixture/'report.json'),'base_c08_manifest_sha256':sha(base/'manifest.json'),'chain_cases':meta['chain_cases'],'udev_identity_cases':meta['udev_identity_cases'],'base_c06_session_sha256':sha(root/'usr/libexec/muos-c06-session'),'scope':'RAM namespace only; native helpers/muhotkey,120s UI, hardware brightness restore and persistent/cache checks','kernel_modules_boot_root_code_changed':False,'native_tested':False,'deployment_sha256':sha(stage/'deployment.tar'),'sources':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/scripts/check-phase4-network-controls.py',repo/'port/device/rk-r35s-p0/network-controls-diagnostic/extension.sh',repo/'port/device/rk-r35s-p0/network-frontend-diagnostic/run.sh']}}
record['ui_window_seconds']=options.window_seconds
(stage/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');(work/'linux-diagnostic/latest-network-controls').write_text(str(stage)+'\n');print('C09 native-helper controls RAM package passed:',stage)
