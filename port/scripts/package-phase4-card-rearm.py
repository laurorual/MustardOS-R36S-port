#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze sanitized C95 native guard/RO/current-preimage capture evidence."""
from pathlib import Path
import importlib,json,os,shutil,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_root_migration import require
from phase4_candidate import sums

def main():
    os.umask(0o077);p=importlib.import_module('prepare-phase4-card-rearm');area=p.AREA
    out=p.REPO/'dist/phase4/card-rearm-native';require(not out.exists(),'Frozen native proof must not be replaced')
    stage=p.initial.latest(area,'latest-complete');ack=json.loads((stage/'host-copy.json').read_text())
    require(ack['passed'] is True and ack['current_preimage_and_capsules_independently_verified'] is True and
        ack['all_aliases_RO_and_guard_verified'] is True and ack['no_payload_repair_executed'] is True,'Native independent capture required')
    for n,h in ack['files'].items():require(sha(stage/n)==h,'Collected preimage changed')
    package=p.initial.latest(area,'latest-package');bundle=package/'bundle';record=json.loads((package/'analysis.json').read_text())
    require(ack['package_manifest_sha256']==record['manifest_sha256']==sha(bundle/'package.json'),'Native package binding')
    manifest=json.loads((bundle/'package.json').read_text());ctx=json.loads((bundle/'context.json').read_text());r=json.loads((stage/'analysis.json').read_text())
    for n,h in manifest['files'].items():
        require(sha(bundle/n)==h,'Package changed')
        if n.endswith('.py'):require(sha(p.REPO/'port/scripts'/n)==h,'Native source changed')
    p.validate_report(r,ctx,manifest)
    require(sha(stage/'current-prefix.backup')==r['current_prefix_sha256'],'Independent prefix binding')
    checks=p.initial.latest(area,'latest-checks');c=json.loads((checks/'analysis.json').read_text())
    require(c['passed'] is True and c['network_or_physical_media_contacted'] is False,'Offline checks required')
    for n,h in c['source_sha256'].items():require(sha(p.REPO/n)==h,'Tested source changed')
    for name,h in c['parent_proofs_sha256'].items():
        root=p.REPO/'dist/phase4'/name;require(sha(root/'SHA256SUMS')==h,'Parent binding changed')
        for n,wanted in sums(root/'SHA256SUMS').items():require(sha(root/n)==wanted,'Parent proof changed')
    public=Path(tempfile.mkdtemp(prefix='public-native.',dir=area))
    summary={'passed':True,'schema':95,'experiment':'C95_NATIVE_RUNTIME_GUARD_REARM_AND_CURRENT_PREIMAGE_CAPTURE',
        'offline_case_count':c['case_count'],'boot_sequence':r['boot_sequence'],'prefix_bytes':r['prefix_bytes'],
        'root_modes':r['root_modes'],'p2_fsck_exit':0,'p3_fsck_exit':0,'userdata_matches_C82':True,
        'all_four_aliases_kernel_readonly':True,'runtime_guard_restored':True,
        'current_preimage_and_capsules_independently_verified':True,'planned_changed_byte_count':sum(len(v['changed_offsets']) for v in r['patches'].values()),
        'physical_payload_written':False,'repair_applied':False,'seed_loaded_or_generated':False,'boot_handoff_authorized':False,
        'parent_proofs_sha256':c['parent_proofs_sha256'],'private_images_payloads_contexts_or_hashes_included':False}
    write_new(public/'analysis.json',(json.dumps(summary,indent=2)+'\n').encode())
    for n in ['analysis.json','fixtures.stdout','fixtures.stderr','fixtures.exit']:shutil.copyfile(checks/n,public/('checks.json' if n=='analysis.json' else n))
    sources={p.REPO/n for n in c['source_sha256']};sources.update([Path(__file__),p.REPO/'docs/analysis/phase4-card-rearm.md'])
    for source in sources:
        dest=public/'source'/source.relative_to(p.REPO);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
    forbidden={r['current_prefix_sha256'],r['attempt_sha256']}
    forbidden.update(v for n,v in ctx['legacy_context'].items() if n.endswith('sha256'))
    forbidden.update(row['sha256'] for row in ctx['legacy_context']['backup_artifacts'].values())
    for f in public.rglob('*'):
        require(not f.is_symlink(),'Public symlink')
        if f.is_file():
            require(f.suffix not in {'.backup','.ext4','.img','.raw','.bin','.dat','.tar','.gb','.sav','.state'},'Public payload')
            require(not any(v.encode() in f.read_bytes() for v in forbidden),'Private digest in public proof')
    write_new(public/'SHA256SUMS',''.join(sha(f)+'  '+str(f.relative_to(public))+'\n' for f in sorted(public.rglob('*')) if f.is_file()).encode())
    shutil.move(str(public),out);sync_dir(out.parent);print('C95 native protection/capture proof:',out)

if __name__=='__main__':main()
