#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C84 freeze redacted offline recovery proof. No backup payloads/capsules."""
from pathlib import Path
import json,os,shutil,tempfile
from phase4_backup_core import sha,write_new
from phase4_candidate import sums
from phase4_root_migration import require

def main():
    os.umask(0o077);repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/root-recovery'
    record=Path((area/'latest-readiness').read_text().strip());require(record.resolve().is_relative_to(area),'Readiness location')
    report=json.loads((record/'analysis.json').read_text());binding=json.loads((record/'binding.json').read_text())
    require(report['passed'] is True and sha(record/'binding.json')==report['private_binding_sha256'],'Readiness binding')
    check=Path(binding['checks']);require(check.resolve().is_relative_to(area),'Check location')
    cases=json.loads((check/'analysis.json').read_text())
    require(cases['passed'] is True and cases['case_count']==report['component_checks']==len(cases['cases']),'Checks')
    require(sha(check/'analysis.json')==binding['checks_sha256']==report['checks_sha256'],'Check binding')
    for n,h in report['source_sha256'].items():require(sha(repo/n)==h,'Prepared source changed')
    for n,h in cases['source_sha256'].items():require(report['source_sha256'][n]==h,'Tested source binding')
    for name,h in report['parent_proofs_sha256'].items():
        proof=repo/'dist/phase4'/name
        require(sha(proof/'SHA256SUMS')==h,'Parent manifest changed')
        for n,value in sums(proof/'SHA256SUMS').items():require(sha(proof/n)==value,'Parent proof changed')
    ack=Path(binding['backup_host_copy']);require(sha(ack)==binding['backup_host_copy_sha256'],'Backup receipt changed')
    complete=Path(binding['repair_completion']);require(sha(complete/'analysis.json')==binding['repair_completion_sha256'],'Repair result changed')
    # The real backup was fully hashed by readiness; recheck small private leaves
    # for redaction without serializing their bytes or metadata into this proof.
    download=Path(binding['backup_download']);private=json.loads((download/'private-files.json').read_text())
    for n,leaf in private['artifacts'].items():require(sha(download/leaf)==private['files'][n]['sha256'],'Private source changed')
    public=Path(tempfile.mkdtemp(prefix='public.',dir=area));out=repo/'dist/phase4/root-recovery'
    require(not out.exists(),'Proof exists; do not overwrite')
    result={k:v for k,v in report.items() if k not in {'private_binding_sha256','source_sha256'}}
    result.update({'physical_boot_test_performed':False,'kernel_entropy_loaded_or_credited':False,
        'synthetic_ext4_recovery_fsck_exit':0,'synthetic_backup_image_unchanged':True,
        'synthetic_public_tree_and_network_identity_preserved':True,
        'actual_entropy_policy_exercised_with_readiness_and_SeedRNG_stubs':True,
        'live_private_payloads_metadata_hashes_UUIDs_or_images_included':False})
    write_new(public/'analysis.json',(json.dumps(result,indent=2)+'\n').encode())
    shutil.copyfile(check/'analysis.json',public/'component-checks.json')
    for n in ['fixtures.stdout','fixtures.stderr','fixtures.exit']:shutil.copyfile(check/n,public/n)
    sources={repo/n for n in report['source_sha256']};sources.update([Path(__file__),repo/'docs/analysis/phase4-root-recovery.md'])
    for src in sorted(sources):
        dst=public/'source'/src.relative_to(repo);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    receipt=json.loads((download/'backup.json').read_text());context=json.loads((complete/'context.json').read_text())
    forbidden=[binding['backup_prefix_sha256'],context['mbr_sha256'],context['boot_prefix_16MiB_sha256']]
    forbidden.extend(row['sha256'] for row in receipt['artifacts'].values())
    forbidden.extend(row['sha256'] for row in binding['backup_private_files'].values())
    for p in public.rglob('*'):
        require(not p.is_symlink(),'Public symlink')
        if p.is_file():
            require(p.suffix.lower() not in {'.bin','.ext4','.img','.fat','.dat','.tar','.gb','.sav','.state'},'Public payload')
            require(not any(h.encode() in p.read_bytes() for h in forbidden),'Private hash in proof')
    write_new(public/'SHA256SUMS',''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()).encode())
    shutil.move(str(public),out)
    print('C84 redacted offline proof verified:',out)

if __name__=='__main__':main()
