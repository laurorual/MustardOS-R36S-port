#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C89 collect the durable recovery journal and independent next-boot fence."""
from pathlib import Path
import argparse,importlib,json,os,re,subprocess,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_root_migration import require,ROOT_OFFSET,ROOT_BYTES,digest
import phase4_root_recovery as recovery

prep=importlib.import_module('prepare-phase4-p2-recovery')
FETCH=r'''
from pathlib import Path
import os,re,stat,sys
root=Path(sys.argv[1]);name=sys.argv[2];attempt=sys.argv[3]
assert re.fullmatch(r'/var/tmp/muos-r35s-c89-recovery\.[a-z0-9_]{8}',str(root)) and re.fullmatch('[0-9a-f]{32}',attempt)
s=root.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700
allowed={'analysis.json','write-journal/unlock-intent.json','write-journal/write-intent.json','write-journal/complete.json',
 'capture/capture-context.json','capture/observation.json','capture/private-files.json','capture/tree.json','handoff/'+attempt+'.json'}
assert name in allowed
for directory,leaves in [('write-journal',{'unlock-intent.json','write-intent.json','complete.json'}),('handoff',{attempt+'.json'})]:
 p=root/directory;s=p.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700
 assert {p.name for p in p.iterdir()}==leaves
for parent in (root/name).parents:
 if parent==root:break
 s=parent.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700
fd=os.open(root/name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
try:
 s=os.fstat(fd);limit=32*1024*1024 if name=='capture/tree.json' else 1024*1024
 assert stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o400 and 0<s.st_size<=limit
 remaining=s.st_size
 while remaining:
  data=os.read(fd,min(1024*1024,remaining));assert data;remaining-=len(data);sys.stdout.buffer.write(data)
 a=os.fstat(fd);assert (s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)
finally:os.close(fd)
'''

def validate(report,ctx,manifest,journal,intent):
    require(report['passed'] is True and report['schema']==89 and report['operation']=='recover-p2-only','Native recovery receipt')
    require(report['source_sha256']==manifest['files'],'Reviewed root payload binding')
    require(report['written_bytes']==ROOT_BYTES and type(report['written_bytes']) is int
        and report['recovery_sha256']==ctx['recovery_sha256'] and report['recovery_counter']==ctx['expected_recovery_counter'],'Recovery image/counter binding')
    for n in ['physical_card_p2_written','p1_MBR_p3_full_complement_preserved','all_four_aliases_kernel_readonly',
        'fresh_capture_and_three_image_scans_verified','new_no_credit_seed_verified_not_loaded','independent_host_copy_of_next_fence_required']:
        require(report[n] is True,'Incomplete recovery receipt')
    require(report['boot_handoff_authorized'] is False,'Native receipt must not authorize handoff')
    require(report['next_attempt_id']==ctx['next_attempt_id'] and report['prior_attempt_sha256']==ctx['physical_capture']['attempt_sha256'],'Prior/next fence binding')
    require(set(journal)=={'unlock-intent','write-intent','complete'},'Incomplete write journal')
    for n,kind in [('unlock-intent','P2_UNLOCK_MAY_HAVE_STARTED'),('write-intent','P2_WRITE_MAY_HAVE_STARTED'),('complete','P2_WRITE_VERIFIED')]:
        value=journal[n];require(value['kind']==kind and value['offset']==ROOT_OFFSET and value['bytes']==ROOT_BYTES,'P2 journal extent/kind')
    for name in ['unlock-intent','write-intent']:
        require(journal[name]['source_sha256']==ctx['recovery_sha256'] and journal[name]['previous_sha256']==ctx['expected_observed_sha256'],'Write journal source/current binding')
    hashes=journal['unlock-intent']['protected_sha256'];require(type(hashes) is list and len(hashes)==2,'Full protected complement hashes')
    for h in hashes:digest(h)
    done=journal['complete'];require(done['sha256']==ctx['recovery_sha256'] and done['boot_handoff_authorized'] is False
        and all(done[n] is True for n in ['all_four_aliases_kernel_readonly','alias_cache_synchronized','protected_complement_verified']),'Cold readback/protection journal')
    physical=ctx['physical_capture'];recovery.checked_attempt(intent,physical['backup_private_files'],physical['backup_counter'],physical['backup_prefix_sha256'])
    require(intent['attempt_id']==ctx['next_attempt_id'] and intent['candidate_root_sha256']==ctx['recovery_sha256']
        and intent['counter_floor']==ctx['expected_recovery_counter'] and recovery.hashed(recovery.encoded(intent))==report['next_attempt_sha256'],'New fence content/hash')

