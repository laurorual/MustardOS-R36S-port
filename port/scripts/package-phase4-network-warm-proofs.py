#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze whitelisted public C13/C14/C15 evidence after each trial was restored."""
from pathlib import Path
import hashlib,json,shutil
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/network-warm'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
stages=[('network-warm-probe','latest-probe'),('network-reconfigure-trial','latest-reconfigure'),('network-controller-trial','latest-controller')]
resolved=[]
for name,pointer in stages:
    stage=Path((area/pointer).read_text().strip())
    assert json.loads((stage/'cleanup-analysis.json').read_text())['passed']
    if pointer=='latest-probe':assert json.loads((stage/'collection-analysis.json').read_text())['passed']
    else:assert json.loads((stage/'analysis.json').read_text())['collected']
    assert (stage/'user-confirmation.json').is_file()
    out=repo/'dist/phase4'/name;assert not out.exists(),'Never overwrite immutable proofs'
    resolved.append((stage,out,pointer))
def copy(src,dst):
    assert src.is_file() and not src.is_symlink(),src
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
def tree(src,dst):
    for p in sorted(src.rglob('*')):
        if p.is_file():copy(p,dst/p.relative_to(src))
for stage,out,pointer in resolved:
    out.mkdir(parents=True)
    for n in ['manifest.json','analysis.json','collection-analysis.json','cleanup-analysis.json','user-confirmation.json',
              'driver-events.txt','initial-report.txt','recovery.txt','logical.txt','probe.conf','driver-events.awk',
              'shell.stdout','shell.stderr']:
        if (stage/n).is_file():copy(stage/n,out/n)
    for label in ['install','boot-request','public-collection','collection','cleanup','numeric-failure','controller-topology']:
        for suffix in ['sh','stdout','stderr','exit']:
            p=stage/(label+'.'+suffix)
            if p.is_file():copy(p,out/p.name)
    for p in stage.glob('audit-phase4-network-*.py'):copy(p,out/p.name)
    if (stage/'payload').is_dir():tree(stage/'payload',out/'public-payload')
    meta=json.loads((stage/'manifest.json').read_text())
    checked=Path(meta['checks_stage'])
    for n in ['report.json','fixture.sh','stdout','stderr']:
        if (checked/n).is_file():copy(checked/n,out/'checks'/n)
    for n in ['phase4-network-warm.md','phase4-resume-checkpoint.md','roadmap.md']:
        copy(repo/'docs/archive/phase4'/n,out/'docs'/n)
    for p in (repo/'port/device/rk-r35s-p0/network-warm-diagnostic').iterdir():
        copy(p,out/'port-source'/p.name)
    files=sorted(p for p in out.rglob('*') if p.is_file())
    (out/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(out))+'\n' for p in files))
    for line in (out/'SHA256SUMS').read_text().splitlines():
        digest,n=line.split('  ',1);assert sha(out/n)==digest,n
    print('Frozen and hash-verified:',out)
