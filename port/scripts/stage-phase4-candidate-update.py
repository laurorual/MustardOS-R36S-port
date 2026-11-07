#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build a public-code-only C24 payload; does not contact or write a device."""
from pathlib import Path
import json,shutil,tarfile
from phase4_candidate import sha,sums

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/rootfs-candidate'
stage=Path((area/'latest-update').read_text().strip());plan=json.loads((stage/'plan.json').read_text());candidate=Path(plan['candidate_stage']);root=candidate/'target'
assert sha(candidate/'analysis.json')==plan['candidate_analysis_sha256']
for name,digest in plan['source_sha256'].items():assert sha(repo/name)==digest
payload=stage/'payload';assert not (stage/'remote-directory').exists();
if payload.exists():shutil.rmtree(payload)
(payload/'new').mkdir(parents=True)
rows=plan['files']
for row in rows:
 name=row['path'];assert not name.startswith(('var/','root/','dev/','boot/'))
 source=root/name;assert source.is_file() and not source.is_symlink() and sha(source)==row['after']['sha256']
 target=payload/'new'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);target.chmod(row['after']['mode'])
(payload/'FILES').write_text(''.join(f"{r['before']['sha256']} {r['before']['mode']:o} {r['after']['sha256']} {r['after']['mode']:o} {r['path']}\n" for r in rows))
(payload/'DIRS').write_text(''.join(f"{r['mode']:o} {r['path']}\n" for r in plan['new_directories']))
(payload/'before.sha256').write_text(''.join(r['before']['sha256']+'  '+r['path']+'\n' for r in rows if r['before']['type']=='F'))
(payload/'after.sha256').write_text(''.join(r['after']['sha256']+'  '+r['path']+'\n' for r in rows))
changed={r['path'] for r in rows}
foundation=sums(root/'usr/libexec/muos-session/prerequisites.sha256')
(payload/'unchanged.sha256').write_text(''.join(d+'  '+n.lstrip('/')+'\n' for n,d in foundation.items() if n.lstrip('/') not in changed))
# Capture only the published immutable foundation hash list, not private state.
survey=Path((area/'latest-survey').read_text().strip())
foundation_source=stage/'foundation-before-source.sha256'
(payload/'foundation-before.sha256').write_bytes(foundation_source.read_bytes() if foundation_source.exists() else (survey/'installed-foundation.sha256').read_bytes())
(payload/'boot-seq').write_text(str(plan['boot_sequence'])+'\n')
assets={'transaction.sh':repo/'port/device/rk-r35s-p0/candidate-update/transaction.sh','native.sh':repo/'port/device/rk-r35s-p0/candidate-update/native.sh','card-guard.sh':repo/'port/device/rk-r35s-p0/linux-diagnostic/card-guard.sh'}
for name,source in assets.items():shutil.copyfile(source,stage/name)
files=[p for p in stage.rglob('*') if p.is_file() and (p.is_relative_to(payload) or p.name in assets)]
(stage/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(stage))+'\n' for p in sorted(files)))
with tarfile.open(stage/'deployment.tar','w') as archive:
 for p in sorted([*files,stage/'SHA256SUMS']):
  info=archive.gettarinfo(str(p),arcname=str(p.relative_to(stage)));info.uid=info.gid=0;info.uname=info.gname='root'
  with p.open('rb') as stream:archive.addfile(info,stream)
meta={'prepared':True,'plan_sha256':sha(stage/'plan.json'),'deployment_sha256':sha(stage/'deployment.tar'),'sources':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),*assets.values()]},'private_bytes_in_payload':False,'counter_seed_SSH_network_p3_excluded':True,'image_flash':False}
(stage/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n');print('C24 payload staged:',len(rows),'public files',stage)
