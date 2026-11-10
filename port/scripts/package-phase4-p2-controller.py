#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze redacted C87 kernel-loop proof; no private manifests or payloads."""
from pathlib import Path
import importlib,json,os,shutil,tempfile
from phase4_backup_core import sha,write_new
from phase4_root_migration import require
from phase4_candidate import sums

def main():
    os.umask(0o077);prep=importlib.import_module('prepare-phase4-p2-qualify');area=prep.AREA;repo=prep.REPO
    complete=prep.prep.latest(area,'latest-complete-qualify');ack=json.loads((complete/'host-copy.json').read_text())
    require(ack['passed'] is True and ack['real_Valve_kernel_loop_test_validated'] is True
        and ack['real_card_all_four_aliases_RO_and_guard_verified'] is True,'Native qualification required')
    for n,h in ack['files'].items():require(sha(complete/n)==h,'Collected artifact changed')
    native=json.loads((complete/'analysis.json').read_text())
    require(sha(complete/'analysis.json')==ack['native_receipt_sha256'],'Native receipt changed')
    pkg=prep.prep.latest(area,'latest-package-qualify');package=json.loads((pkg/'analysis.json').read_text())
    require(ack['package_manifest_sha256']==sha(pkg/'bundle/package.json')==package['package_manifest_sha256'],'Package binding')
    manifest=json.loads((pkg/'bundle/package.json').read_text())
    collector=importlib.import_module('collect-phase4-p2-qualify')
    journals={d:{p.stem:json.loads(p.read_text()) for p in (complete/d).iterdir()} for d in ['success','short-write']}
    collector.validate(native,manifest,journals)
    checks={};sources=set()
    for name,pointer in [('primitive','latest-checks'),('controller','latest-controller-checks'),('transport','latest-transport-checks')]:
        p=prep.prep.latest(area,pointer);r=json.loads((p/'analysis.json').read_text())
        require(r['passed'] is True and r['case_count']==len(r['cases']),'Component checks')
        for n,h in r['source_sha256'].items():require(sha(repo/n)==h,'Tested source changed');sources.add(repo/n)
        checks[name]=(p,r)
    require(sha(checks['controller'][0]/'analysis.json')==package['checks_sha256'],'Deployed controller checks binding')
    sources.update(repo/'port/scripts'/n for n in manifest['files'] if n.endswith('.py'))
    sources.update([Path(__file__),repo/'docs/archive/phase4/phase4-p2-controller.md'])
    for n,h in manifest['files'].items():
        require(sha(pkg/'bundle'/n)==h,'Frozen bundle changed')
        if n.endswith('.py'):require(sha(repo/'port/scripts'/n)==h,'Deployed source changed')
    parents={}
    for name in ['physical-capture','root-recovery','recovery-image','root-permissions','backup-native']:
        proof=repo/'dist/phase4'/name
        for n,h in sums(proof/'SHA256SUMS').items():require(sha(proof/n)==h,'Parent proof changed')
        parents[name]=sha(proof/'SHA256SUMS')
    out=repo/'dist/phase4/p2-controller';require(not out.exists(),'Do not replace a frozen proof')
    public=Path(tempfile.mkdtemp(prefix='public-controller.',dir=area))
    report={'passed':True,'experiment':'C87_P2_CONTROLLER_VALVE_KERNEL_OWNED_LOOP_QUALIFICATION',
        'kernel':native['kernel'],'component_check_counts':{n:r['case_count'] for n,(p,r) in checks.items()},
        'native_loop_case_count':4,'native_loop_cases':native['cases'],'real_loop_p2_bytes':536870912,
        'p2_controller_implemented':True,'kernel_RO_transition_qualified_on_loop':True,
        'short_write_no_retry_no_completion_and_RO_restored':True,'all_collected_journals_and_fsync_verified':True,
        'real_card_all_four_aliases_RO_and_C83_guard_verified':True,'real_card_p2_unchanged_since_C86':True,
        'physical_card_payload_written':False,'physical_card_SETRO0':False,'physical_card_writer_entrypoint_available':False,
        'candidate_provisioned':False,'boot_handoff_authorized':False,'seed_generated_or_loaded':False,
        'physical_postboot_recovery_qualified':False,'parent_proofs_sha256':parents,'private_payloads_or_hashes_included':False}
    write_new(public/'analysis.json',(json.dumps(report,indent=2)+'\n').encode())
    for n,(p,r) in checks.items():shutil.copyfile(p/'analysis.json',public/(n+'-checks.json'))
    for p in sources:
        target=public/'source'/p.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    context=json.loads((pkg/'bundle/context.json').read_text())
    forbidden=[v for n,v in context.items() if n.endswith('sha256')]
    forbidden.extend(row['sha256'] for row in context['backup_private_files'].values())
    forbidden.extend(manifest['files'][n] for n in ['context.json','previous-failure.json'])
    for p in public.rglob('*'):
        require(not p.is_symlink(),'Public symlink')
        if p.is_file():
            require(p.suffix not in {'.img','.ext4','.raw','.dat','.tar','.gb'},'Public payload')
            require(not any(v.encode() in p.read_bytes() for v in forbidden),'Private binding in proof')
    write_new(public/'SHA256SUMS',''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()).encode())
    shutil.move(str(public),out);print('C87 redacted native qualification proof:',out)

if __name__=='__main__':main()
