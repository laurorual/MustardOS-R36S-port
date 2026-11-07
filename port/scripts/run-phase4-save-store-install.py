#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C57 exact four-file additive deployment with an absence backup and rollback."""
from pathlib import Path
import argparse,ipaddress,json,os,re,shutil,subprocess,tarfile,tempfile,time
from phase4_candidate import sha,sums
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'save-store-install';area.mkdir(exist_ok=True)
p=argparse.ArgumentParser(description=__doc__);p.add_argument('operation',choices=['prepare','apply','verify','rollback']);p.add_argument('--host',required=True,type=ipaddress.IPv4Address);p.add_argument('--stage',type=Path);a=p.parse_args()
ssh=['ssh','-p','2222','-i',str(work/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(work/'private/c07-known_hosts'),'-oBatchMode=yes','-oConnectTimeout=6','root@'+str(a.host)]
common='''set -eu
export PATH=/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
umask 077
c25_store=/var/lib/muos-diagnostic;c25_state=/run/muos/c25
. /usr/libexec/muos-c25/policy.sh
. /usr/libexec/muos-c25/card-guard.sh
. /usr/libexec/muos-c25/native.sh
c25_ready
[ ! -e "$c25_store/c25.once" ];[ ! -L "$c25_store/c25.once" ]
[ "$(cat /proc/asound/card0/pcm0p/sub0/status)" = closed ]
if pidof muxretro smoke-check >/dev/null; then exit 64; fi
'''
dirs=['usr/libexec/muos-save-store','usr/share/muos-save-store','usr/share/licenses/muos-save-store']
names=['usr/libexec/muos-save-store/muos-save-store','usr/libexec/muos-save-store/payload.sha256','usr/share/muos-save-store/contract.json','usr/share/licenses/muos-save-store/LICENSE']
stage=Path(tempfile.mkdtemp(prefix='install.',dir=area)) if a.operation=='prepare' else (a.stage.resolve() if a.stage else Path((area/'latest-plan').read_text().strip()))
assert stage.is_relative_to(area)
def remote(label,code,timeout=35):
 (stage/(label+'.sh')).write_text(code)
 r=subprocess.run(ssh+['sh -s'],input=code,text=True,capture_output=True,timeout=timeout)
 for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/(label+'.'+n)).write_text(v)
 assert r.returncode==0,(stage,label,r.stderr[-1800:],r.stdout[-1200:])
 return r.stdout
