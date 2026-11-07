#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C23 public reports/source, excluding the private image and GPU ELF."""
from pathlib import Path
import argparse,json,shutil,tempfile
from phase4_candidate import sha,sums

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/rootfs-candidate'
p=argparse.ArgumentParser();p.add_argument('--name',choices=['rootfs-candidate-composition','candidate-update-r1-rootfs','rootfs-c25-c26-composition','rootfs-c25-c26-calibrated','rootfs-pcm-primed'],default='rootfs-candidate-composition');a=p.parse_args()
stage=Path((area/'latest-composition').read_text().strip());checked=Path((area/'latest-checks').read_text().strip())
assert stage.is_relative_to(area) and checked.is_relative_to(area) and not (stage/'superseded.json').exists()
report=json.loads((stage/'analysis.json').read_text());checks=json.loads((checked/'analysis.json').read_text())
assert report['passed'] and checks['passed'] and not report['candidate_boot_tested']
assert report['private_only'] and not report['redistribution_approved']
assert sha(stage/'images/rootfs.ext4')==report['image_sha256']
for name,digest in {**report['sources'],**checks['source_sha256']}.items():assert sha(repo/name)==digest,name
out=repo/'dist/phase4'/a.name;assert not out.exists()
public=Path(tempfile.mkdtemp(prefix='public-proof.',dir=area))
for name in ['analysis.json','static-audit.json','changes.json','foundation.sha256','expected-tree.json',
             'debugfs.commands','install.mk','install.sh','install.stdout','install.stderr',
             'image.sh','image.stdout','image.stderr','loader.sh','loader.stdout','loader.stderr',
             'boot-contract.sh','boot-contract.stdout','readback-boot-contract.sh','readback-boot-contract.stdout']:
 shutil.copyfile(stage/name,public/name)
shutil.copyfile(checked/'analysis.json',public/'checks.json')
if (stage/'native-r1-equivalence.json').exists():shutil.copyfile(stage/'native-r1-equivalence.json',public/'native-r1-equivalence.json')
if (stage/'native-C26-equivalence.json').exists():shutil.copyfile(stage/'native-C26-equivalence.json',public/'native-C26-equivalence.json')
if a.name=='rootfs-pcm-primed':
 assert report['experiment']=='MUOS-R35S-CANDIDATE-P4-C38' and report['C36_direct_zero_PCM_integrated']
 equivalent=json.loads((stage/'native-C36-equivalence.json').read_text());assert equivalent['passed'] and equivalent['foundation97_identical']
 shutil.copyfile(stage/'native-C36-equivalence.json',public/'native-C36-equivalence.json')
if report.get('C07_counter_owns_umask_and_tmp_mode'):
 counter=Path((area/'latest-counter-checks').read_text().strip());cr=json.loads((counter/'analysis.json').read_text());assert cr['passed']
 assert cr['source_sha256']['port/device/rk-r35s-p0/network-diagnostic/run.sh']==sha(repo/'port/device/rk-r35s-p0/network-diagnostic/run.sh')
 shutil.copyfile(counter/'analysis.json',public/'counter-regressions.json')
source=public/'source';source.mkdir()
extra={'port/buildroot/Config.in',*[f'port/buildroot/package/{n}/{n}.mk' for n in ['muos-core','muos-r35s-profile','muos-r35s-session','muos-r35s-wifi-only','muos-r35s-launcher-once']]}
for name in sorted(set(report['sources'])|set(checks['source_sha256'])|{str(Path(__file__).relative_to(repo))}|extra):
 target=source/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(repo/name,target)
shutil.copyfile(stage/'target/sbin/muos-ext4-diag',public/'candidate-bootstrap')
shutil.copyfile(stage/'target/etc/default/muos-session',public/'muos-session.default')
(public/'PRIVATE-IMAGE-NOT-INCLUDED.txt').write_text('Private host composition proof only; no device write or factory-image boot qualification.\nThe 512MiB image remains under build/phase4/rootfs-candidate; private GPU terms remain unresolved.\nNo private image, vendor GPU bytes, seed, private SSH key, Wi-Fi credentials or backup is distributed here.\nFactory counter0 is a fresh-image template, never an instruction to reset the active card counter.\nThe existing card, credentials/seed/keys/counter and MUOSDATA preferences must be preserved by any future directed update.\nThis is composition from an audited C07 image and approved recipes, not a full from-scratch Buildroot rebuild.\n')
inputs={'base_image_sha256':report['base_image_sha256'],'C22_manifest_sha256':report['C22_manifest_sha256'],
        'composition_sources':report['sources'],'refusal_fixture_sources':checks['source_sha256']}
(public/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out);print('C23 immutable proof, private image excluded:',out)
