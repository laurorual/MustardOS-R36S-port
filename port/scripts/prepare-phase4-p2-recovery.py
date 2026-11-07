#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Prepare finite C89 recovery only after native C86 post-handoff capture.

Never manufactures an observation/fence or starts sudo. C88 initial images
are not accepted as recovery inputs. The card stays offline until host fence
collection after a future successful recovery operation.
"""
from pathlib import Path
import argparse,base64,importlib,json,os,subprocess,tempfile,uuid
from phase4_backup_core import sha,write_new
from phase4_candidate import sums
from phase4_root_migration import require,ROOT_BYTES
import phase4_root_recovery as recovery
import phase4_recovery_image as image

prep=importlib.import_module('prepare-phase4-p2-qualify');helper=importlib.import_module('phase4-p2-recover')
REPO=prep.REPO;WORK=prep.WORK;AREA=WORK/'p2-recovery'

def require_postboot():
    pointer=WORK/'physical-capture/latest-complete-postboot'
    require(pointer.is_file(),'A real C86 post-handoff capture and independent host validation are required; keep card offline, no recovery deployment')
    stage=prep.prep.latest(WORK/'physical-capture','latest-complete-postboot')
    ack=json.loads((stage/'host-copy.json').read_text());native=json.loads((stage/'analysis.json').read_text())
    require(ack['passed'] is True and ack['mode']=='postboot' and ack['physical_postboot_validated'] is True
        and ack['independent_C85_scan_verified'] is True and ack['complete_tree_matches_native'] is True,'Native postboot capture required')
    require(sha(stage/'analysis.json')==ack['native_receipt_sha256'],'Native capture changed')
    package=prep.prep.latest(WORK/'physical-capture','latest-package-postboot')
    require(sha(package/'bundle/package.json')==ack['package_manifest_sha256'],'Capture package binding')
    manifest=json.loads((package/'bundle/package.json').read_text());context=json.loads((package/'bundle/context.json').read_text())
    collector=importlib.import_module('collect-phase4-physical-capture');collector.validate(native,manifest,context)
    for n,row in native['artifacts'].items():
        require(sha(stage/n)==row['sha256'] and (stage/n).stat().st_size==row['bytes'],'Capture artifact changed')
    require(json.loads((stage/'tree.json').read_text())==json.loads((stage/'independent/tree.json').read_text()),'Independent capture tree changed')
    require(json.loads((stage/'observation.json').read_text())==json.loads((stage/'independent/observation.json').read_text()),'Independent observation changed')
    return stage,ack,native,package,context

def main(host):
    os.umask(0o077)
    captured,ack,native,capture_package,physical=require_postboot() # before any SSH/staging.
    AREA.mkdir(exist_ok=True)
    checks={}
    for pointer in ['latest-checks','latest-entry-checks','latest-transport-checks']:
        p=prep.prep.latest(AREA,pointer);report=json.loads((p/'analysis.json').read_text())
        require(report['passed'] is True,'C89 checks required')
        for n,h in report['source_sha256'].items():require(sha(REPO/n)==h,'Tested recovery source changed')
        checks[pointer]=sha(p/'analysis.json')
    for name in ['p2-controller','card-readiness','physical-capture','recovery-image','root-recovery','backup-native']:
        proof=REPO/'dist/phase4'/name
        for n,h in sums(proof/'SHA256SUMS').items():require(sha(proof/n)==h,'Parent proof changed')
    composed=prep.prep.latest(WORK/'recovery-image','latest-compose')
    c=json.loads((composed/'analysis.json').read_text());h=json.loads((composed/'host-analysis.json').read_text());r=json.loads((composed/'request.json').read_text())
    require(h['passed'] is True and sha(composed/'analysis.json')==h['consumer_analysis_sha256']
        and sha(composed/'request.json')==h['request_sha256'],'Completed C85 recovery required')
    for n,digest in h['source_sha256'].items():require(sha(REPO/n)==digest,'Composed source changed')
    require(r['operation']=='compose' and r['observed_sha256']==native['root_sha256']
        and r['observed_image']=='/work/'+str((captured/'root.ext4').relative_to(WORK)),'Recovery must use this exact physical capture')
    attempt=json.loads((capture_package/'bundle/attempt.json').read_text())
    require(recovery.hashed(recovery.encoded(attempt))==physical['attempt_sha256']==r['attempt_sha256'],'Recovery prior intent binding')
    require(r['capture_context']==json.loads((captured/'capture-context.json').read_text()),'Recovery capture context differs')
    require(c['passed'] is True and c['fresh_no_credit_seed_verified'] is True and c['old_seeds_removed'] is True
        and c['root_image_bytes']==ROOT_BYTES and c['seed_loaded'] is False,'Composed no-credit recovery required')
    require(sha(composed/'recovery.ext4')==c['root_image_sha256'],'Composed file changed')
    binding_stage=prep.prep.latest(WORK/'root-recovery','latest-readiness')
    binding=json.loads((binding_stage/'binding.json').read_text());download=Path(binding['backup_download'])
    backup=json.loads((download/'backup.json').read_text());host_ack=Path(binding['backup_host_copy'])
    require(sha(host_ack)==binding['backup_host_copy_sha256'],'Independent backup acknowledgment changed')
    backup_ack=json.loads(host_ack.read_text())
    require(backup_ack['passed'] is True and backup_ack['independent_host_copy_verified'] is True
        and backup_ack['helper_receipt_sha256']==sha(download/'backup.json') and backup['prefix_sha256']==physical['backup_prefix_sha256'],'Known C82 backup')
    require(r['backup_image']=='/work/'+str((download/'root.ext4').relative_to(WORK))
        and r['backup_sha256']==backup['artifacts']['root.ext4']['sha256'] and r['backup_private_files']==physical['backup_private_files']
        and r['backup_counter']==physical['backup_counter'] and r['backup_prefix_sha256']==physical['backup_prefix_sha256'],'Composed backup binding')
    t=prep.prep.transport();survey=t.native(host,t.INSPECT);t.validate_inspection(survey)
    live=t.native(host,"from pathlib import Path; import json,hashlib,platform; p=Path('/run/udev/rules.d/99-holo-automount.rules'); print(json.dumps({'kernel':platform.release(),'guard':hashlib.sha256(p.read_bytes()).hexdigest(),'ro':{n:int((Path('/sys/class/block')/n/'ro').read_text()) for n in ['mmcblk0','mmcblk0p1','mmcblk0p2','mmcblk0p3']}}))")
    qualified=json.loads((REPO/'dist/phase4/p2-controller/analysis.json').read_text())
    card_qualified=json.loads((REPO/'dist/phase4/card-readiness/analysis.json').read_text())
    require(card_qualified['native_MMC_RO_transition_qualified_without_payload'] is True and card_qualified['kernel']==qualified['kernel']
        and live['kernel']==qualified['kernel'] and live['guard']==physical['automount_guard_sha256'] and set(live['ro'].values())=={1},'Qualified kernel/MMC/guard/all-RO required')
    stage=Path(tempfile.mkdtemp(prefix='package-recover.',dir=AREA));bundle=stage/'bundle';bundle.mkdir(mode=0o700)
    # Reuse the already qualified C88 regular-file receiver, with finite C89
    # role names. It exposes neither media IO nor an arbitrary destination.
    staging=importlib.import_module('stage-phase4-initial-image')
    receive=staging.RECEIVE.replace('muos-r35s-c88-candidate.','muos-r35s-c89-recovery.').replace("target=stage/'candidate.ext4'","target=stage/'recovery.ext4'").replace("'schema':88","'schema':89")
    require('muos-r35s-c88' not in receive and "target=stage/'recovery.ext4'" in receive,'Finite receiver role substitution')
    with image.source_image(composed/'recovery.ext4',c['root_image_sha256'],ROOT_BYTES) as fd:
        p=subprocess.run(t.ssh(host)+[t.command(receive,c['root_image_sha256'],c['recovery_counter'])],stdin=fd,capture_output=True,timeout=600)
    write_new(stage/'transfer.stderr',p.stderr);require(p.returncode==0,'Recovery file staging failed; do not retry automatically')
    staged=json.loads(p.stdout);require(staged['passed'] is True and staged['schema']==89 and staged['candidate_sha256']==c['root_image_sha256']
        and staged['physical_media_opened_or_written'] is False,'Recovery staging binding')
    context={'schema':89,'operation':'recover-p2-only','physical_capture':physical,'backup_directory':backup_ack['remote_backup'],
        'backup_receipt_sha256':sha(download/'backup.json'),'backup_artifacts':backup['artifacts'],
        'host_backup_ack_sha256':sha(host_ack),'recovery_file':staged['stage']+'/recovery.ext4','recovery_sha256':c['root_image_sha256'],
        'expected_observed_sha256':native['root_sha256'],'expected_recovery_counter':c['recovery_counter'],
        'next_attempt_id':uuid.uuid4().hex,'qualified_kernel':qualified['kernel']}
    helper.validate_context(context,importlib.import_module('phase4-physical-capture'),importlib.import_module('phase4_root_migration'),recovery)
    for n in helper.SOURCES-{'context.json','attempt.json','host-backup-ack.json'}:write_new(bundle/n,(REPO/'port/scripts'/n).read_bytes())
    write_new(bundle/'context.json',recovery.encoded(context));write_new(bundle/'attempt.json',recovery.encoded(attempt));write_new(bundle/'host-backup-ack.json',host_ack.read_bytes())
    manifest={'operation':'recover-p2-only','files':{p.name:sha(p) for p in bundle.iterdir()}}
    write_new(bundle/'package.json',recovery.encoded(manifest));target='/home/deck/muos-r35s-c89-recover-'+sha(bundle/'package.json')[:12]
    old="{'phase4-offline-backup.py','phase4_backup_core.py','phase4_root_migration.py','migration-plan.json','package.json'}"
    code=t.DEPLOY.replace("Path('/home/deck/muos-r35s-c81')",'Path('+repr(target)+')').replace(old,repr(helper.SOURCES|{'package.json'}))
    files={p.name:{'sha256':sha(p),'data':base64.b64encode(p.read_bytes()).decode()} for p in bundle.iterdir()}
    deployed=t.native(host,code,json.dumps({'files':files}).encode());require(deployed['passed'] is True and deployed['helper_started'] is False
        and deployed['files']=={n:v['sha256'] for n,v in files.items()},'Recovery package readback')
    report={'passed':True,'schema':89,'checks':checks,'target':target,'package_manifest_sha256':sha(bundle/'package.json'),
        'staged_recovery':staged,'C85_composition':str(composed),'C86_capture':str(captured),'physical_card_written':False,
        'sudo_started':False,'boot_handoff_authorized':False}
    write_new(stage/'analysis.json',recovery.encoded(report));(AREA/'latest-package-recover').write_text(str(stage)+'\n')
    print('C89 guarded recovery package prepared; no sudo/media writes:',stage)
    print('Local command: sudo /usr/bin/python3 '+target+'/phase4-p2-recover.py recover')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True);a=p.parse_args();main(a.host)
