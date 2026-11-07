#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C42 native CPU preflight with its RAM cleanup and lock regressions."""
from pathlib import Path
import json
import shutil
import tempfile
from phase4_candidate import sha

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/muxretro'
stage=Path((area/'latest-cpu').read_text().strip());report=json.loads((stage/'analysis.json').read_text());assert report['passed']
checks=Path((area/'latest-cpu-lock-checks').read_text().strip());cr=json.loads((checks/'analysis.json').read_text());assert cr['passed']
pins=set()
for result in [report,cr]:
    for name,digest in result['source_sha256'].items():assert sha(repo/name)==digest,name
    pins.update(result['source_sha256'])
out=repo/'dist/phase4/muxretro-native-cpu';assert not out.exists()
public=Path(tempfile.mkdtemp(prefix='cpu-public.',dir=area))
for name in ['analysis.json','intent.json']:
    shutil.copyfile(stage/name,public/name)
for label in ['preflight','native','postflight','cleanup']:
    for ext in ['sh','stdout','stderr','exit']:shutil.copyfile(stage/(label+'.'+ext),public/(label+'.'+ext))
shutil.copyfile(checks/'analysis.json',public/'lock-checks.json')
pins.add(str(Path(__file__).relative_to(repo)))
for name in pins:
    target=public/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(repo/name,target)
(public/'NOTICE.txt').write_text('C42 actual R35S CPU/loader/API preflight in RAM only. muxretro early version/help and argument refusal, plus original C40 core/checker, ran under deadlines. This is not graphical presentation, ALSA playback or physical-input qualification. RAM binaries removed; rootRO/foundation97/network/PCMclosed preserved. No ELF, image, proprietary blob, raw audio, backup, seed, key or credential included.\n')
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out);print('C42 native CPU proof frozen:',out)
