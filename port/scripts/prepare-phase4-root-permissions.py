#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C83 pinned packaging/metadata collection. No raw media IO on this host."""
from pathlib import Path
import argparse,base64,hashlib,importlib.util,json,os,re,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_candidate import sums
from phase4_root_migration import require
import phase4_root_metadata as metadata

REPO=Path(__file__).resolve().parents[2];WORK=REPO/'build/phase4';AREA=WORK/'root-permissions';BACKUPS=WORK/'offline-backup'
SOURCES=['phase4-root-permissions.py','phase4_root_metadata.py','phase4_backup_core.py','phase4_root_migration.py','phase4-offline-backup.py']

def transport():
    spec=importlib.util.spec_from_file_location('backup_transport',REPO/'port/scripts/run-phase4-offline-backup.py')
    t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t);return t

def context(host):
    proof=REPO/'dist/phase4/backup-native'
    for n,h in sums(proof/'SHA256SUMS').items():require(sha(proof/n)==h,'C82 proof changed')
    record=Path((BACKUPS/'latest-host-copy').read_text().strip());require(record.resolve().is_relative_to(BACKUPS),'Host-copy location')
    ack=json.loads((record/'analysis.json').read_text());download=Path(ack['download'])
    require(download.resolve().is_relative_to(BACKUPS),'Host backup location')
    receipt=json.loads((download/'backup.json').read_text())
    require(ack['passed'] is True and ack['independent_host_copy_verified'] is True and ack['metadata_repair_required_before_boot'] is True,'C82 independent backup required')
    require(sha(download/'backup.json')==ack['helper_receipt_sha256'] and receipt['prefix_sha256']==ack['prefix_sha256'],'C82 receipt')
    for name,row in receipt['artifacts'].items():require(sha(download/name)==row['sha256'],'Host backup changed')
    plan=Path((WORK/'root-migration/latest-plan').read_text().strip())/'migration-plan.json';p=json.loads(plan.read_text())
    t=transport();rule=t.native(host,"from pathlib import Path; import hashlib,json,subprocess; p=Path('/usr/lib/udev/rules.d/99-holo-automount.rules'); print(json.dumps({'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'runtime_override_exists':Path('/run/udev/rules.d/99-holo-automount.rules').exists(),'udevadm_verify_supported':'verify' in subprocess.run(['udevadm','--help'],capture_output=True,text=True).stdout}))")
    require(rule['runtime_override_exists'] is False and rule['udevadm_verify_supported'] is True,'Clean runtime rule / udev verifier required')
    return {'schema':83,'scope':'inode2_mode0777_to0755_only','host_copy_verified':True,'metadata_repair_required_before_boot':True,
        'host_ack_sha256':sha(record/'analysis.json'),'deck_backup':ack['remote_backup'],
        'backup_artifacts':receipt['artifacts'],'backup_receipt_sha256':sha(download/'backup.json'),
        'prefix_before_sha256':receipt['prefix_sha256'],'mbr_sha256':p['mbr_sha256'],
        'boot_prefix_16MiB_sha256':p['boot_prefix_16MiB_sha256'],'automount_rule_sha256':rule['sha256']}

def build(host,action):
    check=Path((AREA/'latest-checks').read_text().strip());c=json.loads((check/'analysis.json').read_text());require(c['passed'] is True,'C83 checks required')
    for name,h in c['source_sha256'].items():require(sha(REPO/name)==h,'C83 tested source changed')
    if action=='inspect':ctx=context(host);planned=None
    else:
        prior=Path((AREA/'latest-inspection').read_text().strip());require(prior.resolve().is_relative_to(AREA),'Inspection location')
        a=json.loads((prior/'host-copy.json').read_text());require(a['passed'] is True and a['host_capsule_copy_verified'] is True,'Independent metadata capsule required')
        for n,h in a['files'].items():require(sha(prior/n)==h,'Metadata capsule changed')
        ctx=json.loads((prior/'context.json').read_text());planned=json.loads((prior/'repair-plan.json').read_text())
        require(planned['context_sha256']==sha(prior/'context.json'),'Repair plan binding')
    stage=Path(tempfile.mkdtemp(prefix='package-'+action+'.',dir=AREA));bundle=stage/'bundle';bundle.mkdir(mode=0o700)
    for name in SOURCES:write_new(bundle/name,(REPO/'port/scripts'/name).read_bytes())
    write_new(bundle/'context.json',(json.dumps(ctx,indent=2)+'\n').encode())
    if planned is not None:write_new(bundle/'repair-plan.json',(json.dumps(planned,indent=2)+'\n').encode())
    manifest={'operation':action,'files':{p.name:sha(p) for p in bundle.iterdir()}}
    write_new(bundle/'package.json',(json.dumps(manifest,indent=2)+'\n').encode())
    target='/home/deck/muos-r35s-c83-'+action+'-'+sha(bundle/'package.json')[:12]
    t=transport();original="{'phase4-offline-backup.py','phase4_backup_core.py','phase4_root_migration.py','migration-plan.json','package.json'}"
    code=t.DEPLOY.replace("Path('/home/deck/muos-r35s-c81')","Path('"+target+"')").replace(original,repr(set(manifest['files'])|{'package.json'}))
    files={p.name:{'sha256':sha(p),'data':base64.b64encode(p.read_bytes()).decode()} for p in bundle.iterdir()}
    result=t.native(host,code,json.dumps({'files':files}).encode());require(result['passed'] is True,'Deployment verification')
    require(result['files']=={n:r['sha256'] for n,r in files.items()} and result['helper_started'] is False,'Deployment readback')
    write_new(stage/'analysis.json',(json.dumps({'passed':True,'operation':action,'target':target,'context_sha256':sha(bundle/'context.json'),
        'checks_sha256':sha(check/'analysis.json'),'source_sha256':c['source_sha256'],'deployment':result},indent=2)+'\n').encode())
    (AREA/('latest-package-'+action)).write_text(str(stage)+'\n')
    print('C83 package/deploy verified:',stage)
    print('Local command: sudo /usr/bin/python3 '+target+'/phase4-root-permissions.py '+action)

