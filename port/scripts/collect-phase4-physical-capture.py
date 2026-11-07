#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C86 collect/fsync private capture and independently scan it with C85."""
from pathlib import Path
import argparse,json,os,re,subprocess,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_root_migration import require,digest
import phase4_root_recovery as recovery
from importlib import import_module
prep=import_module('prepare-phase4-physical-capture')
REPO=prep.REPO;WORK=prep.WORK;AREA=prep.AREA

FETCH=r'''
from pathlib import Path
import os,re,stat,sys
root=Path(sys.argv[1]);name=sys.argv[2]
assert re.fullmatch(r'/var/tmp/muos-r35s-c86-capture\.[a-z0-9_]{8}',str(root))
assert name in {'analysis.json','root.ext4','tree.json','private-files.json','capture-context.json','observation.json'}
s=root.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700
fd=os.open(root/name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
with os.fdopen(fd,'rb') as f:
 before=os.fstat(f.fileno());assert stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and before.st_nlink==1 and stat.S_IMODE(before.st_mode)==0o400
 assert 0<before.st_size<=(512*1024*1024 if name=='root.ext4' else 32*1024*1024)
 while data:=f.read(1024*1024):sys.stdout.buffer.write(data)
 after=os.fstat(f.fileno());assert (before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
'''

def validate(receipt,manifest,context):
    mode=context['operation'];require(mode in ('reference','postboot') and receipt['passed'] is True and receipt['schema']==86 and receipt['operation']==mode,'Capture receipt operation')
    require(receipt['context_sha256']==recovery.hashed(recovery.encoded(context)),'Capture context binding')
    require(receipt['snapshot_source_sha256']=={n:h for n,h in manifest['files'].items() if n!='attempt.json'},'Root snapshot source binding')
    for k in ['all_namespaces_unmounted','alias_cache_synchronized','all_four_aliases_kernel_readonly',
        'source_p2_double_read_verified','MBR_and_16MiB_boot_prefix_preserved','root_snapshot_matches_physical_p2']:
        require(receipt[k] is True,'Physical capture verification incomplete')
    for k in ['device_payload_written','device_writer_available','seed_generated_or_loaded','reboot_requested','userdata_mounted_or_copied']:
        require(receipt[k] is False,'Unexpected writer/runtime capability')
    require(receipt['physical_postboot_capture'] is (mode=='postboot') and receipt['handoff_intent_checked'] is (mode=='postboot'),'Reference/postboot distinction')
    require(type(receipt['root_fsck_exit']) is int and receipt['root_fsck_exit']==0 and type(receipt['root_bytes']) is int and receipt['root_bytes']==512*1024*1024,'Root fsck/size')
    recovery.sequence(receipt['boot_sequence']);digest(receipt['root_sha256'])
    if mode=='reference':require(receipt['boot_sequence']==context['backup_counter'] and receipt['root_sha256']==context['reference_root_sha256'],'Reference state')
    expected={'root.ext4','tree.json','private-files.json'}|({'capture-context.json','observation.json'} if mode=='postboot' else set())
    require(set(receipt['artifacts'])==expected,'Capture artifact set')
    for n,row in receipt['artifacts'].items():
        require(set(row)=={'bytes','sha256'} and type(row['bytes']) is int,'Capture artifact schema')
        require(row['bytes']==512*1024*1024 if n=='root.ext4' else 0<row['bytes']<=32*1024*1024,'Capture artifact size')
        digest(row['sha256'])
    require(receipt['artifacts']['root.ext4']['sha256']==receipt['root_sha256'],'Root artifact binding')

