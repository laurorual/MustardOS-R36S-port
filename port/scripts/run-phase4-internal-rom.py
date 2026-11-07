#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C113 inspect/backup once, then import or collect the same private ROM attempt."""
import argparse,hashlib,io,ipaddress,json,os,re,subprocess,tarfile,tempfile,time
from phase4_internal_rom import *
from phase4_backup_core import write_new,sync_dir
from phase4_gambatte_install import INFRA

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('operation',choices=['inspect','apply','collect'])
 p.add_argument('--host',required=True,type=ipaddress.IPv4Address);p.add_argument('--stage',type=Path);a=p.parse_args()
 os.umask(0o077);AREA.mkdir(mode=0o700,exist_ok=True)
 install,ir,meta,plan=installed();guard=common();checks=Path((AREA/'latest-checks').read_text().strip())
 tested=json.loads((checks/'analysis.json').read_text());require(tested['passed'] is True,'C113 checked implementation')
 for n,h in tested['source_sha256'].items():require(sha(REPO/n)==h,'Checked source changed')
 require(tested['sync_binary_sha256']==plan['files']['sync-path'],'Same qualified sync utility')
 stage=Path(tempfile.mkdtemp(prefix='import.',dir=AREA)) if a.operation=='inspect' else (
  a.stage.resolve() if a.stage else Path((AREA/'latest-plan').read_text().strip()))
 require(stage.resolve().is_relative_to(AREA),'Known private import attempt')
 ssh=['ssh','-p','2222','-i',str(WORK/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes',
 '-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(WORK/'private/c07-known_hosts'),'-oBatchMode=yes','-oConnectTimeout=6','root@'+str(a.host)]
 def write(n,data):write_new(stage/n,data.encode() if isinstance(data,str) else data)
 def remote(label,code,timeout=90,binary=False):
  if (stage/(label+'.sh')).exists():label+='.'+str(time.time_ns())
  write(label+'.sh',code);r=subprocess.run(ssh+['sh -s'],input=code.encode(),capture_output=True,timeout=timeout)
  for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:write(label+'.'+n,v)
  require(r.returncode==0,'C113 '+label+' failed; retain card/attempt: '+str(stage))
  return r.stdout if binary else r.stdout.decode()
 def transfer(n,data):
  r=subprocess.run(ssh+['cat > '+directory+'/'+n],input=data,capture_output=True,timeout=30)
  require(r.returncode==0,'Transfer failed; keep existing attempt')
 def cap_guard():
  text=guard+f'''[ -d {directory} ];[ ! -L {directory} ];[ "$(stat -c %u:%g:%a {directory})" = 0:0:700 ]
'''
  for n,h in job['files'].items():
   mode=700 if n=='sync-path' else 600
   text+=f'''[ -f {directory}/{n} ];[ ! -L {directory}/{n} ];[ "$(stat -c %u:%g:%a:%h {directory}/{n})" = 0:0:{mode}:1 ]
printf '%s  %s\\n' {h} {directory}/{n} | sha256sum -c - >/dev/null
'''
  return text
 def invoke(label,op):
  return remote(label,cap_guard()+f'/usr/libexec/muos-session/mount-namespace /bin/sh {directory}/native.sh {directory} {op}\n',timeout=120)
 if a.operation=='inspect':
  before=remote('before',guard+INFRA)
  directory=remote('allocate',guard+'mktemp -d /run/muos-prefs-data.XXXXXX\n').strip()
  require(re.fullmatch('/run/muos-prefs-data[.][A-Za-z0-9]{6}',directory),'Owned RAM import directory')
  _,prior=assets.qualified();require(not ROM.is_symlink() and ROM.stat().st_size==65536 and sha(ROM)==prior['ROM_sha256'],'Same legally supplied qualified private ROM')
  package=Path((assets.AREA/'latest-package').read_text().strip())
  inputs={n:(NATIVE/n).read_bytes() for n in ['native.sh','functions.sh']}
  inputs['private.gb']=ROM.read_bytes();inputs['ROM.sha256']=(sha(ROM)+'  gb/private.gb\n').encode()
  inputs['sync-path']=(package/'target'/assets.PREFIX/'sync-path').read_bytes()
  job={'schema':113,'host':str(a.host),'directory':directory,'boot_sequence':ir['boot_sequence'],'kernel_boot_id':meta['kernel_boot_id'],
   'files':{n:hashlib.sha256(v).hexdigest() for n,v in inputs.items()},'C112_analysis_sha256':sha(install/'analysis.json'),
   'checks_sha256':sha(checks/'analysis.json'),'source_sha256':tested['source_sha256'],'private_ROM_persist_requested':True}
  write('plan.json',json.dumps(job,indent=2)+'\n');sync_dir(stage)
  for n,data in inputs.items():transfer(n,data)
  code=guard+f'umask 077\nchmod 600 {directory}/*\nchmod 700 {directory}/sync-path\ncat /proc/1/mountinfo > {directory}/mounts.before\n'
  remote('payload-modes',code)
  require(remote('native-sync-ABI',cap_guard()+f'rc=0;{directory}/sync-path || rc=$?;[ "$rc" = 64 ];echo C113_SYNC_HELPER_AARCH64_CLI_REFUSED64\n')=='C113_SYNC_HELPER_AARCH64_CLI_REFUSED64\n','Native helper CLI compatible')
  require(invoke('inspect','inspect')=='C113_INSPECT_RO_BACKUP_COMPLETE\nC113_END operation=inspect status=0\n','Complete read-only inspection')
  native_hashes=remote('backup-hashes',cap_guard()+f'sha256sum {directory}/before.tar {directory}/before.tree\n').splitlines()
  require(len(native_hashes)==2,'Two independent backup hashes')
  for name,line in zip(['before.tar','before.tree'],native_hashes):
   digest,path=line.split();require(path==directory+'/'+name,'Exact backup file')
   data=remote('download-'+name,cap_guard()+f'cat {directory}/{name}\n',binary=True)
   require(hashlib.sha256(data).hexdigest()==digest,'Independent backup bytes matched')
   write(name,data)
   with (stage/name).open('rb') as f:os.fsync(f.fileno())
  with tarfile.open(stage/'before.tar') as tar:
   members=tar.getmembers();require(len(members)<=4096 and sum(m.size for m in members)<=64*1024*1024,'Bounded complete logical backup')
   files={}
   for m in members:
    name=m.name.removeprefix('./');require(not m.name.startswith('/') and '..' not in Path(m.name).parts and (m.isfile() or m.isdir()),'No backup aliases or special files')
    if m.isfile():files[name]=tar.extractfile(m).read()
   require(files['MUOS/preferences/preferences']==b'MUOS-PREFS-1\nVOLUME=55\nBRIGHTNESS=70\n','Existing preferences preserved')
   old=assets.qualified()[0];identity=prior['private_identity'];prefix='MUOS/port-saves-v1/gb/'+identity+'/'
   expected={n.removeprefix('./'):h for h,n in (ln.split() for ln in (old/'collected/store-readonly-after.sha256').read_text().splitlines())}
   require({n.removeprefix(prefix) for n in files if n.startswith(prefix)}==set(expected),'Same complete existing snapshot generation')
   for n,h in expected.items():require(hashlib.sha256(files[prefix+n]).hexdigest()==h,'Snapshot byte-identical to C109')
  verified={'passed':True,'archive_sha256':sha(stage/'before.tar'),'tree_sha256':sha(stage/'before.tree'),
   'members':len(members),'bytes':(stage/'before.tar').stat().st_size,'preferences_55_70_and_C109_snapshot_matched':True,
   'logical_backup_not_block_image':True}
  write('backup-verified.json',json.dumps(verified,indent=2)+'\n');sync_dir(stage)
  require(remote('inspect-after',guard+INFRA)==before,'Inspection infrastructure preserved')
  (AREA/'latest-plan').write_text(str(stage)+'\n');sync_dir(AREA)
  print('C113 independent private data backup verified; no card writes:',stage);return
 job=json.loads((stage/'plan.json').read_text());directory=job['directory']
 require(re.fullmatch('/run/muos-prefs-data[.][A-Za-z0-9]{6}',directory) and job['host']==str(a.host) and
  job['C112_analysis_sha256']==sha(install/'analysis.json') and job['checks_sha256']==sha(checks/'analysis.json') and
  job['kernel_boot_id']==meta['kernel_boot_id'],'Same inspected C112 import context')
 backup=json.loads((stage/'backup-verified.json').read_text())
 require(backup['passed'] is True and backup['archive_sha256']==sha(stage/'before.tar') and backup['tree_sha256']==sha(stage/'before.tree'),'Independent backup preserved')
 if a.operation=='apply':
  require(not (stage/'dispatch.claim').exists(),'Never redispatch; use collect for existing attempt')
  require(remote('apply-before',guard+INFRA)==(stage/'before.stdout').read_text(),'Before-write health unchanged')
  write('dispatch.claim','C113 exactly one private ROM import; never redispatch\n');sync_dir(stage)
  script=f'''#!/bin/sh
rc=0
/usr/libexec/muos-session/mount-namespace /bin/sh {directory}/native.sh {directory} apply || rc=$?
printf '%s\\n' "$rc" > {directory}/apply.exit
printf 'C113_DONE\\n' > {directory}/apply.done
exit "$rc"
'''
  transfer('dispatch.sh',script.encode())
  code=cap_guard()+f'''umask 077
printf 'C113_INDEPENDENT_BACKUP_VERIFIED\\n' > {directory}/host-backup-verified
chmod 600 {directory}/dispatch.sh
printf '%s  %s\\n' {hashlib.sha256(script.encode()).hexdigest()} {directory}/dispatch.sh | sha256sum -c - >/dev/null
nohup setsid /bin/sh {directory}/dispatch.sh > {directory}/apply.log 2>&1 < /dev/null &
echo C113_DISPATCHED
'''
  require(remote('dispatch',code)=='C113_DISPATCHED\n','Detached writer dispatched')
 for _ in range(120):
  r=subprocess.run(ssh+['test -f '+directory+'/apply.done'],capture_output=True,timeout=10)
  if r.returncode==0:break
  time.sleep(2)
 else:raise ValueError('C113 still pending: collect the existing attempt; never redispatch')
 result=remote('result',f'set -eu\ncat {directory}/apply.exit {directory}/apply.log\n')
 require(result=='0\nC113_ROM_INTERNAL_IMPORTED_RO_VERIFIED\nC113_END operation=apply status=0\n','Import failed; retain staging and inspect without retry')
 require(invoke('verify','verify')=='C113_ROM_INTERNAL_VERIFY_NO_WRITE\nC113_END operation=verify status=0\n','Fresh private read-only remount')
 for name in ['apply-before.tree','rw-before.tree','after-write.tree','after-remount.tree','verify.tree']:
  data=remote('collect-'+name,cap_guard()+f'cat {directory}/{name}\n',binary=True)
  require(data==(stage/'before.tree').read_bytes(),'Existing data tree changed: '+name);write(name,data)
 require(remote('after',guard+INFRA)==(stage/'before.stdout').read_text(),'Final infrastructure unchanged')
 remote('mount-health',cap_guard()+f'cmp /proc/1/mountinfo {directory}/mounts.before\necho C113_GLOBAL_MOUNTS_IDENTICAL\n')
 remote('cleanup',cap_guard()+f'''[ ! -e {directory}/data ];[ ! -L {directory}/data ]
cmp /proc/1/mountinfo {directory}/mounts.before
rm -rf {directory}
echo C113_RAM_REMOVED_DATA_UNMOUNTED_ROOT_RO
''')
 require(remote('post-cleanup-health',guard+INFRA)==(stage/'before.stdout').read_text(),'Post-cleanup health preserved')
 report={'passed':True,'schema':113,'boot_sequence':ir['boot_sequence'],'kernel_boot_id':meta['kernel_boot_id'],
  'ROM_sha256':job['files']['private.gb'],'ROM_bytes':ROM.stat().st_size,'private_ROM_internal':True,
  'data_path':'MUOS/port-roms-v1/gb/private.gb','existing_data_files_preserved':True,'C109_snapshot_byte_identical':True,
  'root_read_only':True,'data_unmounted':True,'RAM_removed':True,'global_mountinfo_and_infrastructure_preserved':True,
  'full_card_rewrite_format_repartition_reboot_or_game':False,'independent_backup_sha256':sha(stage/'before.tar'),
  'plan_sha256':sha(stage/'plan.json'),'C112_analysis_sha256':sha(install/'analysis.json'),
  'checks_sha256':sha(checks/'analysis.json'),'source_sha256':tested['source_sha256']}
 write('analysis.json',json.dumps(report,indent=2)+'\n');sync_dir(stage)
 (AREA/'latest-complete').write_text(str(stage)+'\n');sync_dir(AREA)
 print('C113 private ROM internal, existing data preserved and root RO:',stage)
if __name__=='__main__':main()
