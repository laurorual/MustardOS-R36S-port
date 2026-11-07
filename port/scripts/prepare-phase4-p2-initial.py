#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C94 prepare/stage finite initial package only after fresh C93 composition.

Never starts sudo, writes media, or manufactures a capture/handoff record.
"""
from pathlib import Path
import argparse,base64,importlib,json,os,subprocess,tempfile,uuid
from phase4_backup_core import sha,write_new,sync_dir
from phase4_candidate import sums
from phase4_root_migration import require,ROOT_BYTES
import phase4_root_recovery as recovery
import phase4_recovery_image as image

initial=importlib.import_module('prepare-phase4-initial-migration')
helper=importlib.import_module('phase4-p2-initial')
staging=importlib.import_module('stage-phase4-initial-image')
REPO=initial.REPO;WORK=initial.WORK;AREA=WORK/'p2-initial'

def receiver(role):
    require(role in ('factory','candidate'),'Finite regular-file staging role')
    code=staging.RECEIVE.replace('muos-r35s-c88-candidate.','muos-r35s-c94-'+role+'.')
    code=code.replace("target=stage/'candidate.ext4'","target=stage/'"+role+".ext4'")
    code=code.replace("'schema':88","'schema':94,'role':"+repr(role))
    code=code.replace("'candidate_sha256':expected","'image_sha256':expected")
    code=code.replace("'counter':counter","'migration_counter_binding':counter")
    require('muos-r35s-c88' not in code and "target=stage/'"+role+".ext4'" in code,'Finite receiver substitution')
    return code

def composed(value):
    stage=initial.latest(initial.AREA,'latest-complete')
    h=json.loads((stage/'host-analysis.json').read_text());r=json.loads((stage/'analysis.json').read_text())
    request=json.loads((stage/'request.json').read_text());physical=value['physical']
    require(h['passed'] is True and h['schema']==93 and sha(stage/'analysis.json')==h['consumer_analysis_sha256'] and
        sha(stage/'request.json')==h['request_sha256'],'Completed C93 composition binding')
    for n,digest in h['source_sha256'].items():require(sha(REPO/n)==digest,'Composed source changed')
    require(h['capture']==str(value['capture']) and h['capture_package']==str(value['capture_package']) and
        h['held_recovery']==str(value['held']) and h['held_recovery_ack_sha256']==sha(value['held']/'host-copy.json') and
        h['known_boot_floor']==value['known_boot'] and h['independent_host_backup_artifacts_reverified'] is True,
        'Composition must use the current capture/recovery/fence')
    mapped=lambda p:'/work/'+str(p.relative_to(WORK))
    require(request['factory_image']==mapped(value['factory']) and request['factory_sha256']==helper.C79_FACTORY_SHA256 and
        request['observed_image']==mapped(value['capture']/'root.ext4') and request['observed_sha256']==value['native']['root_sha256'] and
        request['capture_context']==value['capture_context'],'Composition source roles changed')
    for name in ['backup_private_files','backup_counter','backup_prefix_sha256']:
        require(request[name]==physical[name],'Composition backup binding')
    require(request['attempt_directory']==mapped(value['held']/'handoff') and
        request['attempt_id']==value['attempt']['attempt_id'] and request['attempt_sha256']==value['held_ack']['next_attempt_sha256'],
        'Composition current handoff binding')
    require(r['passed'] is True and r['schema']==92 and r['operation']=='compose-initial-migration-regular-image' and
        r['root_bytes']==ROOT_BYTES and r['root_fsck_exit']==0 and r['observed_counter']==value['native']['boot_sequence'] and
        r['migration_counter']==r['observed_counter']+1 and r['expected_first_C07_counter']==r['migration_counter']+1,
        'Initial composition counter/size/fsck')
    for name in ['factory_public_tree_and_stable_identity_preserved','historical_markers_preserved',
        'fresh_no_credit_seed_verified','old_seeds_removed','source_images_unchanged']:require(r[name] is True,'Initial composition incomplete')
    for name in ['seed_loaded_or_credited','physical_card_writer_available','boot_handoff_authorized','handoff_fence_created']:
        require(r[name] is False,'Unexpected composition side effect')
    recovery.sequence(r['migration_counter'])
    with image.source_image(stage/'candidate.ext4',r['candidate_sha256'],ROOT_BYTES):pass
    return stage,r

def main(host):
    os.umask(0o077)
    # This gate precedes every SSH/receiver/stage/UUID operation.
    value=initial.inputs();require(value['factory_sha256']==helper.C79_FACTORY_SHA256,'Pinned C79 factory only')
    stage,r=composed(value);AREA.mkdir(exist_ok=True)
    checks={}
    for pointer in ['latest-entry-checks','latest-transport-checks']:
        c=initial.latest(AREA,pointer);report=json.loads((c/'analysis.json').read_text())
        require(report['passed'] is True,'C94 checks required')
        for n,h in report['source_sha256'].items():require(sha(REPO/n)==h,'Tested C94 source changed')
        checks[pointer]=sha(c/'analysis.json')
    for name in ['p2-initial-prepared','initial-preparer','initial-migration','p2-controller','card-readiness','p2-recovery-native','p2-recovery-boot']:
        root=REPO/'dist/phase4'/name
        for n,h in sums(root/'SHA256SUMS').items():require(sha(root/n)==h,'Frozen proof changed')
    t=initial.legacy.prep.prep.transport();survey=t.native(host,t.INSPECT);t.validate_inspection(survey)
    live=t.native(host,"from pathlib import Path; import hashlib,json,platform; s=Path('/sys/class/block'); print(json.dumps({'kernel':platform.release(),'guard':hashlib.sha256(Path('/run/udev/rules.d/99-holo-automount.rules').read_bytes()).hexdigest(),'ro':[int((s/n/'ro').read_text()) for n in ['mmcblk0','mmcblk0p1','mmcblk0p2','mmcblk0p3']]}))")
    qualified=json.loads((REPO/'dist/phase4/p2-controller/analysis.json').read_text())
    mmc=json.loads((REPO/'dist/phase4/card-readiness/analysis.json').read_text())
    require(live['kernel']==qualified['kernel']==mmc['kernel'] and mmc['native_MMC_RO_transition_qualified_without_payload'] is True and
        live['guard']==value['physical']['automount_guard_sha256'] and live['ro']==[1,1,1,1],'Qualified kernel/MMC/guard/all-RO required')
    write_new(AREA/'package.claim',recovery.encoded({'schema':94,'capture_receipt_sha256':sha(value['capture']/'analysis.json'),
        'partial_transfer_must_be_inspected_before_replacement':True}))
    package=Path(tempfile.mkdtemp(prefix='package.',dir=AREA));bundle=package/'bundle';bundle.mkdir(mode=0o700)
    transferred={}
    for role,path,wanted in [('factory',value['factory'],helper.C79_FACTORY_SHA256),('candidate',stage/'candidate.ext4',r['candidate_sha256'])]:
        with image.source_image(path,wanted,ROOT_BYTES) as fd:
            result=subprocess.run(t.ssh(host)+[t.command(receiver(role),wanted,r['migration_counter'])],stdin=fd,capture_output=True,timeout=600)
        write_new(package/(role+'-transfer.stderr'),result.stderr)
        require(result.returncode==0,'Private '+role+' transfer failed; preserve partials, no automatic retry')
        receipt=json.loads(result.stdout)
        require(receipt['passed'] is True and receipt['schema']==94 and receipt['role']==role and
            receipt['image_sha256']==wanted and receipt['bytes']==ROOT_BYTES and
            receipt['migration_counter_binding']==r['migration_counter'] and receipt['physical_media_opened_or_written'] is False,
            'Private role transfer binding')
        transferred[role]=receipt
    old_context=json.loads((initial.latest(WORK/'p2-recovery','latest-package-recover')/'bundle/context.json').read_text())
    boot=initial.latest(WORK/'recovery-boot','latest-final-check')
    ctx={'schema':94,'operation':'migrate-initial-p2-only','physical_capture':value['physical'],
        **{n:old_context[n] for n in ['backup_directory','backup_receipt_sha256','backup_artifacts','host_backup_ack_sha256']},
        'factory_file':transferred['factory']['stage']+'/factory.ext4','factory_sha256':helper.C79_FACTORY_SHA256,
        'candidate_file':transferred['candidate']['stage']+'/candidate.ext4','candidate_sha256':r['candidate_sha256'],
        'expected_observed_sha256':value['native']['root_sha256'],'expected_migration_counter':r['migration_counter'],
        'next_attempt_id':uuid.uuid4().hex,'qualified_kernel':qualified['kernel'],
        'recovery_ack_sha256':sha(value['held']/'host-copy.json'),'recovery_boot_sha256':sha(boot/'analysis.json'),
        'known_boot_floor':value['known_boot']}
    helper.validate_context(ctx,importlib.import_module('phase4-physical-capture'),importlib.import_module('phase4_root_migration'),recovery)
    for name in helper.SOURCES-{'context.json','attempt.json','host-backup-ack.json','host-recovery-ack.json','host-recovery-boot.json'}:
        write_new(bundle/name,(REPO/'port/scripts'/name).read_bytes())
    write_new(bundle/'context.json',recovery.encoded(ctx));write_new(bundle/'attempt.json',recovery.encoded(value['attempt']))
    for name,path in [('host-backup-ack.json',value['backup_host_ack']),('host-recovery-ack.json',value['held']/'host-copy.json'),
        ('host-recovery-boot.json',boot/'analysis.json')]:write_new(bundle/name,path.read_bytes())
    helper.validate_lineage(ctx,bundle,value['attempt'],importlib.import_module('phase4_backup_core'),recovery)
    manifest={'operation':'migrate-initial-p2-only','files':{p.name:sha(p) for p in bundle.iterdir()}}
    write_new(bundle/'package.json',recovery.encoded(manifest));target='/home/deck/muos-r35s-c94-initial-'+sha(bundle/'package.json')[:12]
    original="{'phase4-offline-backup.py','phase4_backup_core.py','phase4_root_migration.py','migration-plan.json','package.json'}"
    deploy=t.DEPLOY.replace("Path('/home/deck/muos-r35s-c81')",'Path('+repr(target)+')').replace(original,repr(helper.SOURCES|{'package.json'}))
    files={p.name:{'sha256':sha(p),'data':base64.b64encode(p.read_bytes()).decode()} for p in bundle.iterdir()}
    result=t.native(host,deploy,json.dumps({'files':files}).encode())
    require(result['passed'] is True and result['helper_started'] is False and result['files']=={n:v['sha256'] for n,v in files.items()},'Finite package readback')
    record={'passed':True,'schema':94,'checks':checks,'target':target,'package_manifest_sha256':sha(bundle/'package.json'),
        'C93_composition':str(stage),'C86_capture':str(value['capture']),'transferred_regular_files':transferred,
        'physical_card_written':False,'sudo_started':False,'boot_handoff_authorized':False}
    write_new(package/'analysis.json',recovery.encoded(record));sync_dir(package)
    (AREA/'latest-package').write_text(str(package)+'\n');sync_dir(AREA)
    print('C94 initial package staged; no sudo/media write:',package)
    print('Local command: sudo /usr/bin/python3 '+target+'/phase4-p2-initial.py migrate')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True);main(p.parse_args().host)
