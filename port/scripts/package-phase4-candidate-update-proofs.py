#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C24 public proof only; excludes backups and private fingerprints."""
from pathlib import Path
import argparse,json,shutil,tempfile
from phase4_candidate import sha,sums

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/rootfs-candidate'
p=argparse.ArgumentParser();p.add_argument('operation',choices=['installed','boot']);p.add_argument('--name');a=p.parse_args()
s=Path((area/'latest-update').read_text().strip());report=json.loads((s/'install-analysis.json').read_text());assert report['passed']
meta=json.loads((s/'manifest.json').read_text());assert sha(s/'deployment.tar')==meta['deployment_sha256']
for name,digest in meta['sources'].items():assert sha(repo/name)==digest
checks=Path((area/'latest-update-checks').read_text().strip());cm=json.loads((checks/'analysis.json').read_text());assert cm['passed'] and cm['plan_sha256']==sha(s/'plan.json')
for name,digest in cm['sources'].items():assert sha(repo/name)==digest
name=a.name or ('candidate-update-'+a.operation);assert name in ['candidate-update-installed','candidate-update-boot','candidate-update-r1-installed','candidate-update-r1-boot','pcm-prime-installed'];out=repo/'dist/phase4'/name;assert not out.exists();public=Path(tempfile.mkdtemp(prefix='update-proof.',dir=area))
names=['install-analysis.json','plan.json','manifest.json']
if a.operation=='installed':
 names+=['deployment.tar','SHA256SUMS','survey.stdout','native-inspect.stdout','native-backup.stdout','apply-result.stdout','health-after.stdout','infrastructure-before.stdout','infrastructure-after.stdout']
else:
 assert json.loads((s/'reboot-return.json').read_text())['passed']
 names+=['reboot-preflight.sh','reboot-preflight.stdout','reboot-request.sh','reboot-request.stdout','reboot-request.json','reboot-return.sh','reboot-return.stdout','reboot-return.json']
for name in names:
 shutil.copyfile(s/name,public/('deployment-SHA256SUMS' if name=='SHA256SUMS' else name))
shutil.copyfile(checks/'analysis.json',public/'fixture-analysis.json')
shutil.copyfile(checks/'stdout',public/'fixture.stdout')
if json.loads((s/'plan.json').read_text())['experiment']=='C24_R1_COUNTER_UMASK':
 counter=Path((area/'latest-counter-checks').read_text().strip());cr=json.loads((counter/'analysis.json').read_text());assert cr['passed']
 for path,digest in cr['source_sha256'].items():assert sha(repo/path)==digest
 shutil.copyfile(counter/'analysis.json',public/'counter-regressions.json')
 previous=Path(json.loads((s/'plan.json').read_text())['previous_update_stage'])
 for item in ['counter-mode-repair.sh','counter-mode-repair.stdout','counter-mode-repair.json','reboot-return.json']:
  shutil.copyfile(previous/item,public/('first-boot-'+item))
if a.operation=='boot' and json.loads((s/'plan.json').read_text())['experiment']=='C24_R1_COUNTER_UMASK':
 (public/'first-boot-diagnosis.json').write_text(json.dumps({'first_direct_boot':46,'network_and_89_hashes_passed':True,'unassisted_full_contract_passed':False,'counter_mode_was':'644','counter_mode_repaired_to':'600','counter_bytes_never_reset':True,'root_cause':'C07 inherited init umask022 instead of C12 umask077','fixed_in':'C24r1 own umask077 and explicit chmod600 before rename','validated_next_boot':47},indent=2)+'\n')
source=public/'source';source.mkdir()
paths={*meta['sources'],*cm['sources'],str(Path(__file__).relative_to(repo)), 'port/scripts/prepare-phase4-candidate-update.py','port/scripts/run-phase4-candidate-update.py','port/scripts/boot-phase4-candidate-update.py'}
paths.update(['port/scripts/phase4_candidate.py','port/scripts/prepare-phase4-candidate-umask-fix.py','port/scripts/check-phase4-c07-counter.py','port/scripts/repair-phase4-candidate-counter-mode.py','port/device/rk-r35s-p0/network-diagnostic/run.sh'])
if name=='pcm-prime-installed':
 assert a.operation=='installed' and json.loads((s/'plan.json').read_text())['experiment']=='C36_PCM_PRIME'
 for pins in [json.loads((s/'plan.json').read_text())['source_sha256']]:
  for path,digest in pins.items():assert sha(repo/path)==digest
  paths.update(pins)
 prime=Path((repo/'build/phase4/audio-clock-audit/latest-prime-checks').read_text().strip())
 pr=json.loads((prime/'analysis.json').read_text());assert pr['passed']
 for path,digest in pr['source_sha256'].items():assert sha(repo/path)==digest
 shutil.copyfile(prime/'analysis.json',public/'prime-checks.json');paths.update(pr['source_sha256'])
 quantum=Path((repo/'build/phase4/audio-buffers/latest-quantum-checks').read_text().strip())
 qr=json.loads((quantum/'analysis.json').read_text());assert qr['passed']
 for path,digest in qr['source_sha256'].items():assert sha(repo/path)==digest
 shutil.copyfile(quantum/'analysis.json',public/'quantum-checks.json');paths.update(qr['source_sha256'])
for name in sorted(paths):
 dest=source/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(repo/name,dest)
(public/'NOTICE.txt').write_text('C24 directed-file proof; no disk image, private backup bytes, private-state fingerprints, seed, keys or credentials.\nRollback is tested in host fixtures; this does not qualify sudden power loss.\nOriginal dArkOSen32 and MUOSDATA are outside the write set.\n')
(public/'SHA256SUMS').write_text(''.join(sha(x)+'  '+str(x.relative_to(public))+'\n' for x in sorted(public.rglob('*')) if x.is_file()))
shutil.move(public,out);print('C24 public proof frozen:',out)