if a.operation=='prepare':
 proof=repo/'dist/phase4/save-store-image'
 for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h
 image=Path((work/'save-store-image/latest-image').read_text().strip())
 assert (image/'analysis.json').read_bytes()==(proof/'analysis.json').read_bytes()
 report=json.loads((image/'analysis.json').read_text());assert report['passed']
 parent_proof=repo/'dist/phase4/save-store-package'
 for n,h in sums(parent_proof/'SHA256SUMS').items():assert sha(parent_proof/n)==h
 assert report['C55_proof_sha256']==sha(parent_proof/'SHA256SUMS')
 approved=json.loads((parent_proof/'composition/analysis.json').read_text())['added']
 target=image/'target'
 for n,h in report['source_sha256'].items():assert sha(repo/n)==h
 expected=sums(target/'usr/libexec/muos-save-store/payload.sha256')
 for n,h in expected.items():assert sha(target/n.lstrip('/'))==h
 survey=common+'printf "BOOT %s\\n" "$(cat "$c25_store/boot-seq")"\n'
 for name in dirs:
  parent=str(Path(name).parent)
  for ancestor in list(Path(parent).parents)[:-1]+[Path(parent)]:
   if str(ancestor)=='.':continue
   survey+=f'[ -d /{ancestor} ];[ ! -L /{ancestor} ]\n[ "$(stat -c "%u:%g:%a" /{ancestor})" = 0:0:755 ]\n'
  survey+=f'[ ! -e /{name} ];[ ! -L /{name} ]\nprintf "ABSENT {name}\\n"\n'
 survey+='printf "FOUNDATION %s\\n" "$(sha256sum /usr/libexec/muos-session/prerequisites.sha256 | cut -d\' \' -f1)"\n'
 observed=remote('survey',survey).splitlines();assert len(observed)==5
 boot=int(observed[0].split()[1]);assert boot>=69
 assert observed[1:4]==['ABSENT '+n for n in dirs]
 assert observed[4]=='FOUNDATION '+sha(target/'usr/libexec/muos-session/prerequisites.sha256')
 payload=stage/'payload';(payload/'new').mkdir(parents=True)
 rows=[]
 for name in names:
  source=target/name;assert source.is_file() and not source.is_symlink()
  assert sha(source)==approved[name]['sha256']
  mode=0o755 if name==names[0] else 0o644;assert source.stat().st_mode&0o777==mode
  to=payload/'new'/name;to.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,to);to.chmod(mode)
  rows.append({'path':name,'before':'absent','mode':mode,'sha256':sha(source)})
 (payload/'FILES').write_text(''.join(r['sha256']+' '+f"{r['mode']:o}"+' '+r['path']+'\n' for r in rows))
 (payload/'boot-seq').write_text(str(boot)+'\n')
 shutil.copyfile(target/'usr/libexec/muos-session/prerequisites.sha256',payload/'foundation.sha256')
 native=repo/'port/device/rk-r35s-p0/save-store-install'
 for name in ['transaction.sh','native.sh']:shutil.copyfile(native/name,stage/name)
 plan={'experiment':'C57_SAVE_STORE_INSTALL','boot_sequence':boot,'files':rows,'absent_directories':dirs,
       'C56_proof_sha256':sha(proof/'SHA256SUMS'),'source_image_analysis_sha256':sha(image/'analysis.json'),
       'foundation_sha256':sha(payload/'foundation.sha256'),'device_written':False,'service_or_boot_hooks_changed':False,
       'source_sha256':{str(n.relative_to(repo)):sha(n) for n in [Path(__file__),*sorted(native.glob('*.sh'))]}}
 (stage/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
 # No existing files are overwritten: backup records exact prior absence.
 # Sync it independently on the host before a root remount is allowed.
 backup={'schema':1,'restore':'remove only four matching public files and three empty new directories',
         'existing_files_backed_up':0,'plan_sha256':sha(stage/'plan.json'),'absent_directories':dirs,'files':rows,
         'private_bytes_copied':False,'foundation_sha256':plan['foundation_sha256']}
 with (stage/'absence-backup.json').open('x') as f:
  json.dump(backup,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 fd=os.open(stage,os.O_DIRECTORY);os.fsync(fd);os.close(fd)
 files=[*sorted(payload.rglob('*')),stage/'transaction.sh',stage/'native.sh'];files=[f for f in files if f.is_file()]
 (stage/'SHA256SUMS').write_text(''.join(sha(f)+'  '+str(f.relative_to(stage))+'\n' for f in files))
 with tarfile.open(stage/'deployment.tar','w') as archive:
  for f in [*files,stage/'SHA256SUMS']:
   info=archive.gettarinfo(str(f),arcname=str(f.relative_to(stage)));info.uid=info.gid=0;info.uname=info.gname='root'
   with f.open('rb') as stream:archive.addfile(info,stream)
 (stage/'manifest.json').write_text(json.dumps({'plan_sha256':sha(stage/'plan.json'),'backup_sha256':sha(stage/'absence-backup.json'),'deployment_sha256':sha(stage/'deployment.tar')},indent=2)+'\n')
 (area/'latest-plan').write_text(str(stage)+'\n');print('C57 exact plan + synced absence backup; no device writes:',stage)
 raise SystemExit(0)
plan=json.loads((stage/'plan.json').read_text());meta=json.loads((stage/'manifest.json').read_text())
for name,key in [('plan.json','plan_sha256'),('absence-backup.json','backup_sha256'),('deployment.tar','deployment_sha256')]:assert sha(stage/name)==meta[key]
if a.operation!='rollback':
 for n,h in plan['source_sha256'].items():assert sha(repo/n)==h
comparison='-ge' if a.operation=='rollback' else '='
common+=f'[ "$(cat "$c25_store/boot-seq")" {comparison} {plan["boot_sequence"]} ]\n'
infra='''for name in udevd wpa_supplicant udhcpc dropbear; do
for pid in $(pidof "$name"); do
[ "$(awk '/^PPid:/ {print $2}' /proc/$pid/status)" = 1 ] || continue
printf '%s %s %s\\n' "$name" "$pid" "$(awk '{print $22}' /proc/$pid/stat)"
done;done
'''
if a.operation=='apply':
 checks=json.loads((stage/'checks/analysis.json').read_text());assert checks['passed'] and checks['plan_sha256']==sha(stage/'plan.json')
 for n,h in checks['source_sha256'].items():assert sha(repo/n)==h
 assert not (stage/'remote-directory').exists(),'Never redispatch; use verify to resume observation'
 # Keep recovery independent of the volatile device capsule.
 for name in ['plan.json','absence-backup.json','deployment.tar','manifest.json']:
  with (stage/name).open('rb') as f:os.fsync(f.fileno())
 fd=os.open(stage,os.O_DIRECTORY);os.fsync(fd);os.close(fd)
 before=remote('before',common+infra)
 directory=remote('allocate',common+'mktemp -d /run/muos-c57.XXXXXX\n').strip();assert re.fullmatch('/run/muos-c57[.][A-Za-z0-9]{6}',directory)
 (stage/'remote-directory').write_text(directory+'\n')
 r=subprocess.run(ssh+['cat > '+directory+'/deployment.tar'],input=(stage/'deployment.tar').read_bytes(),capture_output=True,timeout=30);assert r.returncode==0,r.stderr
 remote('unpack',f'''set -eu
printf '%s  %s\\n' {meta['deployment_sha256']} {directory}/deployment.tar | sha256sum -c -
tar -xf {directory}/deployment.tar -C {directory}
cd {directory}
sha256sum -c SHA256SUMS >/dev/null
''')
 remote('inspect',f'sh {directory}/native.sh {directory} inspect\n')
 remote('mounts-before',common+f'cat /proc/1/mountinfo > {directory}/mounts.before\n')
 remote('dispatch',f'nohup setsid sh {directory}/native.sh {directory} apply > {directory}/apply.log 2>&1 < /dev/null &\necho C57_DISPATCHED\n')
elif a.operation=='verify':
 directory=(stage/'remote-directory').read_text().strip();assert re.fullmatch('/run/muos-c57[.][A-Za-z0-9]{6}',directory)
if a.operation=='rollback':
 directory=remote('recovery-allocate',common+'mktemp -d /run/muos-c57.XXXXXX\n').strip();assert re.fullmatch('/run/muos-c57[.][A-Za-z0-9]{6}',directory)
 (stage/'recovery-directory').write_text(directory+'\n')
 r=subprocess.run(ssh+['cat > '+directory+'/deployment.tar'],input=(stage/'deployment.tar').read_bytes(),capture_output=True,timeout=30);assert r.returncode==0
 remote('recovery-unpack',f'''set -eu
printf '%s  %s\\n' {meta['deployment_sha256']} {directory}/deployment.tar | sha256sum -c -
tar -xf {directory}/deployment.tar -C {directory}
cd {directory}
sha256sum -c SHA256SUMS >/dev/null
''')
 remote('rollback',common+f'sh {directory}/native.sh {directory} rollback\n',timeout=60)
 absent=''.join(f'[ ! -e /{n} ];[ ! -L /{n} ]\n' for n in dirs)
 remote('rollback-health',common+absent+f'rm -rf {directory}\n')
 print('C57 explicit rollback restored absence/root RO:',stage);raise SystemExit(0)
for _ in range(60):
 r=subprocess.run(ssh+[f'test -f {directory}/apply.done'],capture_output=True,timeout=10)
 if r.returncode==0:break
 time.sleep(1)
else:raise AssertionError(('Do not redispatch; inspect pending C57',directory))
result=remote('result',f'cat {directory}/apply.result\ncat {directory}/apply.log\n');assert result.splitlines()[0]=='0',('Inspect rollback; do not repeat',stage)
health=common
for row in plan['files']:
 name=row['path'];health+=f'[ ! -L /{name} ];[ "$(stat -c "%u:%g:%a:%h" /{name})" = 0:0:{row["mode"]:o}:1 ]\n[ "$(sha256sum /{name} | cut -d\' \' -f1)" = {row["sha256"]} ]\n'
health+='sha256sum -c /usr/libexec/muos-save-store/payload.sha256 >/dev/null\n'
after=remote('after',health+infra);assert after==(stage/'before.stdout').read_text()
remote('mounts-after',common+f'cmp /proc/1/mountinfo {directory}/mounts.before\n')
synthetic=common+r'''exec 8>/run/muos/session/lifetime.lock
flock -n 8
probe=$(mktemp -d /run/muos-c57-probe.XXXXXX)
case "$probe" in /run/muos-c57-probe.??????) ;; *) exit 64 ;; esac
trap 'rm -rf "$probe"' EXIT
mkdir -m 700 "$probe/store"
printf 'MUOS-R35S-SAVES-V1\n' > "$probe/store/.muos-saves-v1"
chmod 600 "$probe/store/.muos-saves-v1"
identity=0000000000000000000000000000000000000000000000000000000000000000
binary=/usr/libexec/muos-save-store/muos-save-store
"$binary" init "$probe/store" "$identity"
"$binary" status "$probe/store" "$identity"
rc=0
"$binary" recover "$probe/store" "$identity" || rc=$?
[ "$rc" = 3 ]
printf 'C57_RAM_ONLY_INIT_STATUS_RECOVER_REFUSAL_OK\n'
'''
out=remote('synthetic',synthetic)
assert out.count('MUOS_SAVE_STORE_OK current=00000000 previous=00000000 next=00000001')==2
assert 'C57_RAM_ONLY_INIT_STATUS_RECOVER_REFUSAL_OK' in out
assert remote('final-health',health+infra)==(stage/'before.stdout').read_text()
remote('cleanup',common+f'cmp /proc/1/mountinfo {directory}/mounts.before\nrm -rf {directory}\n[ ! -e {directory} ]\necho C57_RAM_CAPSULE_REMOVED_ROOT_RO\n')
report={'passed':True,'experiment':'C57_INSTALLED_SAVE_STORE','boot_sequence':plan['boot_sequence'],'files_added':4,
        'existing_files_replaced':0,'root_read_only':True,'foundation_files':97,'infrastructure_unchanged':True,
        'reboot_requested':False,'token_or_service_enabled':False,'p3_mounted':False,'private_state_fingerprint_matched':True,
        'plan_sha256':sha(stage/'plan.json'),'native_synthetic_tested':True,'RAM_removed':True,'global_mounts_unchanged':True,
        'remote_capsule':directory}
(stage/'install-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
print('C57 installed and verified; root RO, no service/reboot/p3:',stage)
