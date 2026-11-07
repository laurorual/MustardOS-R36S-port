#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Prepare/deploy finite C87 loop qualification, never start sudo or card IO."""
from pathlib import Path
import argparse,base64,importlib,json,os,tempfile
from phase4_backup_core import sha,write_new
from phase4_candidate import sums
from phase4_root_migration import require
import phase4_root_recovery as recovery

prep=importlib.import_module('prepare-phase4-physical-capture')
helper=importlib.import_module('phase4-p2-qualify')
REPO=prep.REPO;WORK=prep.WORK;AREA=WORK/'p2-writer'

def context_from_reference():
    for n in ['physical-capture','recovery-image','root-recovery','root-permissions','backup-native']:
        root=REPO/'dist/phase4'/n
        for name,h in sums(root/'SHA256SUMS').items():require(sha(root/name)==h,'Parent proof changed')
    stage=prep.latest(WORK/'physical-capture','latest-complete-reference')
    ack=json.loads((stage/'host-copy.json').read_text());report=json.loads((stage/'analysis.json').read_text())
    require(ack['passed'] is True and ack['physical_reference_validated'] is True
        and ack['independent_C85_scan_verified'] is True and ack['complete_tree_matches_native'] is True,'Qualified C86 reference')
    require(sha(stage/'analysis.json')==ack['native_receipt_sha256'],'C86 receipt changed')
    for n,row in report['artifacts'].items():
        require(sha(stage/n)==row['sha256'] and (stage/n).stat().st_size==row['bytes'],'C86 artifact changed')
    package=prep.latest(WORK/'physical-capture','latest-package-reference')
    require(sha(package/'bundle/package.json')==ack['package_manifest_sha256'],'C86 package changed')
    manifest=json.loads((package/'bundle/package.json').read_text());context=json.loads((package/'bundle/context.json').read_text())
    require(sha(package/'bundle/context.json')==manifest['files']['context.json'],'C86 context changed')
    require(recovery.hashed(recovery.encoded(context))==report['context_sha256'],'C86 context receipt binding')
    capture=importlib.import_module('phase4-physical-capture')
    capture.validate_context(context,'reference',importlib.import_module('phase4_root_migration'),recovery)
    return context

def main(host,inspect_previous=False):
    os.umask(0o077);AREA.mkdir(exist_ok=True)
    check=prep.latest(AREA,'latest-controller-checks');tested=json.loads((check/'analysis.json').read_text())
    require(tested['passed'] is True and tested['case_count']==len(tested['cases']),'C87 controller tests')
    for n,h in tested['source_sha256'].items():require(sha(REPO/n)==h,'Controller tested source changed')
    primitive=prep.latest(AREA,'latest-checks');p=json.loads((primitive/'analysis.json').read_text())
    require(p['passed'] is True,'Bounded primitive tests')
    for n,h in p['source_sha256'].items():require(sha(REPO/n)==h,'Primitive tested source changed')
    previous=None
    if inspect_previous:
        failure=prep.latest(AREA,'latest-failure');error=json.loads((failure/'failure.json').read_text())
        old=prep.latest(AREA,'latest-package-qualify');old_report=json.loads((old/'analysis.json').read_text())
        require(old_report['passed'] is True and sha(old/'bundle/package.json')==old_report['package_manifest_sha256'],'Previous package binding')
        previous={'snapshot':error['snapshot'],'partial':error['partial'],
            'snapshot_files':json.loads((old/'bundle/package.json').read_text())['files']}
    context=context_from_reference();t=prep.transport();survey=t.native(host,t.INSPECT)
    inspected={**survey}
    if previous is not None:
        require(survey['run_task_paths']==[previous['snapshot']],'Only the pinned failed snapshot may be retired')
        inspected['run_task_paths']=[]
    t.validate_inspection(inspected)
    observed=t.native(host,"from pathlib import Path; import json,hashlib; p=Path('/run/udev/rules.d/99-holo-automount.rules'); print(json.dumps({'guard_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'ro':{n:int((Path('/sys/class/block')/n/'ro').read_text()) for n in ['mmcblk0','mmcblk0p1','mmcblk0p2','mmcblk0p3']}}))")
    require(observed['guard_sha256']==context['automount_guard_sha256'] and set(observed['ro'].values())<={0,1},'C83 guard/RO preflight')
    stage=Path(tempfile.mkdtemp(prefix='package-qualify.',dir=AREA));bundle=stage/'bundle';bundle.mkdir(mode=0o700)
    for n in helper.SOURCES-{'context.json','previous-failure.json'}:write_new(bundle/n,(REPO/'port/scripts'/n).read_bytes())
    write_new(bundle/'context.json',(json.dumps(context,indent=2)+'\n').encode())
    write_new(bundle/'previous-failure.json',(json.dumps(previous,indent=2)+'\n').encode())
    manifest={'operation':'qualify-loop-only','files':{p.name:sha(p) for p in bundle.iterdir()}}
    write_new(bundle/'package.json',(json.dumps(manifest,indent=2)+'\n').encode())
    target='/home/deck/muos-r35s-c87-qualify-'+sha(bundle/'package.json')[:12]
    old="{'phase4-offline-backup.py','phase4_backup_core.py','phase4_root_migration.py','migration-plan.json','package.json'}"
    code=t.DEPLOY.replace("Path('/home/deck/muos-r35s-c81')",'Path('+repr(target)+')').replace(old,repr(helper.SOURCES|{'package.json'}))
    files={p.name:{'sha256':sha(p),'data':base64.b64encode(p.read_bytes()).decode()} for p in bundle.iterdir()}
    deployed=t.native(host,code,json.dumps({'files':files}).encode())
    require(deployed['passed'] is True and deployed['helper_started'] is False
        and deployed['files']=={n:v['sha256'] for n,v in files.items()},'Deployment readback')
    result={'passed':True,'operation':'qualify-loop-only','target':target,'checks_sha256':sha(check/'analysis.json'),
        'primitive_checks_sha256':sha(primitive/'analysis.json'),'package_manifest_sha256':sha(bundle/'package.json'),
        'source_sha256':tested['source_sha256'],'deployment':deployed,'physical_card_writer_available':False}
    for name,value in [('analysis.json',result),('survey.json',survey),('protection-before.json',observed)]:
        write_new(stage/name,(json.dumps(value,indent=2)+'\n').encode())
    (AREA/'latest-package-qualify').write_text(str(stage)+'\n')
    print('C87 loop-only package/deploy verified:',stage)
    print('Local command: sudo /usr/bin/python3 '+target+'/phase4-p2-qualify.py qualify')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True)
    p.add_argument('--inspect-previous',action='store_true');a=p.parse_args();main(a.host,a.inspect_previous)
