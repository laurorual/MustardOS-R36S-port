#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Revise only the original cartridge; keep the qualified emulator ELF intact."""
from pathlib import Path
import json,subprocess,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/nes-core';old=Path((area/'latest').read_text().strip());prior=json.loads((old/'analysis.json').read_text());assert prior['passed']
core=Path(prior['source_stage'])/'fceumm_libretro.so';assert sha(core)==prior['core_sha256']
stage=Path(tempfile.mkdtemp(prefix='rom.',dir=area));generator=repo/'port/diagnostics/phase4-nes-demo.py'
subprocess.run(['python3',str(generator),str(stage/'r35s-flight.nes')],check=True)
report={**prior,'ROM_sha256':sha(stage/'r35s-flight.nes'),'core_rebuilt':False,'ROM_parent_stage':str(old),'ROM_parent_analysis_sha256':sha(old/'analysis.json'),'source_sha256':{**prior['source_sha256'],str(generator.relative_to(repo)):sha(generator),str(Path(__file__).relative_to(repo)):sha(Path(__file__))}}
assert sha(core)==prior['core_sha256']
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest').write_text(str(stage)+'\n');print('C47 ROM-only revision:',stage)
