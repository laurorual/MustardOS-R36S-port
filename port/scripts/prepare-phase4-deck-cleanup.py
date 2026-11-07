#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C101 deploy a finite cleanup; collect receipt and remove only the task key."""
from pathlib import Path
import argparse,base64,importlib,json,os,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_root_migration import require

REPO=Path(__file__).resolve().parents[2];AREA=REPO/'build/phase4/deck-cleanup-current'
t=importlib.import_module('run-phase4-offline-backup')
cleanup=importlib.import_module('phase4-deck-cleanup')


def prepare(host):
    os.umask(0o077)
    retention=AREA/'host-retention.json';r=json.loads(retention.read_text());require(r['passed'] is True,'Independent host retention required')
    checks=Path((AREA/'latest-checks').read_text().strip());tested=json.loads((checks/'analysis.json').read_text())
    require(tested['passed'] is True,'Cleanup checks required')
    for n,h in tested['source_sha256'].items():require(sha(REPO/n)==h,'Tested cleanup source changed')
    inspected=json.loads((AREA/'inspection.json').read_text());rows=inspected['paths'];cleanup.validate_paths(rows,1000)
    require(inspected['cards']==[],'Reader must be empty')
    helper=REPO/'port/scripts/phase4-deck-cleanup.py';target='/home/deck/muos-r35s-c101-cleanup-'+sha(helper)[:12]
    plan={'schema':101,'paths':rows,'host_retention_verified':True,'host_retention_sha256':sha(retention),'helper_sha256':sha(helper)}
    stage=Path(tempfile.mkdtemp(prefix='package.',dir=AREA))
    write_new(stage/helper.name,helper.read_bytes());write_new(stage/'cleanup-plan.json',(json.dumps(plan,indent=2)+'\n').encode())
    request={'target':target,'expected_paths':[row['path'] for row in rows],
        'files':{p.name:{'data':base64.b64encode(p.read_bytes()).decode(),'sha256':sha(p)} for p in stage.iterdir()}}
    code=r'''
from pathlib import Path
import base64,hashlib,json,os,re,stat,sys
os.umask(0o077);r=json.load(sys.stdin);target=Path(r['target'])
assert re.fullmatch(r'/home/deck/muos-r35s-c101-cleanup-[0-9a-f]{12}',str(target))
assert not list(Path('/sys/class/block').glob('mmcblk*'))
paths={str(p) for base in ['/home/deck','/var/tmp','/tmp','/run'] for p in Path(base).glob('muos-r35s-*')}
assert paths==set(r['expected_paths']) and not target.exists() and not target.is_symlink()
assert set(r['files'])=={'phase4-deck-cleanup.py','cleanup-plan.json'}
payload={n:base64.b64decode(v['data'],validate=True) for n,v in r['files'].items()}
assert all(len(d)<1024*1024 and hashlib.sha256(d).hexdigest()==r['files'][n]['sha256'] for n,d in payload.items())
target.mkdir(mode=0o700)
for n,d in payload.items():
 fd=os.open(target/n,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(d);f.flush();os.fsync(f.fileno())
for n,d in payload.items():assert (target/n).read_bytes()==d
fd=os.open(target,os.O_RDONLY|os.O_DIRECTORY);os.fsync(fd);os.close(fd)
print(json.dumps({'passed':True,'target':str(target),'files':{n:hashlib.sha256(d).hexdigest() for n,d in payload.items()},'helper_started':False}))
'''
    result=t.native(host,code,json.dumps(request).encode());require(result['passed'] is True,'Verified cleanup deployment')
    for n,h in result['files'].items():require(sha(stage/n)==h,'Deployment readback')
    write_new(stage/'deployment.json',(json.dumps(result,indent=2)+'\n').encode());sync_dir(stage)
    (AREA/'latest-package').write_text(str(stage)+'\n');sync_dir(AREA)
    print('C101 package verified:',target)
    print('Local Konsole: sudo /usr/bin/python3 '+target+'/phase4-deck-cleanup.py')


