#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze sanitized C96 two-sector repair evidence after independent collection."""
from pathlib import Path
import importlib,json,os,shutil,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_root_migration import require
from phase4_candidate import sums

def main():
    os.umask(0o077);p=importlib.import_module('prepare-phase4-root-repair-current');area=p.AREA
    out=p.REPO/'dist/phase4/root-repair-current-native';require(not out.exists(),'Frozen native proof must not be replaced')
    stage=p.capture.initial.latest(area,'latest-complete');ack=json.loads((stage/'host-copy.json').read_text())
    require(ack['passed'] is True and ack['current_two_sector_repair_independently_verified'] is True and ack['all_aliases_RO_and_guard_verified'] is True,'Independent current repair required')
    for n,h in ack['files'].items():require(sha(stage/n)==h,'Native repair evidence changed')
    package=p.capture.initial.latest(area,'latest-package');bundle=package/'bundle';record=json.loads((package/'analysis.json').read_text())
    require(ack['package_manifest_sha256']==record['manifest_sha256']==sha(bundle/'package.json'),'Native package binding')
    ctx=json.loads((bundle/'context.json').read_text());manifest=json.loads((bundle/'package.json').read_text())
    for n,h in manifest['files'].items():
        require(sha(bundle/n)==h,'Native repair payload changed')
        if n.endswith('.py'):require(sha(p.REPO/'port/scripts'/n)==h,'Native repair source changed')
    cap,plan=p.helper.validate_lineage(bundle,ctx,importlib.import_module('phase4_backup_core'),p.recovery,p.capture.helper)
    r=json.loads((stage/'analysis.json').read_text());p.validate_report(r,ctx,plan,manifest)
    require(r['boot_sequence']==cap['expected_boot_sequence'] and r['runtime_guard_sha256']==cap['runtime_guard_sha256'],'Native current boot/guard')
    origin=Path(record['C95_current_preimage']);require(origin.resolve().is_relative_to(p.capture.AREA),'Known current preimage')
    for n in (2,3):
        for leaf in ['sb','gd','sector']:require(sha(stage/f'p{n}-{leaf}.bin')==sha(origin/f'p{n}-{leaf}.bin'),'Current source capsule differs')
    expected={n:{'offset':v['sector_offset'],'before_sha256':v['before_sha256'],'after_sha256':v['after_sha256']} for n,v in plan['patches'].items()}
    for n in ['unlock-intent.json','write-intent.json']:
        j=json.loads((stage/n).read_text())
        require(j['kind']=='CURRENT_ROOT_MODE_REPAIR_MAY_HAVE_STARTED' and j['sectors']==expected and
            j['context_sha256']==sha(bundle/'context.json') and j['current_prefix_before_sha256']==plan['current_prefix_before_sha256'] and
            j['automatic_retry_or_rollback'] is False,'Durable journal changed')
    tests=p.capture.initial.latest(area,'latest-checks');c=json.loads((tests/'analysis.json').read_text())
    require(c['passed'] is True and c['network_or_physical_media_contacted'] is False,'Offline checks required')
    for n,h in c['source_sha256'].items():require(sha(p.REPO/n)==h,'Tested source changed')
    for name,h in c['parent_proofs_sha256'].items():
        root=p.REPO/'dist/phase4'/name;require(sha(root/'SHA256SUMS')==h,'Parent proof binding changed')
        for n,wanted in sums(root/'SHA256SUMS').items():require(sha(root/n)==wanted,'Parent proof changed')
    public=Path(tempfile.mkdtemp(prefix='public-native.',dir=area))
    summary={'passed':True,'schema':96,'experiment':'C96_NATIVE_CURRENT_TWO_SECTOR_ROOT_MODE_REPAIR',
        'offline_case_count':c['case_count'],'boot_sequence':r['boot_sequence'],'written_bytes':1024,'written_sectors':2,
        'changed_byte_count':sum(len(v['changed_offsets']) for v in r['patches'].values()),'root_modes':r['root_modes'],
        'p2_fsck_exit':0,'p3_fsck_exit':0,'all_four_aliases_kernel_readonly':True,'runtime_guard_verified':True,
        'full_prefix_posthash_verified':True,'cold_readback_verified':True,'no_superblock_or_GDT_changes':True,
        'userdata_before_and_after_matches_C82':True,'all_unused_p3_sectors_hashed':False,
        'current_preimage_and_capsules_independently_verified':True,'automatic_retry_or_rollback':False,
        'seed_loaded_or_generated':False,'boot_handoff_authorized':False,'C79_migration_executed':False,
        'parent_proofs_sha256':c['parent_proofs_sha256'],'private_images_payloads_contexts_or_hashes_included':False}
    write_new(public/'analysis.json',(json.dumps(summary,indent=2)+'\n').encode())
    for n in ['analysis.json','fixtures.stdout','fixtures.stderr','fixtures.exit']:shutil.copyfile(tests/n,public/('checks.json' if n=='analysis.json' else n))
    sources={p.REPO/n for n in c['source_sha256']};sources.update([Path(__file__),p.REPO/'docs/archive/phase4/phase4-root-repair-current.md'])
    for source in sources:
        dest=public/'source'/source.relative_to(p.REPO);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
    forbidden={plan['current_prefix_before_sha256'],plan['current_prefix_after_sha256'],cap['attempt_sha256']}
    forbidden.update(v for n,v in cap['legacy_context'].items() if n.endswith('sha256'))
    forbidden.update(row['sha256'] for row in cap['legacy_context']['backup_artifacts'].values())
    for f in public.rglob('*'):
        require(not f.is_symlink(),'Public symlink')
        if f.is_file():
            require(f.suffix not in {'.backup','.ext4','.img','.raw','.bin','.dat','.tar','.gb','.sav','.state'},'Public payload')
            require(not any(v.encode() in f.read_bytes() for v in forbidden),'Private digest in public proof')
    write_new(public/'SHA256SUMS',''.join(sha(f)+'  '+str(f.relative_to(public))+'\n' for f in sorted(public.rglob('*')) if f.is_file()).encode())
    shutil.move(str(public),out);sync_dir(out.parent);print('C96 native current root repair proof:',out)

if __name__=='__main__':main()
