#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C94 collect verified initial migration and independent next handoff record."""
from pathlib import Path
import argparse,importlib,json,os,re,subprocess,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_root_migration import require
import phase4_root_recovery as recovery

prep=importlib.import_module('prepare-phase4-p2-initial')
legacy=importlib.import_module('collect-phase4-p2-recovery')
FETCH=legacy.FETCH.replace('muos-r35s-c89-recovery','muos-r35s-c94-initial')

def validate(report,ctx,manifest,journal,intent):
    require(report['passed'] is True and type(report['schema']) is int and report['schema']==94 and
        report['operation']=='migrate-initial-p2-only','Native initial migration operation')
    require(report['factory_sha256']==ctx['factory_sha256']==prep.helper.C79_FACTORY_SHA256 and
        report['pinned_C79_factory_verified'] is True and report['recovery_and_first_boot_qualification_checked'] is True and
        report['physical_boot_after_initial_migration_qualified'] is False,'Pinned factory/lineage and unqualified next boot')
    # Only reuse the pure extent/journal/fence validator. No shadow object is
    # passed to the C89 writer or to recovery eligibility.
    r=dict(report,schema=89,operation='recover-p2-only',recovery_sha256=report['candidate_sha256'],
        recovery_counter=report['migration_counter'])
    c=dict(ctx,recovery_sha256=ctx['candidate_sha256'],expected_recovery_counter=ctx['expected_migration_counter'])
    legacy.validate(r,c,manifest,journal,intent)

def main(host,result):
    os.umask(0o077);require(re.fullmatch(r'/var/tmp/muos-r35s-c94-initial\.[a-z0-9_]{8}',result),'Finite initial result path')
    package=prep.initial.latest(prep.AREA,'latest-package');p=json.loads((package/'analysis.json').read_text());bundle=package/'bundle'
    require(p['passed'] is True and sha(bundle/'package.json')==p['package_manifest_sha256'],'Pinned initial package')
    manifest=json.loads((bundle/'package.json').read_text());ctx=json.loads((bundle/'context.json').read_text())
    for name,h in manifest['files'].items():
        require(sha(bundle/name)==h,'Pinned package leaf changed')
        if name.endswith('.py'):require(sha(prep.REPO/'port/scripts'/name)==h,'Deployed initial source changed')
    prep.helper.validate_context(ctx,importlib.import_module('phase4-physical-capture'),
        importlib.import_module('phase4_root_migration'),recovery)
    prior=json.loads((bundle/'attempt.json').read_text())
    prep.helper.validate_lineage(ctx,bundle,prior,importlib.import_module('phase4_backup_core'),recovery)
    stage=Path(tempfile.mkdtemp(prefix='copy.',dir=prep.AREA));t=prep.initial.legacy.prep.prep.transport()
    attempt=ctx['next_attempt_id'];names=['analysis.json',*[f'write-journal/{n}.json' for n in ['unlock-intent','write-intent','complete']],
        *[f'capture/{n}.json' for n in ['capture-context','observation','private-files','tree']],f'handoff/{attempt}.json']
    for name in names:
        target=stage/name;target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        with target.open('xb') as out:
            r=subprocess.run(t.ssh(host)+[t.command(FETCH,result,name,attempt)],stdout=out,stderr=subprocess.PIPE,timeout=120)
            out.flush();os.fsync(out.fileno())
        require(r.returncode==0,'Initial result transfer failed; no handoff')
    fence=stage/'handoff'/f'{attempt}.json';fence.chmod(0o400)
    fd=os.open(fence,os.O_RDONLY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)
    report=json.loads((stage/'analysis.json').read_text());intent=recovery.load_attempt(stage/'handoff',attempt,report['next_attempt_sha256'])
    journal={n:json.loads((stage/'write-journal'/f'{n}.json').read_text()) for n in ['unlock-intent','write-intent','complete']}
    validate(report,ctx,manifest,journal,intent)
    captured=Path(p['C86_capture']);require(captured.resolve().is_relative_to(prep.WORK/'physical-capture'),'Known independent capture')
    for name in ['tree.json','private-files.json','capture-context.json','observation.json']:
        require(json.loads((stage/'capture'/name).read_text())==json.loads((captured/name).read_text()),'Fresh physical capture differs')
    survey=t.native(host,t.INSPECT);t.validate_inspection(survey)
    live=t.native(host,"from pathlib import Path; import hashlib,json,platform; s=Path('/sys/class/block'); print(json.dumps({'kernel':platform.release(),'guard':hashlib.sha256(Path('/run/udev/rules.d/99-holo-automount.rules').read_bytes()).hexdigest(),'ro':[int((s/n/'ro').read_text()) for n in ['mmcblk0','mmcblk0p1','mmcblk0p2','mmcblk0p3']]}))")
    require(live['kernel']==ctx['qualified_kernel'] and live['guard']==ctx['physical_capture']['automount_guard_sha256'] and
        live['ro']==[1,1,1,1],'Final protection/kernel changed; no handoff')
    ack={'passed':True,'schema':94,'physical_initial_p2_migration_verified':True,'new_fence_independent_host_copy_verified':True,
        'all_receipts_and_directory_fsynced':True,'next_attempt_id':attempt,'next_attempt_sha256':report['next_attempt_sha256'],
        'next_attempt_directory':str(stage/'handoff'),'native_receipt_sha256':sha(stage/'analysis.json'),
        'package_manifest_sha256':sha(bundle/'package.json'),'physical_boot_after_initial_migration_qualified':False,
        'all_card_aliases_RO_and_automount_guard_verified':True,'files':{n:sha(stage/n) for n in names}}
    for name,value in [('host-copy.json',ack),('inspection.json',survey),('protection.json',live)]:write_new(stage/name,recovery.encoded(value))
    for folder in stage.iterdir():
        if folder.is_dir():sync_dir(folder)
    sync_dir(stage);sync_dir(prep.AREA);(prep.AREA/'latest-complete').write_text(str(stage)+'\n');sync_dir(prep.AREA)
    print('C94 initial migration and independent next handoff record verified:',stage)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True);p.add_argument('--result',required=True)
    a=p.parse_args();main(a.host,a.result)