def main(host,result):
    os.umask(0o077);require(re.fullmatch(r'/var/tmp/muos-r35s-c89-recovery\.[a-z0-9_]{8}',result),'Recovery result path')
    package=prep.prep.prep.latest(prep.AREA,'latest-package-recover');p=json.loads((package/'analysis.json').read_text())
    require(p['passed'] is True and sha(package/'bundle/package.json')==p['package_manifest_sha256'],'Pinned recovery package')
    manifest=json.loads((package/'bundle/package.json').read_text());ctx=json.loads((package/'bundle/context.json').read_text())
    for n,h in manifest['files'].items():
        require(sha(package/'bundle'/n)==h,'Package changed')
        if n.endswith('.py'):require(sha(prep.REPO/'port/scripts'/n)==h,'Deployed source changed')
    stage=Path(tempfile.mkdtemp(prefix='copy-recover.',dir=prep.AREA));t=prep.prep.prep.transport()
    attempt=ctx['next_attempt_id'];names=['analysis.json',*[f'write-journal/{n}.json' for n in ['unlock-intent','write-intent','complete']],
        *[f'capture/{n}.json' for n in ['capture-context','observation','private-files','tree']],f'handoff/{attempt}.json']
    for name in names:
        target=stage/name;target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        with target.open('xb') as out:
            target.chmod(0o600);r=subprocess.run(t.ssh(host)+[t.command(FETCH,result,name,attempt)],stdout=out,stderr=subprocess.PIPE,timeout=120)
            out.flush();os.fsync(out.fileno())
        require(r.returncode==0,'Recovery receipt transfer failed; no handoff')
    (stage/'handoff'/f'{attempt}.json').chmod(0o400)
    fd=os.open(stage/'handoff'/f'{attempt}.json',os.O_RDONLY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)
    report=json.loads((stage/'analysis.json').read_text());intent=recovery.load_attempt(stage/'handoff',attempt,report['next_attempt_sha256'])
    journal={n:json.loads((stage/'write-journal'/f'{n}.json').read_text()) for n in ['unlock-intent','write-intent','complete']}
    validate(report,ctx,manifest,journal,intent)
    captured=Path(p['C86_capture']);require(captured.resolve().is_relative_to(prep.WORK/'physical-capture'),'Known independent capture')
    for name in ['tree.json','private-files.json','capture-context.json','observation.json']:
        require(json.loads((stage/'capture'/name).read_text())==json.loads((captured/name).read_text()),'Fresh recovery capture differs from independent source')
    survey=t.native(host,t.INSPECT);t.validate_inspection(survey)
    protection=t.native(host,"from pathlib import Path; import hashlib,json; s=Path('/sys/class/block'); p=Path('/run/udev/rules.d/99-holo-automount.rules'); print(json.dumps({'guard':hashlib.sha256(p.read_bytes()).hexdigest(),'ro':{n:int((s/n/'ro').read_text()) for n in ['mmcblk0','mmcblk0p1','mmcblk0p2','mmcblk0p3']}}))")
    require(protection['guard']==ctx['physical_capture']['automount_guard_sha256'] and set(protection['ro'].values())=={1},'Final card protection differs; no handoff')
    ack={'passed':True,'schema':89,'physical_p2_recovery_verified':True,'new_fence_independent_host_copy_verified':True,
        'all_receipts_and_directory_fsynced':True,'next_attempt_id':attempt,'next_attempt_sha256':report['next_attempt_sha256'],
        'next_attempt_directory':str(stage/'handoff'),'native_receipt_sha256':sha(stage/'analysis.json'),
        'package_manifest_sha256':sha(package/'bundle/package.json'),'physical_boot_after_recovery_qualified':False,
        'all_card_aliases_RO_and_automount_guard_verified':True,'files':{n:sha(stage/n) for n in names}}
    for n,v in [('host-copy.json',ack),('inspection.json',survey),('protection.json',protection)]:write_new(stage/n,recovery.encoded(v))
    for p in stage.iterdir():
        if p.is_dir():sync_dir(p)
    sync_dir(stage);sync_dir(prep.AREA);(prep.AREA/'latest-complete-recover').write_text(str(stage)+'\n')
    print('C89 recovery and independent next-boot fence verified:',stage)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True);p.add_argument('--result',required=True);a=p.parse_args();main(a.host,a.result)
