#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C20 native real-store/reboot proof, excluding private backups/keys."""
from pathlib import Path
import hashlib,json,re,shutil,tempfile

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/preferences'
initial=Path((area/'latest-data-initialize').read_text().strip())
verified=Path((area/'latest-data-verify-after-reboot').read_text().strip())
assert initial.is_relative_to(area) and verified.is_relative_to(area)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reports=[]
for directory,operation in [(initial,'initialize'),(verified,'verify-after-reboot')]:
    report=json.loads((directory/'analysis.json').read_text());reports.append(report)
    assert report['passed'] and report['operation']==operation
    assert sha(repo/'port/scripts/audit-phase4-preferences-data.py')==report['audit_source_sha256']
    for name in ['data-functions.sh','diagnostic.sh']:
        assert sha(repo/'port/device/rk-r35s-p0/preferences'/name)==report['sources'][name]
    for name in ['native.exit','cleanup.exit']:assert (directory/name).read_text().strip()=='0'
    assert 'VOLUME=60\nBRIGHTNESS=75\n' in (directory/'native.stdout').read_text()
before=int(re.search(r'^BOOT_SEQ=(\d+)$',(initial/'native.stdout').read_text(),re.M)[1])
after=int(re.search(r'^BOOT_SEQ=(\d+)$',(verified/'native.stdout').read_text(),re.M)[1])
assert (before,after)==(41,42)
assert json.loads((initial/'reboot-return.json').read_text())['passed']
assert (verified/'final-health.exit').read_text().strip()=='0'
assert 'SELECTED_KERNEL_STORAGE_ERRORS=0' in (verified/'final-health.stdout').read_text()
store=Path((area/'latest-checks').read_text().strip());assert store.is_relative_to(area)
assert sha(store/'muos-preferences')==reports[0]['sources']['muos-preferences']==reports[1]['sources']['muos-preferences']
contract=json.loads((repo/'port/device/rk-r35s-p0/preferences/contract.json').read_text())
assert not contract['persistent_mode_enabled'] and contract['real_data_preparation']['controlled_reboot_41_to_42_retained_pair']
final=repo/'dist/phase4/preferences-data-native';assert not final.exists(),'Never replace frozen evidence'
out=Path(tempfile.mkdtemp(prefix='public-proof.',dir=verified))
def copy(source,target):
    assert source.is_file() and not source.is_symlink(),source
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
for label,directory in [('boot41-initialize',initial),('boot42-verify',verified)]:
    for source in directory.iterdir():
        if source.is_file():copy(source,out/label/source.name)
for name in ['manifest.json','elf.txt','muos-preferences']:
    copy(store/name,out/'store-abi'/name)
copy(repo/'port/utils/muos-preferences.c',out/'port/utils/muos-preferences.c')
for name in ['muos-mount-namespace.c','muos-run-bounded.c']:
    copy(repo/'port/utils'/name,out/'port/utils'/name)
for name in ['contract.json','data-functions.sh','diagnostic.sh']:
    copy(repo/'port/device/rk-r35s-p0/preferences'/name,out/'port/device/rk-r35s-p0/preferences'/name)
for name in ['audit-phase4-preferences-data.py',Path(__file__).name]:
    copy(repo/'port/scripts'/name,out/'port/scripts'/name)
for name in ['phase4-resume-checkpoint.md','phase4-userdata-offline.md','roadmap.md']:
    copy(repo/'docs/analysis'/name,out/'docs'/name)
copy(repo/'port/LICENSE',out/'LICENSE')
copy(repo/'dist/phase4/userdata-offline-complete/SHA256SUMS',out/'references/offline-complete.SHA256SUMS')
summary={'passed':True,'native_boot_before':before,'native_boot_after':after,
         'volume':60,'brightness':75,'defaults_first_use_only':True,
         'real_ext4_unmount_remount_and_controlled_reboot_retention':True,
         'root_readonly_0755_global_mounts_and_network_preserved':True,
         'all_temporary_payloads_removed_p3_unmounted':True,
         'readonly_and_missing_mount_refused':True,'hardware_settings_applied':False,
         'runtime_UI_firmware_integration_enabled':False,
         'power_loss_mid_write_or_long_duration_qualified':False,'private_backup_or_key_collected':False}
(out/'analysis.json').write_text(json.dumps(summary,indent=2)+'\n')
(out/'STATUS.txt').write_text('C20 native typed store passed on test128/Panel0/kernel4.4:41->42 retained60/75.\nStorage proof only; no permanent UI/runtime integration and no power-loss-mid-write qualification.\nNever flash these proof files. Private root backups/seed/credentials/keys are excluded.\n')
assert not any(p.name in ('prefix.backup','independent-backup.json') or p.suffix in ('.ext4','.tar') for p in out.rglob('*'))
files=sorted(p for p in out.rglob('*') if p.is_file())
(out/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(out))+'\n' for p in files))
for line in (out/'SHA256SUMS').read_text().splitlines():
    digest,name=line.split('  ',1);assert sha(out/name)==digest,name
out.replace(final);print('C20 native41->42 store proofs frozen:',final)
