#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C19 public host/native-RAM evidence; no fixture binary or private device data."""
from pathlib import Path
import hashlib,json,shutil
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/preferences'
stage=Path((area/'latest-checks').read_text().strip())
meta=json.loads((stage/'manifest.json').read_text());native=json.loads((stage/'native-analysis.json').read_text())
assert meta['host_passed'] and native['passed']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for n,d in meta['sources'].items():assert sha(repo/n)==d,n
assert sha(stage/'muos-preferences')==meta['production_binary_sha256']
assert sha(repo/'port/scripts/audit-phase4-preferences-ram.py')==native['audit_source_sha256']
out=repo/'dist/phase4/preferences-preparation';assert not out.exists(),'Never overwrite immutable proofs'
out.mkdir(parents=True)
def copy(src,dst):
    assert src.is_file() and not src.is_symlink(),src
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
for n in ['manifest.json','native-analysis.json','fixture.sh','stdout','stderr','build.stdout','build.stderr',
          'elf.txt','muos-preferences','muos-preferences.c','native-allocate.sh','native-allocate.stdout',
          'native-allocate.stderr','native-allocate.exit','native-smoke.sh','native-smoke.stdout',
          'native-smoke.stderr','native-smoke.exit']:
    copy(stage/n,out/n)
for p in [repo/'port/utils/muos-preferences.c',repo/'port/scripts/check-phase4-preferences.py',
          repo/'port/scripts/audit-phase4-preferences-ram.py',repo/'port/device/rk-r35s-p0/preferences/contract.json',Path(__file__)]:
    copy(p,out/'port-source'/p.relative_to(repo/'port'))
copy(repo/'port/LICENSE',out/'LICENSE')
for n in ['phase4-preferences-preparation.md','phase4-resume-checkpoint.md','roadmap.md']:
    copy(repo/'docs/archive/phase4'/n,out/'docs'/n)
files=sorted(p for p in out.rglob('*') if p.is_file())
(out/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(out))+'\n' for p in files))
for line in (out/'SHA256SUMS').read_text().splitlines():
    digest,n=line.split('  ',1);assert sha(out/n)==digest,n
print('C19 preparation proofs frozen and hash-verified:',out)
