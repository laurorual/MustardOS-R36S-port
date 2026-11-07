#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Pinned C82 Deck transport: inspect, deploy backup-only bundle, collect copies."""
from pathlib import Path
import argparse, base64, importlib.util, ipaddress, json, os, re, shlex, stat, subprocess, tempfile
from phase4_backup_core import sha, write_new, sync_dir
from phase4_root_migration import require, CAPACITY, DECK_CID

REPO=Path(__file__).resolve().parents[2];WORK=REPO/'build/phase4';AREA=WORK/'offline-backup'
REMOTE='/home/deck/muos-r35s-c81'

INSPECT=r'''
from pathlib import Path
import hashlib,json,platform,subprocess,shutil
sys=Path('/sys/class/block');cards=[]
for p in sorted(sys.glob('mmcblk*')):
 if not (p/'device/cid').is_file():continue
 cards.append({'name':p.name,'cid_sha256':hashlib.sha256((p/'device/cid').read_text().strip().lower().encode()).hexdigest(),'sectors':int((p/'size').read_text()),'sector_bytes':int((p/'queue/logical_block_size').read_text())})
mounts=subprocess.run(['findmnt','-rn','-o','SOURCE,TARGET,OPTIONS'],capture_output=True,text=True,check=True).stdout.splitlines()
print(json.dumps({'machine':platform.machine(),'DMI':Path('/sys/class/dmi/id/product_name').read_text().strip(),'cards':cards,
 'tools':{t:shutil.which(t) for t in ['python3','debugfs','e2fsck','fsck.fat','blkid','mount','umount','findmnt']},
 'sudo_noninteractive':subprocess.run(['sudo','-n','true'],capture_output=True).returncode==0,
 'var_tmp':subprocess.run(['findmnt','-rn','-T','/var/tmp','-o','FSTYPE,MAJ:MIN'],capture_output=True,text=True,check=True).stdout.strip(),
 'free_bytes':shutil.disk_usage('/var/tmp').free,'card_mounts':[v for v in mounts if v.startswith('/dev/mmcblk')],
 'prior_task_paths':[str(p) for p in Path('/home/deck').glob('muos-r35s-c*')],
 'run_task_paths':[str(p) for p in Path('/run').glob('muos-r35s-c*')]}))
'''

DEPLOY=r'''
from pathlib import Path
import base64,hashlib,json,os,stat,sys
os.umask(0o077);request=json.load(sys.stdin);target=Path('/home/deck/muos-r35s-c81')
files=request['files'];allowed={'phase4-offline-backup.py','phase4_backup_core.py','phase4_root_migration.py','migration-plan.json','package.json'}
assert set(files)==allowed
payload={n:base64.b64decode(v['data'],validate=True) for n,v in files.items()}
assert all(len(data)<=1024*1024 and hashlib.sha256(data).hexdigest()==files[n]['sha256'] for n,data in payload.items())
if target.exists() or target.is_symlink():
 s=target.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700
 assert {p.name for p in target.iterdir()}==allowed
else:
 target.mkdir(mode=0o700)
 for name,data in payload.items():
  fd=os.open(target/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
for name,data in payload.items():
 p=target/name;s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600
 assert p.read_bytes()==data
fd=os.open(target,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);os.fsync(fd);os.close(fd)
print(json.dumps({'passed':True,'target':str(target),'files':{n:files[n]['sha256'] for n in sorted(files)},'helper_started':False,'device_written':False}))
'''

FETCH=r'''
from pathlib import Path
import os,re,stat,sys
root=Path(sys.argv[1]);name=sys.argv[2]
assert re.fullmatch(r'/var/tmp/muos-r35s-c81-backup\.[a-z0-9_]{8}',str(root))
assert name in {'backup.json','prefix.backup','boot.fat','root.ext4','private-files.json','userdata.tar','userdata-manifest.json'} or re.fullmatch(r'private-[0-9]{2}\.dat',name)
s=root.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700
fd=os.open(root/name,os.O_RDONLY|os.O_NOFOLLOW)
with os.fdopen(fd,'rb') as f:
 before=os.fstat(f.fileno());assert stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_uid==os.getuid() and stat.S_IMODE(before.st_mode)==0o400
 limit={'prefix.backup':640*1024*1024,'boot.fat':100*1024*1024,'root.ext4':512*1024*1024,'userdata.tar':68*1024*1024}.get(name,1024*1024)
 assert 0<before.st_size<=limit
 while True:
  data=f.read(1024*1024)
  if not data:break
  sys.stdout.buffer.write(data)
 after=os.fstat(f.fileno());assert (before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
'''

def ssh(host):
    return ['ssh','-C','-p','22','-i',str(WORK/'private/deck-client'),'-oIdentitiesOnly=yes',
        '-oStrictHostKeyChecking=yes','-oHostKeyAlias=192.168.15.16',
        '-oUserKnownHostsFile='+str(WORK/'private/deck-known-hosts'),'-oBatchMode=yes',
        '-oConnectTimeout=8','-oServerAliveInterval=10','-oServerAliveCountMax=3','deck@'+str(ipaddress.IPv4Address(host))]

def command(code,*args):return '/usr/bin/python3 -c '+shlex.quote(code)+''.join(' '+shlex.quote(str(a)) for a in args)

def native(host,code,data=None):
    r=subprocess.run(ssh(host)+[command(code)],input=data,capture_output=True,timeout=30)
    require(r.returncode==0,'Deck operation failed; inspect private receipts')
    return json.loads(r.stdout)

