#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C76 selective additive core install with an independently synced absence backup."""
from pathlib import Path
import argparse, ipaddress, json, os, re, shutil, subprocess, tarfile, tempfile, time
from phase4_candidate import sha, sums
from phase4_gambatte_install import context, REPO, WORK, AREA, NATIVE, ROOTS, INFRA

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('operation',choices=['prepare','apply','verify','rollback'])
p.add_argument('--host',required=True,type=ipaddress.IPv4Address)
p.add_argument('--stage',type=Path)
a=p.parse_args()
source,package,added,names,dirs,preserved,parents,common=context()
AREA.mkdir(exist_ok=True)
stage=Path(tempfile.mkdtemp(prefix='install.',dir=AREA)) if a.operation=='prepare' else (
 a.stage.resolve() if a.stage else Path((AREA/'latest-plan').read_text().strip()))
assert stage.is_relative_to(AREA);stage.chmod(0o700)
ssh=['ssh','-p','2222','-i',str(WORK/'private/c07-client'),'-oIdentitiesOnly=yes',
 '-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222',
 '-oUserKnownHostsFile='+str(WORK/'private/c07-known_hosts'),'-oBatchMode=yes','-oConnectTimeout=6','root@'+str(a.host)]
def remote(label,code,timeout=60):
 (stage/(label+'.sh')).write_text(code)
 r=subprocess.run(ssh+['sh -s'],input=code,capture_output=True,text=True,timeout=timeout)
 for ext,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/(label+'.'+ext)).write_text(v)
 assert r.returncode==0,(stage,label,r.stderr[-1200:])
 return r.stdout
def absent():
 code=''
 for name in ROOTS:
  for parent in reversed(Path(name).parents):
   if str(parent)=='.':continue
   code+=f'[ ! -L /{parent} ];[ "$(stat -c \'%u:%g:%a\' /{parent})" = 0:0:755 ]\n'
  code+=f'[ ! -e /{name} ];[ ! -L /{name} ];[ ! -e /{name}.c76-new ];[ ! -L /{name}.c76-new ]\n'
 return code
