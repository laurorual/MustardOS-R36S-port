#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C41 host preparation evidence; keep executable and vendor bytes private."""
from pathlib import Path
import json
import shutil
import tempfile
from phase4_candidate import sha

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'muxretro'
audit=Path((area/'latest-audit').read_text().strip());ar=json.loads((audit/'analysis.json').read_text());assert ar['passed']
build=Path(ar['build_stage']);br=json.loads((build/'analysis.json').read_text());assert br['passed']
assert sha(build/'analysis.json')==ar['build_analysis_sha256']
assert sha(build/'source/bin/muxretro')==ar['binary_sha256']
checks=Path(ar['component_check_stage']);cr=json.loads((checks/'analysis.json').read_text());assert cr['passed']
assert sha(checks/'analysis.json')==ar['component_check_analysis_sha256']
pins=set()
for report in [ar,br,cr]:
    for name,digest in report['source_sha256'].items():assert sha(repo/name)==digest,name
    pins.update(report['source_sha256'])
for name,digest in cr['patched_source_sha256'].items():assert sha(build/'source'/name)==digest,name
out=repo/'dist/phase4/muxretro-host-preparation';assert not out.exists()
public=Path(tempfile.mkdtemp(prefix='public.',dir=area))
for source,relative in [(build,'build'),(audit,'audit'),(checks,'checks')]:
    (public/relative).mkdir()
    for name in ['analysis.json',relative.replace('checks','check')+'.sh',relative.replace('checks','check')+'.stdout',relative.replace('checks','check')+'.stderr',relative.replace('checks','check')+'.exit']:
        shutil.copyfile(source/name,public/relative/name)
for name in ['loader-under-test.inc','environment-under-test.inc']:shutil.copyfile(checks/name,public/'checks'/name)
pins.add(str(Path(__file__).relative_to(repo)))
for name in sorted(pins):
    target=public/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(repo/name,target)
(public/'licenses').mkdir()
shutil.copyfile(build/'source/LICENSE',public/'licenses/muos-frontend-GPL-3.0.txt')
shutil.copyfile(build/'rcheevos-2ad0b8672f68a48148620164510b963039e49eb1/LICENSE',public/'licenses/rcheevos-MIT.txt')
(public/'NOTICE.txt').write_text('C41 host preparation only. muxretro and rcheevos built privately against the existing SDK; real parser/loader components tested with the original no-content C40 core under QEMU. Final executable loader and early CLI passed, not a graphical or console qualification. No ELF, rootfs, vendor GPU bytes, ROM/BIOS, raw audio, backup, key, seed or credential is included. Existing frontend libraries, C36 and test-card state preserved.\n')
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out);print('C41 public proof frozen, executable excluded:',out)
