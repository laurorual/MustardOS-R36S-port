#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze redacted real-MMC protection-transition evidence (no payload)."""
from pathlib import Path
import importlib,json,os,shutil,tempfile
from phase4_backup_core import sha,write_new
from phase4_root_migration import require
from phase4_candidate import sums

def main():
    os.umask(0o077);prep=importlib.import_module('prepare-phase4-p2-card-readiness');area=prep.AREA;repo=prep.REPO
    stage=prep.prep.prep.latest(area,'latest-complete');ack=json.loads((stage/'host-copy.json').read_text())
    require(ack['passed'] is True and ack['native_MMC_RO_transition_qualified_without_payload'] is True
        and ack['current_all_RO_and_guard_verified'] is True,'Native card readiness required')
    for n,h in ack['files'].items():require(sha(stage/n)==h,'Native receipt/journal changed')
    report=json.loads((stage/'analysis.json').read_text());pkg=prep.prep.prep.latest(area,'latest-package');p=json.loads((pkg/'analysis.json').read_text())
    require(ack['package_manifest_sha256']==sha(pkg/'bundle/package.json')==p['package_manifest_sha256'],'Package binding')
    manifest=json.loads((pkg/'bundle/package.json').read_text());collector=importlib.import_module('collect-phase4-p2-card-readiness')
    collector.validate(report,{n:json.loads((stage/'journal'/f'{n}.json').read_text()) for n in ['unlock-intent','complete']},manifest,report['kernel'])
    checks={};sources=set()
    for name,pointer in [('controller','latest-checks'),('transport','latest-transport-checks')]:
        path=prep.prep.prep.latest(area,pointer);r=json.loads((path/'analysis.json').read_text());require(r['passed'] is True,'Checks required')
        for n,h in r['source_sha256'].items():require(sha(repo/n)==h,'Tested source changed');sources.add(repo/n)
        checks[name]=(path,r)
    require(sha(checks['controller'][0]/'analysis.json')==p['checks_sha256'],'Deployed test binding')
    for n,h in manifest['files'].items():
        require(sha(pkg/'bundle'/n)==h,'Frozen package changed')
        if n.endswith('.py'):require(sha(repo/'port/scripts'/n)==h,'Deployed code changed')
    sources.update([Path(__file__),repo/'docs/archive/phase4/phase4-p2-card-readiness.md'])
    parents={}
    for name in ['p2-controller','physical-capture','initial-image']:
        root=repo/'dist/phase4'/name
        for n,h in sums(root/'SHA256SUMS').items():require(sha(root/n)==h,'Parent proof changed')
        parents[name]=sha(root/'SHA256SUMS')
    public=Path(tempfile.mkdtemp(prefix='public.',dir=area));out=repo/'dist/phase4/card-readiness';require(not out.exists(),'Do not replace proof')
    result={n:v for n,v in report.items() if n!='source_sha256'}
    result.update({'experiment':'C90_NATIVE_TEST128_KERNEL_RO_TRANSITION_WITHOUT_PAYLOAD',
        'native_MMC_RO_transition_qualified_without_payload':True,'component_check_counts':{n:r['case_count'] for n,(p,r) in checks.items()},
        'independent_host_copy_and_protection_verified':True,'parent_proofs_sha256':parents,'private_context_or_hashes_included':False})
    write_new(public/'analysis.json',(json.dumps(result,indent=2)+'\n').encode())
    for name,(path,r) in checks.items():shutil.copyfile(path/'analysis.json',public/(name+'-checks.json'))
    for source in sources:
        target=public/'source'/source.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    ctx=json.loads((pkg/'bundle/context.json').read_text());forbidden=[v for k,v in ctx.items() if k.endswith('sha256')]
    forbidden.extend(row['sha256'] for row in ctx['backup_private_files'].values());forbidden.append(manifest['files']['context.json'])
    for file in public.rglob('*'):
        require(not file.is_symlink(),'Public symlink')
        if file.is_file():require(not any(h.encode() in file.read_bytes() for h in forbidden),'Private hash in proof')
    write_new(public/'SHA256SUMS',''.join(sha(f)+'  '+str(f.relative_to(public))+'\n' for f in sorted(public.rglob('*')) if f.is_file()).encode())
    shutil.move(str(public),out);print('C90 native MMC no-payload readiness proof:',out)

if __name__=='__main__':main()