def finish(host):
    os.umask(0o077);stage=Path((AREA/'latest-package').read_text().strip())
    require(stage.resolve().is_relative_to(AREA),'Known cleanup package')
    plan=json.loads((stage/'cleanup-plan.json').read_text());deployment=json.loads((stage/'deployment.json').read_text())
    require(sha(AREA/'host-retention.json')==plan['host_retention_sha256'],'Host retention record changed')
    fetch=r'''
from pathlib import Path
import json,os,stat
p=Path('/home/deck/.muos-r35s-c101-cleanup-result.json');s=p.lstat()
assert stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o400 and s.st_size<100000
print(p.read_text())
'''
    receipt=t.native(host,fetch)
    require(receipt['passed'] is True and receipt['schema']==101 and receipt['cleanup_plan_sha256']==sha(stage/'cleanup-plan.json') and
        receipt['host_retention_sha256']==plan['host_retention_sha256'],'Native cleanup receipt binding')
    require(set(receipt['paths_removed'])=={deployment['target'],*[row['path'] for row in plan['paths']]} and
        receipt['project_directories_removed']==len(plan['paths'])+1,'Exact cleanup scope')
    for n in ['reader_empty_verified','all_mount_namespaces_checked','project_loop_devices_absent','host_retention_verified']:
        require(receipt[n] is True,'Incomplete cleanup')
    write_new(stage/'native-receipt.json',(json.dumps(receipt,indent=2)+'\n').encode());sync_dir(stage)
    public=(REPO/'build/phase4/private/deck-client.pub').read_text().split()
    require(len(public)>=2 and public[0]=='ssh-ed25519','Exact task public key')
    code=r'''
from pathlib import Path
import hashlib,json,os,stat,sys
r=json.load(sys.stdin);p=Path('/home/deck/.muos-r35s-c101-cleanup-result.json')
receipt=json.loads(p.read_text());assert receipt['cleanup_plan_sha256']==r['plan_sha256']
assert not list(Path('/sys/class/block').glob('mmcblk*'))
assert not [str(p) for base in ['/home/deck','/var/tmp','/tmp','/run'] for p in Path(base).glob('muos-r35s-*')]
assert not Path('/run/udev/rules.d/99-holo-automount.rules').exists()
auth=Path('/home/deck/.ssh/authorized_keys');s=auth.lstat()
assert stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600
key=[x.encode() for x in r['key']];lines=auth.read_bytes().splitlines(keepends=True)
remaining=[line for line in lines if line.split()[:2]!=key];removed=len(lines)-len(remaining)
assert 1<=removed<=4
temp=auth.with_name('authorized_keys.muos-cleanup');fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
with os.fdopen(fd,'wb') as f:f.write(b''.join(remaining));f.flush();os.fsync(f.fileno())
os.replace(temp,auth)
assert auth.read_bytes()==b''.join(remaining)
fd=os.open(auth.parent,os.O_RDONLY|os.O_DIRECTORY);os.fsync(fd);os.close(fd)
p.unlink();fd=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY);os.fsync(fd);os.close(fd)
print(json.dumps({'passed':True,'project_paths_remaining':[],'cleanup_receipt_removed':not p.exists(),
 'task_key_lines_removed':removed,'other_authorized_key_lines_preserved':True,'sshd_service_changed':False,
 'card_opened_or_written':False}))
'''
    result=t.native(host,code,json.dumps({'key':public[:2],'plan_sha256':sha(stage/'cleanup-plan.json')}).encode())
    require(result['passed'] is True and result['cleanup_receipt_removed'] is True,'Final cleanup/key removal failed')
    write_new(stage/'final.json',(json.dumps(result,indent=2)+'\n').encode());sync_dir(stage)
    (AREA/'latest-complete').write_text(str(stage)+'\n');sync_dir(AREA)
    print('C101 Deck files, temporary rule, receipt and task key removed:',stage)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('operation',choices=['prepare','finish']);p.add_argument('--host',required=True)
    args=p.parse_args();globals()[args.operation](args.host)
