#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Archive public C19 lab and C20 plan evidence; never include card root backups."""
from pathlib import Path
import hashlib,json,shutil

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/preferences'
stage=Path((area/'latest-ext4').read_text().strip());survey=Path((area/'latest-layout').read_text().strip())
assert stage.is_relative_to(area) and survey.is_relative_to(area)
meta=json.loads((stage/'manifest.json').read_text());native=json.loads((stage/'native-analysis.json').read_text())
plan=json.loads((survey/'userdata-plan.json').read_text());checks=json.loads((survey/'layout-checks.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert meta['host_passed'] and native['passed'] and checks['passed'] and not plan['execution_enabled']
for n,d in meta['sources'].items():assert sha(repo/n)==d,n
for n,d in meta['payloads'].items():assert sha(stage/n)==d,n
assert sha(repo/'port/scripts/audit-phase4-preferences-ext4.py')==native['audit_source_sha256']
assert sha(stage/'after.ext4')==native['after_image_sha256']
assert sha(repo/'port/scripts/phase4_userdata_layout.py')==plan['planner_sha256']
out=repo/'dist/phase4/preferences-ext4';assert not out.exists(),'Never replace immutable evidence'
out.mkdir(parents=True)
def copy(src,dst):
    assert src.is_file() and not src.is_symlink(),src
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
for n in ['manifest.json','native-analysis.json','elf.txt','superblock.txt','fsck-before.txt','fsck-after.txt',
          'record-after.txt','debugfs-after.stderr','offline-check.stderr','build.stdout','build.stderr',
          'fixture.sh','stdout','stderr','phase4-preferences-ext4','muos-preferences',
          'native-allocate.sh','native-allocate.stdout','native-allocate.stderr','native-allocate.exit',
          'native-smoke.sh','native-smoke.stdout','native-smoke.stderr','native-smoke.exit',
          'native-cleanup.sh','native-cleanup.stdout','native-cleanup.stderr','native-cleanup.exit']:
    copy(stage/n,out/'lab'/n)
for n in ['mbr.before','mbr.proposed','userdata-plan.json','layout-checks.json','read-mbr.sh',
          'read-mbr.stderr','read-inventory.sh','inventory.json','inventory.stdout','inventory.stderr']:
    copy(survey/n,out/'plan-only'/n)
negative=Path(meta['host_results_reused_from']);assert negative.is_relative_to(area)
for n in ['native-upload.stderr','native-cleanup.stdout','native-cleanup.exit']:
    copy(negative/n,out/'tar-z-refused-before-mount'/n)
for n in ['port/diagnostics/phase4-preferences-ext4.c','port/scripts/prepare-phase4-preferences-ext4.py',
          'port/scripts/audit-phase4-preferences-ext4.py','port/utils/muos-preferences.c',
          'port/device/rk-r35s-p0/preferences/contract.json','port/scripts/phase4_userdata_layout.py',
          'port/scripts/check-phase4-userdata-layout.py','port/scripts/inspect-phase4-userdata-offline.py',
          'port/scripts/package-phase4-preferences-ext4-proofs.py','port/LICENSE',
          'docs/analysis/phase4-preferences-ext4.md','docs/analysis/phase4-resume-checkpoint.md','docs/analysis/roadmap.md']:
    copy(repo/n,out/n)
(out/'NOT-A-CARD-IMAGE.txt').write_text(
 'Native ext4 tmpfs-loop proof and OFFLINE PLAN ONLY. No bootable/release image.\n'
 'Do not write mbr.proposed directly to media. See separate C20 partial/continuation evidence.\n'
 'No card filesystem, seed, credentials, keys, or private backup is included.\n')
files=sorted(p for p in out.rglob('*') if p.is_file())
(out/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(out))+'\n' for p in files))
for line in (out/'SHA256SUMS').read_text().splitlines():
    digest,n=line.split('  ',1);assert sha(out/n)==digest,n
print('C19 native ext4/C20 plan public proofs frozen:',out)
