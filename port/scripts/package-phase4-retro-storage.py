#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C43 reports without original preference fingerprints or RAM copies."""
from pathlib import Path
import json,shutil,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/muxretro'
stage=Path((area/'latest-storage').read_text().strip());report=json.loads((stage/'analysis.json').read_text())
assert report['passed'] and report['real_preferences_read_only'] and report['preferences_byte_exact_after']
checks=Path(report['host_checks_stage']);assert sha(checks/'analysis.json')==report['host_checks_sha256']
cr=json.loads((checks/'analysis.json').read_text());assert cr['passed']
pins=set()
for result in [report,cr]:
    for name,digest in result['source_sha256'].items():assert sha(repo/name)==digest,name
    pins.update(result['source_sha256'])
out=repo/'dist/phase4/retro-ram-storage';assert not out.exists()
public=Path(tempfile.mkdtemp(prefix='storage-public.',dir=area))
for name in ['analysis.json','intent.json']:shutil.copyfile(stage/name,public/name)
for label in ['preflight','prepare','native','postflight','cleanup']:
    for ext in ['sh','stdout','stderr','exit']:shutil.copyfile(stage/(label+'.'+ext),public/(label+'.'+ext))
shutil.copyfile(checks/'analysis.json',public/'host-checks.json')
pins.add(str(Path(__file__).relative_to(repo)))
for name in pins:
    target=public/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(repo/name,target)
(public/'NOTICE.txt').write_text('C43 native storage-isolation preparation. Real MUOSDATA/preferences mounted RO+noload; only a RAM copy was loaded. Existing S90 storage adapter bound tmpfs aliases, verified a disposable write, and stopped. Original preference bytes and global mountinfo unchanged, RAM removed, rootRO/foundation97/network preserved. No graphical/audio/input test. No ELF, rootfs, preference copy or fingerprint, proprietary blob, backup, key, seed or credential included.\n')
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out);print('C43 public RAM-storage proof frozen:',out)
