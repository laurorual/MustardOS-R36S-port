#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Provision the pinned C79 factory from the independently verified C86 file."""
from pathlib import Path
import fcntl,importlib,json,os,stat,subprocess,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_candidate import sums
from phase4_root_migration import require,ROOT_BYTES
import phase4_recovery_image as image

prep=importlib.import_module('prepare-phase4-p2-qualify')
REPO=prep.REPO;WORK=prep.WORK;AREA=WORK/'initial-image'

def mapped(path):
    p=Path(path);require(p.resolve().is_relative_to(WORK),'Private build path')
    return '/work/'+str(p.relative_to(WORK))

def main():
    os.umask(0o077);AREA.mkdir(exist_ok=True)
    checks=prep.prep.latest(AREA,'latest-checks');tested=json.loads((checks/'analysis.json').read_text())
    require(tested['passed'] is True,'C88 tests required')
    for n,h in tested['source_sha256'].items():require(sha(REPO/n)==h,'Tested source changed')
    parents={}
    for n in ['gambatte-card-image','physical-capture','p2-controller','root-recovery','recovery-image']:
        root=REPO/'dist/phase4'/n
        for name,h in sums(root/'SHA256SUMS').items():require(sha(root/name)==h,'Parent proof changed')
        parents[n]=sha(root/'SHA256SUMS')
    ctx=prep.context_from_reference()
    reference=prep.prep.latest(WORK/'physical-capture','latest-complete-reference')/'root.ext4'
    require(sha(reference)==ctx['reference_root_sha256'],'Verified C86 source changed')
    factory_stage=prep.prep.latest(WORK/'gambatte-card-image','latest-image')
    factory_source=factory_stage/'partition-readback/rootfs.ext4'
    factory_proof=json.loads((REPO/'dist/phase4/gambatte-card-image/analysis.json').read_text())
    require(factory_proof['passed'] is True and factory_proof['factory_boot_counter']==0
        and factory_proof['regions']['rootfs.ext4']['bytes']==ROOT_BYTES,'Pinned C79 factory')
    factory_sha=factory_proof['regions']['rootfs.ext4']['sha256']
    stage=Path(tempfile.mkdtemp(prefix='provision.',dir=AREA));(AREA/'latest-attempt').write_text(str(stage)+'\n')
    source=os.open(factory_source,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        before=os.fstat(source)
        require(stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and before.st_nlink==1
            and before.st_size==ROOT_BYTES and stat.S_IMODE(before.st_mode)==0o644,'Qualified public factory leaf')
        fcntl.flock(source,fcntl.LOCK_EX|fcntl.LOCK_NB);require(image.fd_sha(source)==factory_sha,'Factory source hash')
        target=os.open(stage/'factory.ext4',os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        try:image.sparse_clone(source,target,ROOT_BYTES);require(image.fd_sha(target)==factory_sha,'Private factory copy differs')
        finally:os.close(target)
        require(image.signature(os.fstat(source))==image.signature(before) and image.fd_sha(source)==factory_sha,'Factory changed during copy')
    finally:os.close(source)
    request={'factory_image':mapped(stage/'factory.ext4'),'factory_sha256':factory_sha,'reference_image':mapped(reference),
        'reference_sha256':ctx['reference_root_sha256'],'private_files':ctx['backup_private_files'],'counter':ctx['backup_counter']}
    write_new(stage/'request.json',(json.dumps(request,indent=2)+'\n').encode());container=(WORK/'rootfs-container.iid').read_text().strip()
    cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
        '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=64m',
        '-v',str(WORK)+':/work:rw,z','-v',str(REPO/'port')+':/port:ro,z',container,'python3',
        '/port/scripts/phase4-initial-image.py','--request',mapped(stage/'request.json'),'--stage',mapped(stage)]
    p=subprocess.run(cmd,capture_output=True,timeout=600)
    for ext,data in [('stdout',p.stdout),('stderr',p.stderr),('exit',(str(p.returncode)+'\n').encode())]:write_new(stage/('consumer.'+ext),data)
    require(p.returncode==0,'C88 provisioning failed; inspect private stage '+str(stage))
    report=json.loads((stage/'analysis.json').read_text())
    require(report['passed'] is True and report['counter_preserved']==ctx['backup_counter']
        and report['candidate_provisioned'] is True and report['boot_handoff_authorized'] is False,'Candidate receipt')
    require(sha(stage/'candidate.ext4')==report['candidate_sha256'] and (stage/'candidate.ext4').stat().st_size==ROOT_BYTES,'Candidate readback')
    require(sha(reference)==ctx['reference_root_sha256'] and sha(factory_source)==factory_sha,'Original sources changed')
    result={'passed':True,'schema':88,'checks_sha256':sha(checks/'analysis.json'),'consumer_analysis_sha256':sha(stage/'analysis.json'),
        'request_sha256':sha(stage/'request.json'),'parent_proofs_sha256':parents,'candidate_sha256':report['candidate_sha256'],
        'source_sha256':{**tested['source_sha256'],str(Path(__file__).relative_to(REPO)):sha(Path(__file__))},
        'physical_device_contacted':False,'physical_card_writer_available':False,'boot_handoff_authorized':False}
    write_new(stage/'host-analysis.json',(json.dumps(result,indent=2)+'\n').encode());sync_dir(stage)
    (AREA/'latest-complete').write_text(str(stage)+'\n');print('C88 private C79 provisioned and sources preserved:',stage)

if __name__=='__main__':main()
