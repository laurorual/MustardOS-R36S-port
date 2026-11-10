#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C76 sanitized installation/absence-backup evidence, no ELF or UUID."""
from pathlib import Path
import json, shutil, tempfile
from phase4_candidate import sha, sums
from phase4_gambatte_install import context, REPO, WORK, AREA

source,package,_,names,dirs,_,parents,_=context()
stage=Path((AREA/'latest-plan').read_text().strip())
plan=json.loads((stage/'plan.json').read_text())
r=json.loads((stage/'install-analysis.json').read_text())
c=json.loads((stage/'checks/analysis.json').read_text())
meta=json.loads((stage/'manifest.json').read_text())
assert r['passed'] and c['passed'] and c['case_count']==50
assert r['plan_sha256']==c['plan_sha256']==meta['plan_sha256']==sha(stage/'plan.json')
assert r['files_added']==9 and r['directories_added']==8 and r['existing_files_replaced']==0
assert r['preserved_prerequisites']==132 and r['root_read_only'] and r['RAM_removed']
assert r['native_loader_API1_memory_content_metadata_passed'] and r['private_state_fingerprint_matched']
assert r['infrastructure_and_global_mounts_preserved']
for key in ['core_initialized','ROM_loaded','GUI_replayed','p3_mounted','reboot_requested','caller_or_service_enabled']:
    assert r[key] is False,key
assert r['core_sha256']==package['core_sha256'] and r['combined_license_review_pending']
assert sha(stage/'absence-backup.json')==meta['backup_sha256']
assert sha(stage/'deployment.tar')==meta['deployment_sha256']
assert sha(stage/'identity-check')==meta['probe_sha256']
for n,h in sums(stage/'SHA256SUMS').items():assert sha(stage/n)==h
for label in ['survey','probe-build','before','allocate','unpack','inspect','mounts-before','dispatch','result',
              'after','mounts-after','native-ABI','final-health','cleanup','post-cleanup-health']:
    assert (stage/(label+'.exit')).read_text()=='0\n',label
assert (stage/'collected-apply.result').read_text()=='0\n'
assert 'C76_INSTALLED_ROOT_RO_NO_SERVICE_NO_TOKEN_NO_REBOOT' in (stage/'collected-apply.log').read_text()
assert (stage/'native-ABI.stdout').read_text()=='C48_GB_IDENTITY_OK API=1 memory_content=1 ROM_loaded=0\nC76_INSTALLED_CORE_METADATA_ONLY_OK\n'
assert (stage/'final-health.stdout').read_bytes()==(stage/'post-cleanup-health.stdout').read_bytes()==(stage/'before.stdout').read_bytes()
# Pin the source header used for the fresh, metadata-only probe as well as its
# MIT source and final ELF checksum; build paths themselves are not evidence.
build_path=(source/'build-vars.txt').read_text().strip().split('=',1)[1]
assert build_path.startswith('/work/')
build=WORK/build_path.removeprefix('/work/')
source_files=json.loads((REPO/'dist/phase4/gambatte-package/source-files.json').read_text())
header='libgambatte/libretro-common/include/libretro.h'
assert sha(build/header)==source_files[header]
out=REPO/'dist/phase4/gambatte-installed';assert not out.exists()
public=Path(tempfile.mkdtemp(prefix='public.',dir=AREA))
sources={Path(__file__),REPO/'docs/archive/phase4/phase4-gambatte-installed.md'}
for report in [plan,r,c]:
    for n,h in report['source_sha256'].items():assert sha(REPO/n)==h,n;sources.add(REPO/n)
for filename in ['plan.json','absence-backup.json','install-analysis.json']:
    shutil.copyfile(stage/filename,public/filename)
shutil.copyfile(stage/'checks/analysis.json',public/'checks.json')
for filename in ['fixtures.sh','stdout','stderr','exit']:
    shutil.copyfile(stage/'checks'/filename,public/('fixtures.'+filename))
for filename in ['native-ABI.stdout','native-ABI.stderr','native-ABI.exit','collected-apply.result','collected-apply.log']:
    shutil.copyfile(stage/filename,public/filename)
for src in sources:
    dest=public/'source'/src.relative_to(REPO);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
(public/'proof.json').write_text(json.dumps({'passed':True,'experiment':'C76_INSTALLED_GAMBATTE_PROOF',
    'parents_sha256':parents,'core_sha256':r['core_sha256'],'metadata_only_native_probe':True,
    'ROM_or_private_state_or_ELF_included':False,'private_boot_binding_included':False,
    'native_rollback_or_power_loss_qualified':False},indent=2)+'\n')
for path in public.rglob('*'):
    assert not path.is_symlink()
    if path.is_file():
        assert path.suffix.lower() not in {'.gb','.gbc','.so','.img','.ext4','.png','.wav','.sav','.state','.bundle','.ini','.gz','.tar'}
        data=path.read_bytes()
        assert not data.startswith(b'\x7fELF') and meta['kernel_boot_id'].encode() not in data,path
assert (WORK/'graphics-config/output/.config').read_bytes()==(WORK/'network-tools/baseline.config').read_bytes()
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out)
for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h
print('C76 source/sanitized install proof frozen:',out)