def main(host,mode,remote):
    require(re.fullmatch(r'/var/tmp/muos-r35s-c86-capture\.[a-z0-9_]{8}',remote),'Capture result path')
    os.umask(0o077);package=prep.latest(AREA,'latest-package-'+mode);p=json.loads((package/'analysis.json').read_text())
    require(p['passed'] is True and p['mode']==mode and sha(package/'bundle/package.json')==p['package_manifest_sha256'],'Package binding')
    for n,h in p['source_sha256'].items():require(sha(REPO/n)==h,'Tested capture source changed')
    bundle=package/'bundle';manifest=json.loads((bundle/'package.json').read_text());context=json.loads((bundle/'context.json').read_text())
    for n,h in manifest['files'].items():require(sha(bundle/n)==h,'Package leaf changed')
    t=prep.transport()
    code=r'''
from pathlib import Path
import hashlib,json,os,re,stat,sys
r=json.load(sys.stdin);p=Path(r['path']);assert re.fullmatch(r'/var/tmp/muos-r35s-c86-capture\.[a-z0-9_]{8}',str(p))
s=p.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700
a=p/'analysis.json';s=a.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=1024*1024 and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o400
receipt=json.loads(a.read_text());assert {x.name for x in p.iterdir()}==set(receipt['artifacts'])|{'analysis.json'}
files={}
for leaf in p.iterdir():
 s=leaf.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o400
 with leaf.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 files[leaf.name]={'sha256':h,'bytes':s.st_size}
print(json.dumps({'receipt':receipt,'files':files}))
'''
    remote_data=t.native(host,code,json.dumps({'path':remote}).encode());receipt=remote_data['receipt']
    validate(receipt,manifest,context)
    require(set(remote_data['files'])==set(receipt['artifacts'])|{'analysis.json'},'Remote inventory')
    for n,row in receipt['artifacts'].items():require(remote_data['files'][n]==row,'Remote artifact changed')
    stage=Path(tempfile.mkdtemp(prefix='copy-'+mode+'.',dir=AREA))
    for n,row in remote_data['files'].items():
        require(n in {'analysis.json',*receipt['artifacts']},'Download leaf')
        path=stage/n;fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as out:
            r=subprocess.run(t.ssh(host)+[t.command(FETCH,remote,n)],stdout=out,stderr=subprocess.PIPE,timeout=300)
            require(r.returncode==0,'Capture transfer failed; retain partial copy');out.flush();os.fsync(out.fileno())
        require(path.stat().st_size==row['bytes'] and sha(path)==row['sha256'],'Independent artifact hash/size')
    require(json.loads((stage/'analysis.json').read_text())==receipt,'Downloaded receipt differs')
    independent=stage/'independent';independent.mkdir(mode=0o700)
    mapped=lambda path:'/work/'+str(path.relative_to(WORK))
    rows=json.loads((stage/'private-files.json').read_text());recovery.manifest(rows,receipt['boot_sequence'])
    require(receipt['private_file_count']==len(rows) and receipt['tree_entry_count']==len(json.loads((stage/'tree.json').read_text())),'Capture inventory counts')
    if mode=='reference':
        require(rows==context['backup_private_files'],'Reference private state')
        request={'operation':'reference','backup_image':mapped(stage/'root.ext4'),'backup_sha256':receipt['root_sha256'],
            'backup_private_files':rows,'backup_counter':receipt['boot_sequence'],'backup_root_mode':0o755}
    else:
        prior=prep.latest(WORK/'root-recovery','latest-readiness');binding=json.loads((prior/'binding.json').read_text())
        download=Path(binding['backup_download']);b=json.loads((download/'backup.json').read_text());journal=independent/'journal';journal.mkdir(mode=0o700)
        attempt=json.loads((bundle/'attempt.json').read_text());leaf=journal/(attempt['attempt_id']+'.json');write_new(leaf,recovery.encoded(attempt));leaf.chmod(0o400)
        request={'operation':'collect','backup_image':mapped(download/'root.ext4'),'backup_sha256':b['artifacts']['root.ext4']['sha256'],
            'backup_private_files':context['backup_private_files'],'backup_counter':context['backup_counter'],'backup_root_mode':0o777,
            'backup_prefix_sha256':context['backup_prefix_sha256'],'observed_image':mapped(stage/'root.ext4'),'observed_sha256':receipt['root_sha256'],
            'attempt_directory':mapped(journal),'attempt_id':attempt['attempt_id'],'attempt_sha256':context['attempt_sha256'],
            'capture_context':json.loads((stage/'capture-context.json').read_text())}
    write_new(independent/'request.json',(json.dumps(request,indent=2)+'\n').encode())
    container=(WORK/'rootfs-container.iid').read_text().strip()
    cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
        '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=64m',
        '-v',str(WORK)+':/work:rw,z','-v',str(REPO/'port')+':/port:ro,z',container,'python3','/port/scripts/phase4-recovery-image.py',
        '--request',mapped(independent/'request.json'),'--stage',mapped(independent)]
    r=subprocess.run(cmd,capture_output=True,timeout=600)
    write_new(independent/'consumer.stdout',r.stdout);write_new(independent/'consumer.stderr',r.stderr)
    require(r.returncode==0,'Independent C85 scan failed; inspect private copy')
    require(json.loads((independent/'analysis.json').read_text())['passed'] is True,'Independent scan incomplete')
    require(json.loads((stage/'tree.json').read_text())==json.loads((independent/'tree.json').read_text()),'Independent full-tree mismatch')
    if mode=='postboot':require(json.loads((stage/'observation.json').read_text())==json.loads((independent/'observation.json').read_text()),'Independent postboot observation mismatch')
    sync_dir(stage)
    result={'passed':True,'mode':mode,'remote_result':remote,'native_receipt_sha256':sha(stage/'analysis.json'),
        'independent_C85_scan_verified':True,'all_artifact_hashes_and_fsync_verified':True,'complete_tree_matches_native':True,
        'physical_reference_validated':mode=='reference','physical_postboot_validated':mode=='postboot',
        'snapshot_sha256':receipt['root_sha256'],'package_manifest_sha256':p['package_manifest_sha256']}
    write_new(stage/'host-copy.json',(json.dumps(result,indent=2)+'\n').encode())
    (AREA/('latest-complete-'+mode)).write_text(str(stage)+'\n');print('C86 independent copy and C85 scan verified:',stage)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['reference','postboot']);p.add_argument('--host',required=True);p.add_argument('--result',required=True)
    a=p.parse_args();main(a.host,a.mode,a.result)
