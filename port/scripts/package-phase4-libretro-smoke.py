#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C40 source and host evidence; leave diagnostic ELF files private."""
from pathlib import Path
import json
import shutil
import tempfile
from phase4_candidate import sha

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
stage=Path((work/'libretro-smoke/latest').read_text().strip())
assert stage.resolve().is_relative_to(work/'libretro-smoke')
report=json.loads((stage/'analysis.json').read_text())
assert report['passed'] and report['QEMU_loader_and_API_passed'] and not report['native_console_tested']
for name,digest in report['source_sha256'].items():assert sha(repo/name)==digest,name
for name,digest in report['binary_sha256'].items():assert sha(stage/name)==digest,name
header=work/'foundation/frontend-source/retro/core/libretro.h'
assert sha(header)==report['libretro_header_sha256']
out=repo/'dist/phase4/libretro-smoke-preparation';assert not out.exists(),'Never overwrite frozen evidence'
public=Path(tempfile.mkdtemp(prefix='public.',dir=work/'libretro-smoke'))
for name in ['analysis.json','build.sh','build.stdout','build.stderr','build.exit']:shutil.copyfile(stage/name,public/name)
for name in [*report['source_sha256'],str(Path(__file__).relative_to(repo))]:
    target=public/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(repo/name,target)
(public/'libretro-header-license.txt').write_text(header.read_text().split('*/',1)[0]+'*/\n')
(public/'NOTICE.txt').write_text('C40 diagnostic preparation only: original MIT no-content core and API checker, built with the existing AArch64 SDK and tested under QEMU against the private C38 userspace loader. No console test or muxretro integration qualification. No ELF, ROM, BIOS, image, vendor GPU bytes, raw audio, key, credential or private backup included. Installed C36 policy and the test card were not changed.\n')
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out)
print('C40 public preparation proof, private ELF excluded:',out)
