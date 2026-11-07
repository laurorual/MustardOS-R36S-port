#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C74 read-only new-boot evidence, excluding UUID and private bindings."""
from pathlib import Path
import json, shutil, tempfile
from phase4_candidate import sha, sums
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'installed-provider-return'
stage=Path((area/'latest-check').read_text().strip());r=json.loads((stage/'analysis.json').read_text())
assert r['passed'] and r['RAM_removed'] and r['root_read_only']
assert r['boot_sequence']==72 and r['previous_C73_boot']==71 and r['reboot_reported_by_user']
assert r['eager_installed_provider4_and_host_CLI_passed'] and not r['persistent_device_files_written']
for name,digest in r['parent_proofs_sha256'].items():
 proof=repo/'dist/phase4'/name
 for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h
 assert sha(proof/'SHA256SUMS')==digest
sources={Path(__file__),repo/'docs/analysis/phase4-installed-provider-return.md'}
for n,h in r['source_sha256'].items():assert sha(repo/n)==h;sources.add(repo/n)
out=repo/'dist/phase4/installed-provider-return';assert not out.exists()
public=Path(tempfile.mkdtemp(prefix='public.',dir=area))
(public/'analysis.json').write_text(json.dumps({k:('private' if k=='kernel_boot_id' else v) for k,v in r.items()},indent=2)+'\n')
for label in ['native-ABI','native-ABI-initial']:
 for ext in ['stdout','stderr','exit']:shutil.copyfile(stage/(label+'.'+ext),public/(label+'.'+ext))
shutil.copyfile(stage/'console-observation.stdout',public/'console-observation.txt')
for source in sources:
 dest=public/'source'/source.relative_to(repo);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
for p in public.rglob('*'):
 if p.is_file():assert not p.read_bytes().startswith(b'\x7fELF') and r['kernel_boot_id'].encode() not in p.read_bytes()
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out)
for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h
print('C74 sanitized new-boot proof frozen:',out)
