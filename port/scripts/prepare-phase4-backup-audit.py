#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C82 deploy a finite partial-image diagnostic, without starting privileged IO."""
from pathlib import Path
import argparse,base64,importlib.util,json,os,tempfile
from phase4_backup_core import sha,write_new

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/offline-backup'
spec=importlib.util.spec_from_file_location('transport',repo/'port/scripts/run-phase4-offline-backup.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True);args=p.parse_args()
os.umask(0o077);prior=t.current_package()/'bundle'
checks=Path((area/'latest-audit-checks').read_text().strip());r=json.loads((checks/'analysis.json').read_text());assert r['passed']
for name,h in r['source_sha256'].items():assert sha(repo/name)==h
stage=Path(tempfile.mkdtemp(prefix='audit-package.',dir=area));bundle=stage/'bundle';bundle.mkdir(mode=0o700)
names=['audit-phase4-backup-private.py','phase4_backup_core.py','phase4_root_migration.py','migration-plan.json']
for name in names:
 source=repo/'port/scripts'/name if name.startswith('audit-') else prior/name
 write_new(bundle/name,source.read_bytes())
manifest={'diagnostic_only':True,'files':{n:sha(bundle/n) for n in names}}
write_new(bundle/'package.json',(json.dumps(manifest,indent=2)+'\n').encode())
files={f.name:{'sha256':sha(f),'data':base64.b64encode(f.read_bytes()).decode()} for f in bundle.iterdir()}
target='/home/deck/muos-r35s-c82-audit-'+sha(bundle/'audit-phase4-backup-private.py')[:12]
code=t.DEPLOY.replace("Path('/home/deck/muos-r35s-c81')","Path('"+target+"')").replace("'phase4-offline-backup.py'","'audit-phase4-backup-private.py'")
result=t.native(args.host,code,json.dumps({'files':files}).encode())
assert result['passed'] and not result['helper_started'] and result['files']=={n:v['sha256'] for n,v in files.items()}
write_new(stage/'analysis.json',(json.dumps({'passed':True,'diagnostic_only':True,'checks_sha256':sha(checks/'analysis.json'),'deployment':result},indent=2)+'\n').encode())
(area/'latest-audit-package').write_text(str(stage)+'\n')
print('C82 audit deployed/verified, not started:',stage)
print('Local command: sudo /usr/bin/python3 '+target+'/audit-phase4-backup-private.py /var/tmp/muos-r35s-c81-backup.chy99nhv')