if a.operation=='prepare':
 evidence=remote('survey',common+absent()+'''cat /var/lib/muos-diagnostic/boot-seq
cat /proc/sys/kernel/random/boot_id
''').splitlines()
 assert len(evidence)==2
 boot=int(evidence[0]);uuid=evidence[1]
 assert boot>=72 and re.fullmatch('[0-9a-f-]{36}',uuid)
 payload=stage/'payload';(payload/'new').mkdir(parents=True)
 rows=[]
 for name in names:
  src=source/'target'/name;dest=payload/'new'/name;dest.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(src,dest);dest.chmod(0o644)
  rows.append({'path':name,'before':'absent','mode':0o644,'sha256':sha(src)})
 (payload/'FILES').write_text(''.join(r['sha256']+' 644 '+r['path']+'\n' for r in rows))
 (payload/'boot-seq').write_text(str(boot)+'\n');(payload/'boot-uuid').write_text(uuid+'\n')
 (payload/'boot-seq').chmod(0o600);(payload/'boot-uuid').chmod(0o600)
 (payload/'foundation.sha256').write_text(''.join(h+'  '+n+'\n' for n,h in sorted(preserved.items())))
 for name in ['transaction.sh','native.sh']:shutil.copyfile(NATIVE/name,stage/name)
 # Compile the small MIT metadata-only probe from pinned source, rather than
 # rely on an unrecorded helper binary. It never calls retro_init or loads ROM.
 core_build=json.loads((source/'build-vars.txt').read_text().replace('MUOS_GAMBATTE_BUILDDIR=','"').strip()+'"')
 assert core_build.startswith('/work/gambatte-package/')
 code=f'''/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc -O2 -mcpu=cortex-a35 -I{core_build}/libgambatte/libretro-common/include /port/diagnostics/phase4-gb-identity-check.c -ldl -o /work/{stage.relative_to(WORK)}/identity-check
'''
 cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
 '--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{WORK}:/work:rw,z','-v',f'{REPO}/port:/port:ro,z',
 (WORK/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',code]
 result=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
 for ext,v in [('sh',code),('stdout',result.stdout),('stderr',result.stderr),('exit',str(result.returncode)+'\n')]: (stage/('probe-build.'+ext)).write_text(v)
 assert result.returncode==0,result.stderr
 (stage/'identity-check').chmod(0o700)
 plan={'experiment':'C76_GAMBATTE_INSTALL','boot_sequence':boot,'files':rows,'absent_directories':dirs,
 'roots_absent':ROOTS,'parent_proofs_sha256':parents,'preserved_prerequisites':132,
 'C75_analysis_sha256':sha(source/'analysis.json'),'core_sha256':package['core_sha256'],
 'byte_identical_qualified_core':True,'combined_license_review_pending':True,'activation':'manual metadata probe only',
 'boot_service_caller_ROM_save_or_existing_files_changed':False,'device_written':False,
 'source_sha256':{str(n.relative_to(REPO)):sha(n) for n in [Path(__file__),REPO/'port/scripts/phase4_gambatte_install.py',
 REPO/'port/scripts/prepare-phase4-gambatte-install.py',REPO/'port/diagnostics/phase4-gb-identity-check.c',*NATIVE.glob('*.sh')]}}
 (stage/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
 backup={'schema':1,'plan_sha256':sha(stage/'plan.json'),'existing_files_backed_up':0,
 'restore':'remove only nine reviewed matching public leaves and eight owned empty directories',
 'absent_roots':ROOTS,'absent_directories':dirs,'files':rows,'private_bytes_copied':False}
 (stage/'absence-backup.json').write_text(json.dumps(backup,indent=2)+'\n')
 files=[q for q in payload.rglob('*') if q.is_file()]+[stage/n for n in ['native.sh','transaction.sh','identity-check']]
 (stage/'SHA256SUMS').write_text(''.join(sha(q)+'  '+str(q.relative_to(stage))+'\n' for q in sorted(files)))
 with tarfile.open(stage/'deployment.tar','w') as tar:
  for q in files+[stage/'SHA256SUMS']:
   info=tar.gettarinfo(str(q),arcname=str(q.relative_to(stage)));info.uid=info.gid=0;info.uname=info.gname='root'
   with q.open('rb') as stream:tar.addfile(info,stream)
 (stage/'deployment.tar').chmod(0o600)
 metadata={'plan_sha256':sha(stage/'plan.json'),'backup_sha256':sha(stage/'absence-backup.json'),
 'deployment_sha256':sha(stage/'deployment.tar'),'probe_sha256':sha(stage/'identity-check'),
 'host':str(a.host),'kernel_boot_id':uuid}
 (stage/'manifest.json').write_text(json.dumps(metadata,indent=2)+'\n')
 for name in ['plan.json','absence-backup.json','deployment.tar','manifest.json']:
  with (stage/name).open('rb') as stream:os.fsync(stream.fileno())
 fd=os.open(stage,os.O_DIRECTORY);os.fsync(fd);os.close(fd)
 (AREA/'latest-plan').write_text(str(stage)+'\n')
 print('C76 exact absence plan/backup synced; no persistent device write:',stage)
 raise SystemExit(0)
plan=json.loads((stage/'plan.json').read_text());meta=json.loads((stage/'manifest.json').read_text())
assert meta['host']==str(a.host)
for name,key in [('plan.json','plan_sha256'),('absence-backup.json','backup_sha256'),('deployment.tar','deployment_sha256')]:assert sha(stage/name)==meta[key]
for n,h in plan['source_sha256'].items():assert sha(REPO/n)==h,n
common+=f'[ "$(cat "$c25_store/boot-seq")" = {plan["boot_sequence"]} ]\n'
common+=f'[ "$(cat /proc/sys/kernel/random/boot_id)" = {meta["kernel_boot_id"]} ]\n'
if a.operation=='apply':
 checks=json.loads((stage/'checks/analysis.json').read_text());assert checks['passed'] and checks['plan_sha256']==sha(stage/'plan.json')
 for n,h in checks['source_sha256'].items():assert sha(REPO/n)==h,n
 assert not (stage/'remote-directory').exists(),'Never redispatch; use verify with the same stage'
 remote('before',common+absent()+INFRA)
 directory=remote('allocate',common+'mktemp -d /run/muos-c76.XXXXXX\n').strip()
 assert re.fullmatch('/run/muos-c76[.][A-Za-z0-9]{6}',directory)
 (stage/'remote-directory').write_text(directory+'\n')
else:
 directory=(stage/'remote-directory').read_text().strip();assert re.fullmatch('/run/muos-c76[.][A-Za-z0-9]{6}',directory)
if a.operation=='apply':
 result=subprocess.run(ssh+['cat > '+directory+'/deployment.tar'],input=(stage/'deployment.tar').read_bytes(),capture_output=True,timeout=30)
 assert result.returncode==0
 remote('unpack',f'''set -eu
printf '%s  %s\\n' {meta['deployment_sha256']} {directory}/deployment.tar | sha256sum -c - >/dev/null
tar -xf {directory}/deployment.tar -C {directory}
cd {directory};sha256sum -c SHA256SUMS >/dev/null
''')
 remote('inspect',common+f'sh {directory}/native.sh {directory} inspect\n',timeout=90)
 remote('mounts-before',common+f'cat /proc/1/mountinfo > {directory}/mounts.before\n')
 remote('dispatch',common+f'nohup setsid sh {directory}/native.sh {directory} apply > {directory}/apply.log 2>&1 < /dev/null &\necho C76_DISPATCHED\n')
if a.operation=='rollback':
 remote('rollback',common+f'sh {directory}/native.sh {directory} rollback\n',timeout=90)
 remote('rollback-health',common+absent()+INFRA)
 print('C76 explicit recovery restored absence, root RO:',stage);raise SystemExit(0)
for _ in range(60):
 result=subprocess.run(ssh+[f'test -f {directory}/apply.done'],capture_output=True,timeout=10)
 if result.returncode==0:break
 time.sleep(1)
else:raise AssertionError('C76 pending: inspect existing capsule, never redispatch')
result=remote('result',f'cat {directory}/apply.result\ncat {directory}/apply.log\n')
assert result.splitlines()[0]=='0',('Inspect rollback; do not reapply',stage)
health=common
for row in plan['files']:
 n=row['path'];health+=f'[ ! -L /{n} ];[ "$(stat -c \'%u:%g:%a:%h\' /{n})" = 0:0:644:1 ]\n'
 health+=f"printf '%s  %s\\n' {row['sha256']} /{n} | sha256sum -c - >/dev/null\n"
for n in dirs:health+=f'[ ! -L /{n} ];[ "$(stat -c \'%u:%g:%a\' /{n})" = 0:0:755 ]\n'
health+='sha256sum -c /usr/share/muos-gambatte/payload.sha256 >/dev/null\n'
assert remote('after',health+INFRA)==(stage/'before.stdout').read_text()
remote('mounts-after',health+f'cmp /proc/1/mountinfo {directory}/mounts.before\n')
abi=health+f'''exec 8>/run/muos/session/lifetime.lock
flock -n 8
export LD_BIND_NOW=1 LD_LIBRARY_PATH=/opt/muos/frontend/lib:/usr/lib:/lib
{directory}/identity-check /opt/muos/share/core/gambatte_libretro.so
echo C76_INSTALLED_CORE_METADATA_ONLY_OK
'''
out=remote('native-ABI',abi)
assert out=='C48_GB_IDENTITY_OK API=1 memory_content=1 ROM_loaded=0\nC76_INSTALLED_CORE_METADATA_ONLY_OK\n'
assert remote('final-health',health+INFRA)==(stage/'before.stdout').read_text()
for name in ['apply.result','apply.log']:
 out=remote('collect-'+name,health+f'cat {directory}/{name}\n')
 (stage/('collected-'+name)).write_text(out)
remote('cleanup',health+f'''[ ! -L {directory} ];[ "$(stat -c '%u:%g:%a' {directory})" = 0:0:700 ]
cmp /proc/1/mountinfo {directory}/mounts.before
! findmnt -rn -M {directory} >/dev/null
rm -rf {directory}
[ ! -e {directory} ]
echo C76_RAM_REMOVED_ROOT_RO
''')
assert remote('post-cleanup-health',health+INFRA)==(stage/'before.stdout').read_text()
assert (WORK/'graphics-config/output/.config').read_bytes()==(WORK/'network-tools/baseline.config').read_bytes()
r={'passed':True,'experiment':'C76_INSTALLED_GAMBATTE','boot_sequence':plan['boot_sequence'],
 'core_sha256':plan['core_sha256'],'files_added':9,'directories_added':8,'existing_files_replaced':0,
 'preserved_prerequisites':132,'native_loader_API1_memory_content_metadata_passed':True,
 'core_initialized':False,'ROM_loaded':False,'GUI_replayed':False,'root_read_only':True,
 'private_state_fingerprint_matched':True,'infrastructure_and_global_mounts_preserved':True,
 'p3_mounted':False,'reboot_requested':False,'caller_or_service_enabled':False,'RAM_removed':True,
 'combined_license_review_pending':True,'plan_sha256':sha(stage/'plan.json'),
 'source_sha256':plan['source_sha256']}
(stage/'install-analysis.json').write_text(json.dumps(r,indent=2)+'\n')
print('C76 core installed: nine leaves/eight dirs, native metadata API1, root RO, RAM removed:',stage)