def validate_inspection(r):
    require(r['machine']=='x86_64' and r['DMI'] in ('Jupiter','Galileo'),'Wrong offline host')
    require(r['cards']==[{'name':'mmcblk0','cid_sha256':DECK_CID,'sectors':CAPACITY,'sector_bytes':512}],'Wrong card or original present')
    require(all(r['tools'].values()) and r['free_bytes']>=3*1024**3,'Host dependencies/space')
    require(r['var_tmp'].split()[0] in ('ext4','btrfs') and not r['card_mounts'],'Persistent destination or card mounted')
    require(not r['run_task_paths'],'Prior root snapshot/helper needs inspection')

def current_package():
    package=Path((AREA/'latest-package').read_text().strip())
    require(package.resolve().is_relative_to(AREA),'Package location')
    r=json.loads((package/'analysis.json').read_text())
    require(r['passed'] is True and sha(package/'bundle/package.json')==r['bundle_manifest_sha256'],'Package receipt')
    for name,h in r['source_sha256'].items():require(sha(REPO/name)==h,'Frozen source changed')
    spec=importlib.util.spec_from_file_location('backup_prep',REPO/'port/scripts/prepare-phase4-offline-backup.py')
    prep=importlib.util.module_from_spec(spec);spec.loader.exec_module(prep);prep.verify_bundle(package/'bundle')
    return package

def collect(host,remote,plan):
    require(re.fullmatch(r'/var/tmp/muos-r35s-c81-backup\.[a-z0-9_]{8}',remote),'Backup path')
    require(plan.resolve().is_relative_to(WORK/'root-migration'),'Plan location')
    stage=Path(tempfile.mkdtemp(prefix='download.',dir=AREA));stage.chmod(0o700)
    def fetch(name):
        target=stage/name
        with target.open('xb') as output:
            target.chmod(0o600)
            r=subprocess.run(ssh(host)+[command(FETCH,remote,name)],stdout=output,stderr=subprocess.PIPE,timeout=600)
            output.flush();os.fsync(output.fileno())
        require(r.returncode==0,'Private artifact transfer failed')
    fetch('backup.json');receipt=json.loads((stage/'backup.json').read_text())
    require(receipt['passed'] is True and receipt['experiment']=='C81_OFFLINE_BACKUP_ONLY' and receipt['plan_sha256']==sha(plan),'Remote backup binding')
    allowed={'prefix.backup','boot.fat','root.ext4','private-files.json','userdata.tar','userdata-manifest.json'}
    require(allowed<=set(receipt['artifacts']) and len(receipt['artifacts'])<=13,'Artifact inventory')
    for name,row in receipt['artifacts'].items():
        require(name in allowed or re.fullmatch(r'private-[0-9]{2}\.dat',name),'Artifact name')
        fetch(name);require((stage/name).stat().st_size==row['bytes'] and sha(stage/name)==row['sha256'],'Artifact transfer differs')
    sync_dir(stage)
    spec=importlib.util.spec_from_file_location('backup_collect',REPO/'port/scripts/collect-phase4-offline-backup.py')
    checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
    package=current_package();manifest=json.loads((package/'bundle/package.json').read_text())
    ack=checker.verify_download(stage,plan,manifest.get('source_root_policy'))
    record=Path(tempfile.mkdtemp(prefix='native-copy.',dir=AREA))
    write_new(record/'analysis.json',(json.dumps({**ack,'download':str(stage),'remote_backup':remote,
        'transport_source_sha256':sha(Path(__file__))},indent=2)+'\n').encode())
    (AREA/'latest-host-copy').write_text(str(record)+'\n')
    return record

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['inspect','deploy','collect'])
    p.add_argument('--host',required=True,type=ipaddress.IPv4Address);p.add_argument('--backup');p.add_argument('--plan',type=Path);a=p.parse_args()
    os.umask(0o077);AREA.mkdir(exist_ok=True)
    if a.action=='collect':
        require(a.backup is not None and a.plan is not None,'Backup path and plan required')
        print('C82 independent private host copy verified:',collect(a.host,a.backup,a.plan));return
    r=native(a.host,INSPECT)
    stage=Path(tempfile.mkdtemp(prefix='deck-'+a.action+'.',dir=AREA))
    write_new(stage/'inspect.json',(json.dumps(r,indent=2)+'\n').encode())
    validate_inspection(r)
    if a.action=='deploy':
        package=current_package();bundle=package/'bundle'
        payload={'files':{f.name:{'sha256':sha(f),'data':base64.b64encode(f.read_bytes()).decode()} for f in bundle.iterdir()}}
        manifest=json.loads((bundle/'package.json').read_text())
        target=REMOTE if 'source_root_policy' not in manifest else '/home/deck/muos-r35s-c82-backup-'+sha(bundle/'package.json')[:12]
        result=native(a.host,DEPLOY.replace("Path('/home/deck/muos-r35s-c81')","Path('"+target+"')"),json.dumps(payload).encode())
        require(result['passed'] is True and result['files']=={f.name:sha(f) for f in bundle.iterdir()} and result['helper_started'] is False,'Deployment readback')
        write_new(stage/'deploy.json',(json.dumps(result,indent=2)+'\n').encode())
    (AREA/('latest-deck-'+a.action)).write_text(str(stage)+'\n')
    print(json.dumps(r,indent=2));print('C82 '+a.action+' verified:',stage)

if __name__=='__main__':main()
