#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C93 pinned host composition. No SSH, device, deployment, handoff or reboot.

Reject stale C86 captures before composing any seed/image. The current C89
fence and independently observed recovery boot determine the freshness floor.
"""
from pathlib import Path
import argparse,fcntl,importlib,json,os,stat,subprocess,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_candidate import sums
from phase4_root_migration import require,ROOT_BYTES,digest
import phase4_root_recovery as recovery
import phase4_recovery_image as image

legacy=importlib.import_module('prepare-phase4-p2-recovery')
collector=importlib.import_module('collect-phase4-p2-recovery')
REPO=legacy.REPO;WORK=legacy.WORK;AREA=WORK/'initial-migration'

def latest(area,pointer):
    p=Path((area/pointer).read_text().strip());require(p.resolve().is_relative_to(area),'Private record location');return p

def verified_file(path,wanted,size=None):
    """Verify existing host backup bytes, not just an older acknowledgment."""
    digest(wanted)
    require(size is None or (type(size) is int and 0<size<=640*1024*1024),'Bounded host backup size')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        s=os.fstat(fd)
        require(stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and
            stat.S_IMODE(s.st_mode) in (0o400,0o600) and
            (s.st_size==size if size is not None else 0<s.st_size<=1024*1024),'Private host backup leaf metadata')
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        require(image.fd_sha(fd)==wanted,'Host backup bytes changed or unavailable')
        raw=os.pread(fd,s.st_size+1,0) if size is None else None
        require(image.signature(os.fstat(fd))==image.signature(s),'Host backup changed during verification')
        if raw is not None:require(len(raw)==s.st_size and recovery.hashed(raw)==wanted,'Host backup metadata readback')
        return raw
    finally:os.close(fd)

def current_backup(old):
    reference=latest(WORK/'root-recovery','latest-readiness')
    report=json.loads((reference/'analysis.json').read_text())
    require(report['passed'] is True and sha(reference/'binding.json')==report['private_binding_sha256'],'C84 backup binding')
    binding=json.loads((reference/'binding.json').read_text())
    download=Path(binding['backup_download']);ack_path=Path(binding['backup_host_copy'])
    require(download.resolve().is_relative_to(WORK/'offline-backup') and
        ack_path.resolve().is_relative_to(WORK/'offline-backup'),'Known host backup paths')
    image.private_stage(download);image.private_stage(ack_path.parent)
    require(binding['backup_host_copy_sha256']==old['host_backup_ack_sha256'],'Current C82 acknowledgment binding')
    receipt=json.loads(verified_file(download/'backup.json',old['backup_receipt_sha256']))
    ack=json.loads(verified_file(ack_path,old['host_backup_ack_sha256']))
    require(ack['passed'] is True and ack['independent_host_copy_verified'] is True and
        ack['helper_receipt_sha256']==old['backup_receipt_sha256'] and
        ack['prefix_sha256']==old['physical_capture']['backup_prefix_sha256'],'Independent host backup receipt')
    require(receipt['passed'] is True and receipt['artifacts']==old['backup_artifacts'] and
        receipt['boot_sequence']==old['physical_capture']['backup_counter'] and
        receipt['prefix_sha256']==old['physical_capture']['backup_prefix_sha256'],'Known C82 artifact inventory')
    for name,row in receipt['artifacts'].items():
        require('/' not in name and name not in ('','.','..'),'Backup artifact leaf')
        verified_file(download/name,row['sha256'],row['bytes'])
    return download,ack_path

def freshness(held,context,attempt,native,known_boot):
    digest(held['next_attempt_sha256']);digest(context['attempt_sha256'])
    require(context['operation']=='postboot' and native['operation']=='postboot','Postboot capture required')
    require(held['next_attempt_id']==attempt['attempt_id'] and
        held['next_attempt_sha256']==context['attempt_sha256']==recovery.hashed(recovery.encoded(attempt)),
        'A new C86 capture bound to the current C89 fence is required; old captures cannot compose a migration')
    require(type(known_boot) is int and known_boot==attempt['counter_floor']+1,'Qualified first recovery boot binding')
    require(type(native['boot_sequence']) is int and known_boot<=native['boot_sequence']<=9998,
        'Capture counter is below the independently qualified recovery boot')
    require(native['context_sha256']==recovery.hashed(recovery.encoded(context)),'Capture context hash binding')

def held_recovery():
    stage=latest(WORK/'p2-recovery','latest-complete-recover');ack=json.loads((stage/'host-copy.json').read_text())
    for n in ['passed','physical_p2_recovery_verified','new_fence_independent_host_copy_verified',
        'all_receipts_and_directory_fsynced']:require(ack[n] is True,'Independent C89 recovery/fence required')
    for n,h in ack['files'].items():require(sha(stage/n)==h,'C89 evidence changed')
    package=latest(WORK/'p2-recovery','latest-package-recover');bundle=package/'bundle'
    require(sha(bundle/'package.json')==ack['package_manifest_sha256'],'C89 package binding')
    report=json.loads((stage/'analysis.json').read_text());ctx=json.loads((bundle/'context.json').read_text())
    manifest=json.loads((bundle/'package.json').read_text())
    for n,h in manifest['files'].items():require(sha(bundle/n)==h,'C89 package leaf changed')
    require(Path(ack['next_attempt_directory'])==stage/'handoff','Independent current fence directory')
    attempt=recovery.load_attempt(stage/'handoff',ack['next_attempt_id'],ack['next_attempt_sha256'])
    journal={n:json.loads((stage/'write-journal'/f'{n}.json').read_text()) for n in ['unlock-intent','write-intent','complete']}
    collector.validate(report,ctx,manifest,journal,attempt)
    boot=latest(WORK/'recovery-boot','latest-final-check');b=json.loads((boot/'analysis.json').read_text())
    public=json.loads((REPO/'dist/phase4/p2-recovery-boot/analysis.json').read_text())
    require(b['passed'] is True and b['physical_boot_after_recovery_qualified'] is True and
        b['recovery_host_copy_sha256']==sha(stage/'host-copy.json') and
        b['boot_sequence']==attempt['counter_floor']+1==public['boot_sequence'] and
        public['physical_boot_after_recovery_qualified'] is True,'Independent first recovery boot required')
    return stage,ack,attempt,b['boot_sequence'],ctx

def inputs():
    held,ack,attempt,known,old=held_recovery()
    # Check the cheap headers against the CURRENT fence before touching large
    # images, allocating a stage, or invoking the RNG/container.
    capture_package=latest(WORK/'physical-capture','latest-package-postboot')
    physical=json.loads((capture_package/'bundle/context.json').read_text())
    captured_attempt=json.loads((capture_package/'bundle/attempt.json').read_text())
    captured=latest(WORK/'physical-capture','latest-complete-postboot')
    native=json.loads((captured/'analysis.json').read_text())
    freshness(ack,physical,captured_attempt,native,known)
    require(captured_attempt==attempt,'Current handoff record changed')
    for name in ['backup_private_files','backup_counter','backup_prefix_sha256','automount_guard_sha256']:
        require(physical[name]==old['physical_capture'][name],'Known backup/guard binding changed')
    verified,copy,native,package,physical=legacy.require_postboot()
    require(verified==captured and package==capture_package,'Capture records changed during validation')
    capture_context=json.loads((captured/'capture-context.json').read_text())
    backup,backup_ack=current_backup(old)
    # Reuse only C88's PRIVATE FACTORY copy; never its stale candidate/seed.
    initial=latest(WORK/'initial-image','latest-complete');h=json.loads((initial/'host-analysis.json').read_text())
    require(h['passed'] is True and sha(initial/'request.json')==h['request_sha256'],'C88 factory request binding')
    request=json.loads((initial/'request.json').read_text());name=request['factory_image']
    require(name.startswith('/work/'),'Known C88 factory role')
    factory=WORK/name[len('/work/'):]
    require(factory.resolve()==(initial/'factory.ext4').resolve() and not factory.is_symlink(),'Only C88 factory source, never its candidate')
    proof=json.loads((REPO/'dist/phase4/gambatte-card-image/analysis.json').read_text())
    require(proof['passed'] is True and proof['factory_boot_counter']==0 and
        proof['regions']['rootfs.ext4']['bytes']==ROOT_BYTES,'Pinned C79 factory proof')
    factory_sha=proof['regions']['rootfs.ext4']['sha256']
    require(request['factory_sha256']==factory_sha,'Pinned C79 factory digest')
    with image.source_image(factory,factory_sha,ROOT_BYTES):pass
    return {'held':held,'held_ack':ack,'attempt':attempt,'known_boot':known,'capture':captured,
        'capture_package':capture_package,'native':native,'physical':physical,'capture_context':capture_context,
        'factory':factory,'factory_sha256':factory_sha,'backup_download':backup,'backup_host_ack':backup_ack}

def main(operation):
    os.umask(0o077);require(operation in ('check','compose'),'Finite host operation')
    parents={}
    for name in ['initial-migration','initial-image','gambatte-card-image','p2-recovery-native','p2-recovery-boot','physical-capture']:
        proof=REPO/'dist/phase4'/name
        for n,h in sums(proof/'SHA256SUMS').items():require(sha(proof/n)==h,'Frozen parent proof changed')
        parents[name]=sha(proof/'SHA256SUMS')
    checks=latest(AREA,'latest-preparer-checks');tested=json.loads((checks/'analysis.json').read_text())
    require(tested['passed'] is True,'C93 preparer checks required')
    for n,h in tested['source_sha256'].items():require(sha(REPO/n)==h,'Tested C93 source changed')
    # C92 production sources must still be exactly the ones exercised there.
    c92=latest(AREA,'latest-checks');prior=json.loads((c92/'analysis.json').read_text())
    require(prior['passed'] is True,'C92 composition checks required')
    for n,h in prior['source_sha256'].items():require(sha(REPO/n)==h,'Tested C92 source changed')
    value=inputs()
    if operation=='check':print('C93 fresh capture/fence/backup/boot/factory verified; no composition or device IO');return
    require(not (AREA/'latest-complete').exists(),'Migration composition already complete; do not regenerate seed')
    write_new(AREA/'compose.claim',recovery.encoded({'schema':93,'capture_receipt_sha256':sha(value['capture']/'analysis.json'),
        'current_fence_sha256':value['held_ack']['next_attempt_sha256'],'manual_review_required_before_replacement':True}))
    stage=Path(tempfile.mkdtemp(prefix='compose.',dir=AREA));(AREA/'latest-attempt').write_text(str(stage)+'\n')
    mapped=lambda p:'/work/'+str(p.relative_to(WORK))
    request={'factory_image':mapped(value['factory']),'factory_sha256':value['factory_sha256'],
        'observed_image':mapped(value['capture']/'root.ext4'),'observed_sha256':value['native']['root_sha256'],
        'backup_private_files':value['physical']['backup_private_files'],'backup_counter':value['physical']['backup_counter'],
        'backup_prefix_sha256':value['physical']['backup_prefix_sha256'],
        'attempt_directory':mapped(value['held']/'handoff'),'attempt_id':value['attempt']['attempt_id'],
        'attempt_sha256':value['held_ack']['next_attempt_sha256'],'capture_context':value['capture_context']}
    write_new(stage/'request.json',recovery.encoded(request));container=(WORK/'rootfs-container.iid').read_text().strip()
    cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
        '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=64m',
        '-v',str(WORK)+':/work:rw,z','-v',str(REPO/'port')+':/port:ro,z',container,'python3',
        '/port/scripts/phase4-initial-migration.py','--request',mapped(stage/'request.json'),'--stage',mapped(stage)]
    result=subprocess.run(cmd,capture_output=True,timeout=900)
    for n,data in [('stdout',result.stdout),('stderr',result.stderr),('exit',(str(result.returncode)+'\n').encode())]:write_new(stage/('consumer.'+n),data)
    require(result.returncode==0,'C93 composition failed; preserve claim/partial, no automatic retry')
    report=json.loads((stage/'analysis.json').read_text())
    require(report['passed'] is True and report['schema']==92 and report['root_bytes']==ROOT_BYTES and
        report['observed_counter']==value['native']['boot_sequence'] and
        report['migration_counter']==report['observed_counter']+1 and report['fresh_no_credit_seed_verified'] is True and
        report['seed_loaded_or_credited'] is False and report['physical_card_writer_available'] is False and
        report['boot_handoff_authorized'] is False and sha(stage/'candidate.ext4')==report['candidate_sha256'],
        'C92 migration image completion binding')
    require(sha(value['factory'])==value['factory_sha256'] and sha(value['capture']/'root.ext4')==request['observed_sha256'],
        'Factory/capture changed during composition')
    host={'passed':True,'schema':93,'consumer_analysis_sha256':sha(stage/'analysis.json'),'request_sha256':sha(stage/'request.json'),
        'capture':str(value['capture']),'capture_package':str(value['capture_package']),
        'held_recovery':str(value['held']),'held_recovery_ack_sha256':sha(value['held']/'host-copy.json'),
        'backup_download':str(value['backup_download']),'backup_host_ack':str(value['backup_host_ack']),
        'independent_host_backup_artifacts_reverified':True,
        'known_boot_floor':value['known_boot'],'source_sha256':{**prior['source_sha256'],**tested['source_sha256']},
        'preparer_checks_sha256':sha(checks/'analysis.json'),'parent_proofs_sha256':parents,
        'device_contacted_or_written':False,'boot_handoff_authorized':False}
    write_new(stage/'host-analysis.json',recovery.encoded(host));sync_dir(stage)
    (AREA/'latest-complete').write_text(str(stage)+'\n');sync_dir(AREA)
    print('C93 fresh initial migration regular image composed:',stage)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('operation',choices=['check','compose']);a=p.parse_args();main(a.operation)
