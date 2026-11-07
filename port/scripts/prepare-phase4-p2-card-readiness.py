#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Deploy C90 exact-card no-payload readiness; never start sudo or unlock."""
from pathlib import Path
import argparse,base64,importlib,json,os,tempfile
from phase4_backup_core import sha,write_new
from phase4_root_migration import require
from phase4_candidate import sums

prep=importlib.import_module('prepare-phase4-p2-qualify');helper=importlib.import_module('phase4-p2-card-readiness')
REPO=prep.REPO;WORK=prep.WORK;AREA=WORK/'card-readiness'

def main(host):
    os.umask(0o077);AREA.mkdir(exist_ok=True)
    checks=prep.prep.latest(AREA,'latest-checks');tested=json.loads((checks/'analysis.json').read_text())
    require(tested['passed'] is True,'C90 tests required')
    for n,h in tested['source_sha256'].items():require(sha(REPO/n)==h,'Readiness source changed')
    for name in ['p2-controller','physical-capture','initial-image']:
        proof=REPO/'dist/phase4'/name
        for n,h in sums(proof/'SHA256SUMS').items():require(sha(proof/n)==h,'Parent proof changed')
    loop=prep.prep.latest(WORK/'p2-writer','latest-package-qualify')
    manifest=json.loads((loop/'bundle/package.json').read_text())
    for n in ['phase4_p2_controller.py','phase4_p2_write_core.py']:
        require(sha(REPO/'port/scripts'/n)==manifest['files'][n],'Physically loop-qualified controller changed')
    eligibility=prep.prep.latest(WORK/'p2-recovery','latest-checks');eligible=json.loads((eligibility/'analysis.json').read_text())
    require(eligible['passed'] is True and eligible['source_sha256']['port/scripts/phase4_p2_recovery.py']==sha(REPO/'port/scripts/phase4_p2_recovery.py'),'Target adapter tests required')
    ctx=prep.context_from_reference();t=prep.prep.transport();inspection=t.native(host,t.INSPECT);t.validate_inspection(inspection)
    live=t.native(host,"from pathlib import Path; import hashlib,json,platform; p=Path('/run/udev/rules.d/99-holo-automount.rules'); print(json.dumps({'kernel':platform.release(),'guard':hashlib.sha256(p.read_bytes()).hexdigest(),'ro':{n:int((Path('/sys/class/block')/n/'ro').read_text()) for n in ['mmcblk0','mmcblk0p1','mmcblk0p2','mmcblk0p3']}}))")
    qualified=json.loads((REPO/'dist/phase4/p2-controller/analysis.json').read_text())
    require(live['kernel']==qualified['kernel'] and live['guard']==ctx['automount_guard_sha256'] and set(live['ro'].values())=={1},'Qualified kernel/current RO/guard required')
    stage=Path(tempfile.mkdtemp(prefix='package.',dir=AREA));bundle=stage/'bundle';bundle.mkdir(mode=0o700)
    for n in helper.SOURCES-{'context.json'}:write_new(bundle/n,(REPO/'port/scripts'/n).read_bytes())
    write_new(bundle/'context.json',(json.dumps(ctx,indent=2)+'\n').encode())
    package={'operation':'card-readiness-no-payload','files':{p.name:sha(p) for p in bundle.iterdir()}}
    write_new(bundle/'package.json',(json.dumps(package,indent=2)+'\n').encode())
    target='/home/deck/muos-r35s-c90-readiness-'+sha(bundle/'package.json')[:12]
    old="{'phase4-offline-backup.py','phase4_backup_core.py','phase4_root_migration.py','migration-plan.json','package.json'}"
    code=t.DEPLOY.replace("Path('/home/deck/muos-r35s-c81')",'Path('+repr(target)+')').replace(old,repr(helper.SOURCES|{'package.json'}))
    files={p.name:{'sha256':sha(p),'data':base64.b64encode(p.read_bytes()).decode()} for p in bundle.iterdir()}
    deployed=t.native(host,code,json.dumps({'files':files}).encode())
    require(deployed['passed'] is True and deployed['helper_started'] is False and deployed['files']=={n:v['sha256'] for n,v in files.items()},'Readiness deploy/readback')
    for n,r in [('inspection.json',inspection),('protection.json',live),('analysis.json',{'passed':True,'schema':90,
        'operation':'card-readiness-no-payload','target':target,'checks_sha256':sha(checks/'analysis.json'),
        'package_manifest_sha256':sha(bundle/'package.json'),'physical_payload_writer_called':False,'helper_started':False})]:
        write_new(stage/n,(json.dumps(r,indent=2)+'\n').encode())
    (AREA/'latest-package').write_text(str(stage)+'\n');print('C90 no-payload readiness deployed/read back:',stage)
    print('Local command: sudo /usr/bin/python3 '+target+'/phase4-p2-card-readiness.py check')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True);a=p.parse_args();main(a.host)
