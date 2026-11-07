#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Validate C82 root-policy against the private copied image, without card IO."""
from pathlib import Path
import json,subprocess
from phase4_backup_core import sha

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'offline-backup'
stage=Path((area/'latest-native-audit').read_text().strip());assert stage.resolve().is_relative_to(area)
prior=Path((work/'root-migration/latest-plan').read_text().strip());plan=prior/'migration-plan.json'
assert prior.resolve().is_relative_to(work/'root-migration')
code=r'''
from pathlib import Path
import json,subprocess,sys,tempfile
sys.path.insert(0,'/port/scripts')
import phase4_backup_core as c
stage=Path(sys.argv[1]);plan=json.loads(Path(sys.argv[2]).read_text());image=stage/'root.partial.ext4'
policy=c.validate_source_root_policy(json.loads((stage/'source-root-policy.json').read_text()))
before=c.sha(image);assert before==policy['diagnostic_root_sha256']
def run(args):
 assert args[0]=='debugfs' and args[-1]==str(image)
 r=subprocess.run(args,capture_output=True,text=True,timeout=30);assert r.returncode==0;return r
with tempfile.TemporaryDirectory(prefix='private-validation.',dir=stage) as target:
 target=Path(target)
 try:c.extract_private(image,target,plan,run)
 except ValueError as e:assert str(e)=='Private parent alias/owner/mode'
 else:raise AssertionError('Default policy must refuse0777')
 r=c.extract_private(image,target,plan,run,source_root_mode=policy['p2_mode'])
 assert not r['seed_loaded'] and not r['key_generated'] and r['source_root_mode']==0o777
 assert c.sha(image)==before
 print(json.dumps({'passed':True,'diagnostic_only':True,'private_file_count':len(r['files']),
  'boot_sequence':plan['survey_boot_sequence'],'source_image_unchanged':True,'default_policy_refused':True,
  'explicit_source_policy_validated':True,'device_opened':False,'seed_loaded':False,'backup_qualified':False}))
'''
container=(work/'rootfs-container.iid').read_text().strip();rel=lambda p:'/work/'+str(p.relative_to(work))
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id:uid=0,gid=0','--user=0',
 '--tmpfs','/tmp:rw,nosuid,nodev,size=64m','-v',str(work)+':/work:rw,z','-v',str(repo/'port')+':/port:ro,z',container,'python3','-c',code,rel(stage),rel(plan)]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
for ext,data in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:(stage/('private-validation.'+ext)).write_text(data)
assert r.returncode==0,(stage,r.stderr[-800:])
report=json.loads(r.stdout);assert report['passed']
report['source_sha256']={str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/scripts/phase4_backup_core.py']}
(stage/'private-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('C82 private partial root validated locally:',report['private_file_count'],'files; default still refuses0777; no card IO.')
