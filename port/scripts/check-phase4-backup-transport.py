#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C82 focused transport guards, no network or device access."""
from pathlib import Path
import ast, copy, importlib.util, json, tempfile
from unittest.mock import patch
from phase4_backup_core import sha

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/offline-backup'
spec=importlib.util.spec_from_file_location('transport',repo/'port/scripts/run-phase4-offline-backup.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
stage=Path(tempfile.mkdtemp(prefix='transport-checks.',dir=area));cases=[]
def reject(name,call):
 try:call()
 except (ValueError,OSError):cases.append(name)
 else:raise AssertionError(name)
good={'machine':'x86_64','DMI':'Jupiter','cards':[{'name':'mmcblk0','cid_sha256':t.DECK_CID,'sectors':t.CAPACITY,'sector_bytes':512}],
      'tools':dict.fromkeys(['python3','debugfs','e2fsck','fsck.fat','blkid','mount','umount','findmnt'],'/usr/bin/tool'),
      'free_bytes':4*1024**3,'var_tmp':'ext4 259:8','card_mounts':[],'run_task_paths':[]}
t.validate_inspection(good);cases.append('exact-backup-preflight')
for key,value in [('machine','aarch64'),('DMI','other'),('cards',[]),('free_bytes',1),('var_tmp','tmpfs 0:1'),('card_mounts',['/dev/mmcblk0p2 rw']),('run_task_paths',['/run/foreign'])]:
 changed=copy.deepcopy(good);changed[key]=value;reject('refuse-'+key,lambda:t.validate_inspection(changed))
changed=copy.deepcopy(good);changed['cards'][0]['cid_sha256']='0'*64
reject('refuse-wrong-card',lambda:t.validate_inspection(changed))
changed=copy.deepcopy(good);changed['tools']['debugfs']=None
reject('refuse-missing-tool',lambda:t.validate_inspection(changed))
with patch.object(t.subprocess,'run',side_effect=AssertionError('network must not run')):
 for path in ['/home/deck','/var/tmp/muos-r35s-c81-backup.12345678/../foreign','/var/tmp/muos-r35s-c81-backup.bad;reboot']:
  reject('refuse-collection-path-'+str(len(cases)),lambda:t.collect('192.168.15.13',path,stage/'plan'))
 reject('refuse-public-plan-path',lambda:t.collect('192.168.15.13','/var/tmp/muos-r35s-c81-backup.12345678',Path('/tmp/plan')))
 reject('refuse-host-shell-text',lambda:t.ssh('192.168.15.13;reboot'))
argv=t.ssh('192.168.15.13')
assert '-oStrictHostKeyChecking=yes' in argv and '-oHostKeyAlias=192.168.15.16' in argv and '-oBatchMode=yes' in argv
cases.append('pinned-batch-SSH')
bundle=t.current_package();assert bundle.is_relative_to(area);cases.append('existing-C81-bundle-verified-no-rebuild')
for code in [t.INSPECT,t.DEPLOY,t.FETCH]:ast.parse(code)
ast.parse(Path(t.__file__).read_text())
sources=[Path(__file__),Path(t.__file__)]
(stage/'analysis.json').write_text(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,'network_or_device_contacted':False,
 'C81_checks_reused_without_reexecution':72,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}},indent=2)+'\n')
(area/'latest-transport-checks').write_text(str(stage)+'\n')
print('C82 focused transport checks:',len(cases),'passed:',stage)
