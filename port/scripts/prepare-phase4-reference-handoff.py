#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Seal a conservative C84 intent for the CURRENT reference, never C88.

No card IO or boot request. This is the required fence before moving the
existing C76/C86 installation back to the R35S for recovery qualification.
"""
from pathlib import Path
import argparse,importlib,json,os,tempfile,uuid
from phase4_backup_core import sha,write_new,sync_dir
from phase4_candidate import sums
from phase4_root_migration import require
import phase4_root_recovery as recovery

prep=importlib.import_module('prepare-phase4-p2-qualify')
REPO=prep.REPO;WORK=prep.WORK;AREA=WORK/'p2-recovery'

def main(host):
    os.umask(0o077);AREA.mkdir(exist_ok=True)
    require(not (AREA/'latest-reference-handoff').exists(),'Reference handoff already sealed; reuse its pinned intent, never create another automatically')
    require(not any(AREA.glob('reference-handoff.*')),'Prior partial reference handoff must be inspected; never issue a replacement fence automatically')
    for name in ['card-readiness','initial-image','p2-controller','root-recovery','physical-capture']:
        proof=REPO/'dist/phase4'/name
        for n,h in sums(proof/'SHA256SUMS').items():require(sha(proof/n)==h,'Parent proof changed')
    for pointer in ['latest-checks','latest-entry-checks','latest-transport-checks']:
        checked=prep.prep.latest(AREA,pointer);r=json.loads((checked/'analysis.json').read_text())
        require(r['passed'] is True,'C89 tests required before reference handoff')
        for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'Tested recovery sources changed')
    ctx=prep.context_from_reference();ready=prep.prep.latest(WORK/'card-readiness','latest-complete')
    ack=json.loads((ready/'host-copy.json').read_text());require(ack['passed'] is True
        and ack['native_MMC_RO_transition_qualified_without_payload'] is True,'Actual MMC readiness required')
    for n,h in ack['files'].items():require(sha(ready/n)==h,'Readiness evidence changed')
    package=prep.prep.latest(WORK/'card-readiness','latest-package')
    require(sha(package/'bundle/package.json')==ack['package_manifest_sha256'],'Readiness package binding')
    require(json.loads((package/'bundle/context.json').read_text())==ctx,'Current-reference/readiness binding')
    t=prep.prep.transport();survey=t.native(host,t.INSPECT);t.validate_inspection(survey)
    live=t.native(host,"from pathlib import Path; import hashlib,json,platform; p=Path('/run/udev/rules.d/99-holo-automount.rules'); print(json.dumps({'kernel':platform.release(),'guard':hashlib.sha256(p.read_bytes()).hexdigest(),'ro':{n:int((Path('/sys/class/block')/n/'ro').read_text()) for n in ['mmcblk0','mmcblk0p1','mmcblk0p2','mmcblk0p3']}}))")
    native=json.loads((ready/'analysis.json').read_text());require(native['kernel']==live['kernel']
        and live['guard']==ctx['automount_guard_sha256'] and set(live['ro'].values())=={1},'Handoff requires unchanged kernel/card protection')
    stage=Path(tempfile.mkdtemp(prefix='reference-handoff.',dir=AREA));journal=stage/'journal';journal.mkdir(mode=0o700)
    record=recovery.attempt_record(ctx['backup_private_files'],ctx['backup_counter'],ctx['backup_prefix_sha256'],
        ctx['reference_root_sha256'],ctx['backup_counter'],uuid.uuid4().hex)
    fence=recovery.seal_attempt(journal,record);expected=sha(fence)
    require(recovery.load_attempt(journal,record['attempt_id'],expected)==record,'Sealed reference fence readback')
    result={'passed':True,'purpose':'CURRENT_C76_REFERENCE_HANDOFF_FOR_PHYSICAL_RECOVERY_QUALIFICATION',
        'attempt_id':record['attempt_id'],'attempt_sha256':expected,'attempt_directory':str(journal),
        'current_reference_counter':ctx['backup_counter'],'current_reference_sha256':ctx['reference_root_sha256'],
        'C88_candidate_selected':False,'boot_may_have_occurred':True,'boot_success_assumed':False,
        'original_backup_reference_recovery_policy_applies':True,'automatic_rollback':False,
        'card_payload_written':False,'seed_generated_or_loaded':False,'boot_requested':False,
        'C90_host_copy_sha256':sha(ready/'host-copy.json'),'source_sha256':sha(Path(__file__))}
    write_new(stage/'analysis.json',recovery.encoded(result));write_new(stage/'inspection.json',recovery.encoded(survey))
    write_new(stage/'protection.json',recovery.encoded(live));sync_dir(journal);sync_dir(stage);sync_dir(AREA)
    write_new(AREA/'latest-reference-handoff',(str(stage)+'\n').encode())
    print('Current reference handoff fence sealed and reread; C88 NOT selected:',stage)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True);a=p.parse_args();main(a.host)
