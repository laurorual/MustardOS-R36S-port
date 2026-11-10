#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze tested C89 preparation sources; never imply native recovery success."""
from pathlib import Path
import json,os,shutil,tempfile
from phase4_backup_core import sha,write_new
from phase4_candidate import sums
from phase4_root_migration import require

def main():
    os.umask(0o077)
    repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'p2-recovery'
    out=repo/'dist/phase4/p2-recovery-prepared'
    require(not out.exists(),'Do not replace a frozen proof')
    counts={};reports={};sources={Path(__file__),repo/'docs/archive/phase4/phase4-p2-recovery.md'}
    for name,pointer in [('eligibility','latest-checks'),('entry','latest-entry-checks'),
                         ('transport','latest-transport-checks'),('handoff','latest-handoff-checks')]:
        path=Path((area/pointer).read_text().strip())
        require(path.resolve().is_relative_to(area),'Private test record location')
        report=json.loads((path/'analysis.json').read_text())
        require(report['passed'] is True and report['physical_device_or_network_contacted'] is False
            and report['case_count']==len(report['cases']),'Successful offline checks required')
        for n,h in report['source_sha256'].items():
            source=repo/n
            require(source.resolve().is_relative_to(repo/'port') and sha(source)==h,'Tested source changed')
            sources.add(source)
        counts[name]=report['case_count'];reports[name]=report
    parents={}
    for name in ['p2-controller','card-readiness','physical-capture','recovery-image','root-recovery','backup-native']:
        proof=repo/'dist/phase4'/name
        for n,h in sums(proof/'SHA256SUMS').items():require(sha(proof/n)==h,'Prior proof changed')
        parents[name]=sha(proof/'SHA256SUMS')
    public=Path(tempfile.mkdtemp(prefix='public-prepared.',dir=area))
    analysis={'passed':True,'schema':89,'experiment':'C89_P2_RECOVERY_SOFTWARE_PREPARED_OFFLINE',
        'component_check_counts':counts,'component_check_total':sum(counts.values()),
        'physical_recovery_writer_executed':False,'physical_recovery_qualified':False,
        'physical_boot_after_recovery_qualified':False,'initial_C79_migration_qualified':False,
        'root_entrypoint_body_tested_end_to_end':False,'boot_handoff_authorized':False,
        'parent_proofs_sha256':parents,'private_images_payloads_trees_or_hashes_included':False}
    write_new(public/'analysis.json',(json.dumps(analysis,indent=2)+'\n').encode())
    for name,report in reports.items():
        write_new(public/(name+'-checks.json'),(json.dumps(report,indent=2)+'\n').encode())
    for source in sources:
        target=public/'source'/source.relative_to(repo)
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    # Private reference hashes and fence identifiers must never enter the proof.
    forbidden=[]
    handoff=Path((area/'latest-reference-handoff').read_text().strip())
    require(handoff.resolve().is_relative_to(area),'Private handoff record location')
    private=json.loads((handoff/'analysis.json').read_text())
    forbidden.extend(private[n] for n in ['attempt_id','attempt_sha256','current_reference_sha256'])
    binding_area=work/'root-recovery'
    binding=Path((binding_area/'latest-readiness').read_text().strip())
    require(binding.resolve().is_relative_to(binding_area),'Private backup record location')
    private=json.loads((binding/'binding.json').read_text())
    forbidden.extend(row['sha256'] for row in private['backup_private_files'].values())
    for file in public.rglob('*'):
        require(not file.is_symlink(),'Public symlink')
        if file.is_file():
            require(file.suffix not in {'.img','.ext4','.raw','.dat','.tar','.gb'},'Public payload')
            require(not any(value.encode() in file.read_bytes() for value in forbidden),'Private hash or fence in proof')
    write_new(public/'SHA256SUMS',''.join(sha(f)+'  '+str(f.relative_to(public))+'\n'
        for f in sorted(public.rglob('*')) if f.is_file()).encode())
    shutil.move(str(public),out)
    print('C89 prepared-only proof:',out,'cases:',sum(counts.values()))

if __name__=='__main__':main()