def expected_prefix(path,patch):
    h=hashlib.sha256();offset=patch['sector_offset'];replacement=bytes.fromhex(patch['after'])
    require(path.stat().st_size==640*1024*1024 and offset%512==0,'Protected prefix bounds')
    with path.open('rb') as stream:
        position=0
        while block:=stream.read(1024*1024):
            if position<=offset<position+len(block):
                start=offset-position;require(block[start:start+512].hex()==patch['before'],'Prefix sector differs from capsule')
                block=block[:start]+replacement+block[start+512:]
            h.update(block);position+=len(block)
    return h.hexdigest()

def collect(host,action,remote):
    require(re.fullmatch(r'/var/tmp/muos-r35s-c83-'+action+r'\.[a-z0-9_]{8}',remote),'Result path')
    code=r'''
from pathlib import Path
import base64,hashlib,json,os,re,stat,sys
r=json.load(sys.stdin);root=Path(r['path']);assert re.fullmatch(r'/var/tmp/muos-r35s-c83-(inspect|apply)\.[a-z0-9_]{8}',str(root))
s=root.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700
names={'analysis.json','p2-sb.bin','p2-gd.bin','p2-sector.bin','p3-sb.bin','p3-gd.bin','p3-sector.bin'}
assert {p.name for p in root.iterdir()}==names
files={}
for name in names:
 p=root/name;s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o400 and s.st_size<=65536
 data=p.read_bytes();files[name]={'data':base64.b64encode(data).decode(),'sha256':hashlib.sha256(data).hexdigest()}
print(json.dumps(files))
'''
    t=transport();files=t.native(host,code,json.dumps({'path':remote}).encode())
    stage=Path(tempfile.mkdtemp(prefix=action+'.',dir=AREA))
    for name,row in files.items():
        require(name in {'analysis.json',*[f'p{n}-{k}.bin' for n in (2,3) for k in ['sb','gd','sector']]},'Capsule filename')
        write_new(stage/name,base64.b64decode(row['data'],validate=True));require(sha(stage/name)==row['sha256'],'Capsule hash')
    package=Path((AREA/('latest-package-'+action)).read_text().strip());ctxfile=package/'bundle/context.json';ctx=json.loads(ctxfile.read_text())
    write_new(stage/'context.json',ctxfile.read_bytes());native=json.loads((stage/'analysis.json').read_text())
    require(native['passed'] is True and native['operation']==action and native['context_sha256']==sha(ctxfile),'Native result binding')
    require(native['backup_verified'] is True and native['host_copy_verified'] is True and native['userdata_before_matches_C82'] is True,'Native backup/userdata checks')
    for n in (2,3):
        start,size=(128*1024*1024,512*1024*1024) if n==2 else (640*1024*1024,248561664*512)
        patch=metadata.sector_patch((stage/f'p{n}-sb.bin').read_bytes(),(stage/f'p{n}-gd.bin').read_bytes(),(stage/f'p{n}-sector.bin').read_bytes(),start,size)
        require(patch==native['patches'][str(n)],'Independent capsule reconstruction')
    if action=='inspect':
        host=Path((BACKUPS/'latest-host-copy').read_text().strip());ack=json.loads((host/'analysis.json').read_text());prefix=Path(ack['download'])/'prefix.backup'
        require(sha(prefix)==ctx['prefix_before_sha256'],'Independent prefix hash')
        planned={'context_sha256':sha(ctxfile),'host_capsule_copy_verified':True,'patches':native['patches'],
                 'prefix_after_sha256':expected_prefix(prefix,native['patches']['2'])}
        write_new(stage/'repair-plan.json',(json.dumps(planned,indent=2)+'\n').encode())
    else:
        require(native['device_written'] is True and native['written_sectors']==2 and native['kernel_readonly'] is True,'Repair completion')
        require(native['userdata_after_matches_C82'] is True and native['full_prefix_posthash_verified'] is True and native['no_superblock_or_GDT_changes'] is True,'Post-repair preservation')
        require(native['p2_fsck_exit']==native['p3_fsck_exit']==0 and native['source_root_modes']=={'p2':0o755,'p3':0o755},'Post-repair modes/fsck')
    sync_dir(stage)
    write_new(stage/'host-copy.json',(json.dumps({'passed':True,'host_capsule_copy_verified':True,'remote_result':remote,
        'files':{p.name:sha(p) for p in stage.iterdir()}},indent=2)+'\n').encode())
    (AREA/('latest-inspection' if action=='inspect' else 'latest-complete')).write_text(str(stage)+'\n')
    print('C83 native '+action+' result and independent capsule verified:',stage)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['inspect','apply','collect-inspect','collect-apply'])
    p.add_argument('--host',required=True);p.add_argument('--result');a=p.parse_args();os.umask(0o077);AREA.mkdir(exist_ok=True)
    if a.action.startswith('collect-'):
        require(a.result is not None,'Result path required');collect(a.host,a.action[8:],a.result)
    else:build(a.host,a.action)

if __name__=='__main__':main()
