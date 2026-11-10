#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C92 offline checks/source evidence. Never packages a private image."""
from pathlib import Path
import json,os,shutil,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_candidate import sums
from phase4_root_migration import require

def main():
    os.umask(0o077);repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/initial-migration'
    check=Path((area/'latest-checks').read_text().strip())
    require(check.resolve().is_relative_to(area),'Private test record location')
    report=json.loads((check/'analysis.json').read_text())
    require(report['passed'] is True and report['case_count']==len(report['cases']) and
        report['physical_device_or_network_contacted'] is False and report['production_512MiB_images_composed'] is False,
        'Completed offline-only checks required')
    for n,h in report['source_sha256'].items():require(sha(repo/n)==h,'Tested source changed')
    for name,h in report['parent_proofs_sha256'].items():
        root=repo/'dist/phase4'/name;require(sha(root/'SHA256SUMS')==h,'Parent proof binding changed')
        for n,wanted in sums(root/'SHA256SUMS').items():require(sha(root/n)==wanted,'Parent proof changed')
    out=repo/'dist/phase4/initial-migration';require(not out.exists(),'Do not replace a frozen proof')
    public=Path(tempfile.mkdtemp(prefix='public.',dir=area))
    summary={'passed':True,'schema':92,'experiment':'C92_FRESH_INITIAL_C79_REGULAR_IMAGE_COMPOSITION_OFFLINE',
        'component_check_count':report['case_count'],'real_32MiB_ext4_fixtures':True,
        'physical_device_or_network_contacted':False,'production_512MiB_images_composed':False,
        'physical_card_writer_available':False,'boot_handoff_authorized':False,'handoff_fence_created':False,
        'seed_loaded_or_credited':False,'initial_C79_physical_migration_qualified':False,
        'parent_proofs_sha256':report['parent_proofs_sha256'],'private_images_payloads_or_hashes_included':False}
    write_new(public/'analysis.json',(json.dumps(summary,indent=2)+'\n').encode())
    for name in ['analysis.json','fixtures.stdout','fixtures.stderr','fixtures.exit']:
        shutil.copyfile(check/name,public/('component-checks.json' if name=='analysis.json' else name))
    sources={repo/n for n in report['source_sha256']}
    sources.update([Path(__file__),repo/'docs/archive/phase4/phase4-initial-migration.md'])
    for source in sources:
        require(source.resolve().is_relative_to(repo),'Repository source required')
        target=public/'source'/source.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
    for file in public.rglob('*'):
        require(not file.is_symlink(),'Public symlink')
        if file.is_file():require(file.suffix.lower() not in {'.ext4','.img','.raw','.bin','.dat','.tar','.gb','.sav','.state'},'Public payload')
    write_new(public/'SHA256SUMS',''.join(sha(p)+'  '+str(p.relative_to(public))+'\n'
        for p in sorted(public.rglob('*')) if p.is_file()).encode())
    shutil.move(str(public),out);sync_dir(out.parent);print('C92 offline proof:',out)

if __name__=='__main__':main()
