#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze public C20 partial execution + qualified continuation, excluding backups."""
from pathlib import Path
import hashlib,json,shutil,tempfile

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/preferences'
stage=Path((area/'latest-offline-package').read_text().strip());assert stage.is_relative_to(area)
checks=json.loads((stage/'checks.json').read_text());assert checks['passed']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(stage/'deployment.tar')==checks['deployment_sha256']
assert sha(repo/'port/scripts/prepare-phase4-userdata-offline.py')==checks['prepare_source_sha256']
assert sha(repo/'port/scripts/audit-phase4-preferences-data.py')==checks['native_audit_sha256']
for name,digest in checks['native_diagnostic_sources'].items():
    assert sha(repo/'port/device/rk-r35s-p0/preferences'/name)==digest
assert json.loads((stage/'deployment-revalidation.json').read_text())['passed']
legacy=Path(checks['resumes_verified_backup_from']);assert legacy.is_relative_to(area)
root_checks=Path(checks['root_mode_checks']);assert root_checks.is_relative_to(area)
root=json.loads((root_checks/'checks.json').read_text());assert root['passed']
assert sha(repo/'port/scripts/phase4-userdata-offline-server.py')==root['server_source_sha256']
assert sha(repo/'port/scripts/phase4_userdata_io.py')==root['io_source_sha256']
assert sha(repo/'port/scripts/check-phase4-root-mode-repair.py')==root['check_source_sha256']
for name,digest in checks['manifest']['files'].items():assert sha(stage/'payload'/name)==digest
contract=json.loads((repo/'port/device/rk-r35s-p0/preferences/contract.json').read_text())
assert not contract['persistent_mode_enabled'] and not contract['real_data_preparation']['p3_filesystem_created']
final=repo/'dist/phase4/userdata-offline-partial';assert not final.exists(),'Immutable evidence already exists'
out=Path(tempfile.mkdtemp(prefix='public-proof.',dir=stage))
def copy(src,dst):
    assert src.is_file() and not src.is_symlink(),src
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
for name in ['checks.json','formatter-fsck.txt','formatter-superblock.txt','formatter-blkid.txt',
             'formatter.stdout','formatter.stderr','data-marker-readback','prefs-marker-readback',
             'preferences-inode.txt','debugfs.commands','marker-write.log','native-entrypoint.stdout',
             'native-entrypoint.stderr','deployment-revalidation.json','deck-final-payload-verify.sh',
             'deck-final-payload-verify.stdout','deck-final-payload-verify.stderr']:
    copy(stage/name,out/'prepared'/name)
for source in (stage/'payload').iterdir():copy(source,out/'prepared/payload'/source.name)
for name in ['fat-before.txt','root-before.txt','final-idle-state.sh','final-idle-state.json','summary.json']:
    copy(stage/'prior-native'/name,out/'native-partial'/name)
for action in ['backup','ack-backup','partition','format','stop']:
    for directory in legacy.glob('deck-'+action+'.*'):
        for name in ['command','stdout','stderr','exit']:
            copy(directory/name,out/'native-partial'/directory.name/name)
for directory in legacy.glob('deck-inspect.*'):
    value=json.loads((directory/'stdout').read_text());result=value['result']
    redacted={k:result.get(k) for k in ['read_only','euid','architecture','dmi_product','cards','helper_state']}
    redacted['test_card_block_tree']=[b for b in json.loads(result['blocks'])['blockdevices'] if b['name']=='mmcblk0']
    target=out/'native-partial'/directory.name/'redacted.json';target.parent.mkdir(parents=True)
    target.write_text(json.dumps(redacted,indent=2)+'\n')
for source in (legacy/'payload').iterdir():copy(source,out/'executed-legacy-payload'/source.name)
for category,path in [('io',Path(checks['io_checks'])),('protocol',Path(checks['server_checks']))]:
    assert path.is_relative_to(area)
    copy(path/'checks.json',out/'host-checks'/category/'checks.json')
for name in ['checks.json','fsck-before.txt','fsck-after.txt','inode-before.txt','inode-after.txt',
             'inode-map.txt','correction.stdout','correction.stderr']:
    copy(root_checks/name,out/'host-checks/root-mode-copy'/name)
original=area/'offline-package.ehgfexs6'
for name in ['c07-poweroff-preflight.sh','c07-poweroff-preflight.stdout','c07-poweroff-preflight.stderr',
             'c07-poweroff-request.sh','c07-poweroff-request.stdout','c07-poweroff-request.stderr','c07-poweroff-request.exit']:
    copy(original/name,out/'c07-transfer'/name)
sources=['phase4_userdata_layout.py','check-phase4-userdata-layout.py','phase4_userdata_io.py',
         'check-phase4-userdata-io.py','phase4-userdata-offline-server.py','phase4-userdata-offline-client.py',
         'check-phase4-userdata-offline-server.py','check-phase4-root-mode-repair.py',
         'inspect-phase4-userdata-offline.py','prepare-phase4-userdata-offline.py',
         'run-phase4-userdata-offline.py','audit-phase4-preferences-data.py',Path(__file__).name]
for name in sources:copy(repo/'port/scripts'/name,out/'port/scripts'/name)
for name in ['contract.json','data-functions.sh','diagnostic.sh']:
    copy(repo/'port/device/rk-r35s-p0/preferences'/name,out/'port/device/rk-r35s-p0/preferences'/name)
copy(repo/'port/LICENSE',out/'LICENSE')
for name in ['phase4-userdata-offline.md','phase4-preferences-ext4.md','phase4-resume-checkpoint.md','roadmap.md']:
    copy(repo/'docs/analysis'/name,out/'docs'/name)
(out/'STATUS.txt').write_text(
 'PARTIAL C20 EXECUTION: p3 MBR entry exists; filesystem NOT created. Test128 unmounted in Deck; R35S off.\n'
 'Root mode is still0777 after Deck automount. Corrected helper/root-mode operation are prepared, NOT active.\n'
 'Do not flash any file in this evidence folder. Follow checkpoint/resume after local helper activation.\n'
 'No private640MiB backup, rootfs, seed, credentials, private key or complete host mount inventory is included.\n')
assert not any(p.suffix in ('.ext4','.tar') or p.name in ('prefix.backup','independent-backup.json') for p in out.rglob('*'))
files=sorted(p for p in out.rglob('*') if p.is_file())
(out/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(out))+'\n' for p in files))
for line in (out/'SHA256SUMS').read_text().splitlines():
    digest,name=line.split('  ',1);assert sha(out/name)==digest,name
out.replace(final)
print('Public C20 partial execution/continuation evidence frozen; backups excluded:',final)
