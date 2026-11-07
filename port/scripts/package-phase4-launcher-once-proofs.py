#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze immutable C25 public proofs; never include backups or a rootfs."""
from pathlib import Path
import argparse, json, shutil, tempfile
from phase4_candidate import sha

repo=Path(__file__).resolve().parents[2]; area=repo/'build/phase4/rootfs-candidate'
p=argparse.ArgumentParser(description=__doc__); p.add_argument('operation',choices=['installed','session','fallback']); p.add_argument('--trial',type=Path); a=p.parse_args()
s=Path((area/'latest-update').read_text().strip()); installation=s; plan=json.loads((s/'plan.json').read_text()); assert plan['experiment']=='C25_LAUNCHER_ONCE'
assert json.loads((s/'install-analysis.json').read_text())['passed']
meta=json.loads((s/'manifest.json').read_text()); assert sha(s/'deployment.tar')==meta['deployment_sha256'] and sha(s/'plan.json')==meta['plan_sha256']
tc=Path((area/'latest-update-checks').read_text().strip()); tx=json.loads((tc/'analysis.json').read_text()); assert tx['passed'] and tx['plan_sha256']==sha(s/'plan.json')
pc=Path((area/'latest-c25-checks').read_text().strip()); policy=json.loads((pc/'analysis.json').read_text()); assert policy['passed']
pins={**plan['source_sha256'],**meta['sources'],**tx['sources'],**policy['source_sha256']}
for name,digest in pins.items(): assert sha(repo/name)==digest,name
if a.trial:
 assert a.operation!='installed'
 s=a.trial.resolve(); assert s.is_relative_to(area) and s.name.startswith('c25-physical.')
 tm=json.loads((s/'trial.json').read_text())
 assert tm['installation_stage']==str(installation) and tm['plan_sha256']==sha(installation/'plan.json')
 assert tm['previous_fallback_sha256']==sha(installation/'c25-fallback.json')
name=({'session':'launcher-once-physical-boot','fallback':'launcher-once-physical-fallback'} if a.trial else {'installed':'launcher-once-installed','session':'launcher-once-boot','fallback':'launcher-once-fallback'})[a.operation]
out=repo/'dist/phase4'/name; assert not out.exists(),'Do not overwrite approved evidence'
public=Path(tempfile.mkdtemp(prefix='c25-proof.',dir=area))
names=['plan.json','manifest.json','install-analysis.json']
if a.trial:
 names+=['trial.json']
 names+=['ram-control-checks.json','ram-control-fixtures.sh','ram-control-fixtures.stdout','preparation-retry.json']
 if (s/'physical-observation.json').exists(): names+=['physical-observation.json']
 if a.operation=='session' and (s/'audio-analysis.json').exists():
  names+=['audio-analysis.json','audio-active-audit.sh','audio-active-audit.stdout','audio-active-audit.stderr','audio-active-audit.exit','audio-active-graph.json','audio-active-graph.exit','audio-active-top.stdout','audio-active-top.stderr','audio-active-top.exit']
if a.operation=='installed':
 assert json.loads((s/'c25-negative.json').read_text())['passed']
 names+=['deployment.tar','survey.stdout','native-inspect.stdout','native-backup.stdout','apply-result.stdout','health-after.stdout','infrastructure-before.stdout','infrastructure-after.stdout','c25-negative.sh','c25-negative.stdout','c25-negative.json']
 shutil.copyfile(s/'SHA256SUMS',public/'deployment-SHA256SUMS')
else:
 key='c25-collect' if a.operation=='session' else 'c25-fallback'
 assert json.loads((s/(key+'.json')).read_text())['passed']
 names += [key+'.json',key+'-health.sh',key+'-health.stdout',key+'-final-health.sh',key+'-final-health.stdout']
 shutil.copytree(s/key,public/'collected')
 if a.operation=='session':
  names += ['c25-arm.json','c25-reboot.json','c25-running.sh','c25-running.stdout','c25-running.json','c25-infrastructure-running.stdout','c25-infrastructure-stopped.stdout']
  if (s/'collection-retry.json').exists(): names += ['collection-retry.json',*['first-collection-final-health.'+x for x in ['sh','stdout','stderr','exit']]]
 else: names += ['c25-fallback-reboot.json']
for name in names:
 origin=installation if name in ['plan.json','manifest.json','install-analysis.json'] else s
 shutil.copyfile(origin/name,public/name)
for source,name in [(tc/'analysis.json','transaction-analysis.json'),(tc/'stdout','transaction.stdout'),(pc/'analysis.json','policy-analysis.json'),(pc/'stdout','policy.stdout'),(pc/'kconfig.stdout','kconfig.stdout')]: shutil.copyfile(source,public/name)
sources=set(pins)|{str(Path(__file__).relative_to(repo)),'port/scripts/run-phase4-launcher-once.py','port/scripts/run-phase4-candidate-update.py','port/scripts/phase4_candidate.py'}
for name in sorted(sources):
 assert name.startswith('port/')
 target=public/'source'/name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(repo/name,target)
(public/'NOTICE.txt').write_text('C25 public code and bounded one-shot evidence. No rootfs/GPU blob, backup, private fingerprint, seed, SSH key or network credential. Original dArkOSen32 preserved. Defaults remain off; no permanent launcher. Sudden power loss and complete factory-image boot are unqualified.\n')
(public/'SHA256SUMS').write_text(''.join(sha(f)+'  '+str(f.relative_to(public))+'\n' for f in sorted(public.rglob('*')) if f.is_file()))
shutil.move(public,out); print('C25 public proof frozen:',out)
