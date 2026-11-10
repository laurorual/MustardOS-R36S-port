#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze offline C20 completion with fresh cache readback; exclude all backups."""
from pathlib import Path
import hashlib,json,shutil,tempfile

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/preferences'
stage=Path((area/'latest-offline-complete').read_text().strip());assert stage.is_relative_to(area)
meta=json.loads((stage/'analysis.json').read_text());assert meta['passed']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(repo/'port/scripts/collect-phase4-userdata-offline.py')==meta['collector_source_sha256']
confirmed=json.loads((stage/'root-mode-repair-cache-confirmed.json').read_text())
assert confirmed['after']['changed_bytes']==5 and confirmed['supersedes_cached_whole_device_readback']
assert sha(repo/'port/scripts/audit-phase4-userdata-alias-cache.py')==confirmed['audit_source_sha256']
legacy=Path(meta['executed_package']);assert legacy.is_relative_to(area)
final=repo/'dist/phase4/userdata-offline-complete';assert not final.exists(),'Do not replace frozen evidence'
out=Path(tempfile.mkdtemp(prefix='public-proof.',dir=stage))
def copy(source,target):
    assert source.is_file() and not source.is_symlink(),source
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
for source in stage.iterdir():
    if source.is_file():copy(source,out/'native'/source.name)
for action in ['inspect','resume','ack-backup','format','verify','repair-root-mode','stop']:
    for directory in legacy.glob('deck-'+action+'.*'):
        if action=='inspect':
            response=json.loads((directory/'stdout').read_text());raw=response.get('result',{})
            redacted={key:raw.get(key) for key in ['euid','architecture','dmi_product','cards','helper_state','mbr_phase','data_probe','raw_inspection_error']}
            target=out/'control'/directory.name/'redacted.json';target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(json.dumps(redacted,indent=2)+'\n')
        else:
            for name in ['command','stdout','stderr','exit']:copy(directory/name,out/'control'/directory.name/name)
for source in (legacy/'payload').iterdir():copy(source,out/'executed-legacy-payload'/source.name)
copy(legacy/'alias-cache-audit-prepared.json',out/'executed-cache-audit-prepared.json')
for key in ['latest-alias-cache-checks','latest-offline-io','latest-offline-server','latest-root-mode-checks']:
    directory=Path((area/key).read_text().strip());assert directory.is_relative_to(area)
    copy(directory/'checks.json',out/'checks'/key/'checks.json')
for name in ['audit-phase4-userdata-alias-cache.py','check-phase4-userdata-alias-cache.py',
             'phase4_userdata_io.py','phase4-userdata-offline-server.py',
             'check-phase4-userdata-io.py','check-phase4-userdata-offline-server.py',
             'check-phase4-root-mode-repair.py','collect-phase4-userdata-offline.py',
             'audit-phase4-preferences-data.py',Path(__file__).name]:
    copy(repo/'port/scripts'/name,out/'port/scripts'/name)
for name in ['contract.json','data-functions.sh','diagnostic.sh']:
    copy(repo/'port/device/rk-r35s-p0/preferences'/name,out/'port/device/rk-r35s-p0/preferences'/name)
for name in ['phase4-userdata-offline.md','phase4-resume-checkpoint.md','roadmap.md']:
    copy(repo/'docs/archive/phase4'/name,out/'docs'/name)
copy(repo/'port/LICENSE',out/'LICENSE')
(out/'STATUS.txt').write_text(
 'C20 OFFLINE COMPLETE: ext4 data volume/markers, root0755 and 3 offline filesystem checks passed.\n'
 'Legacy zero-byte root-mode readback was stale; cache-confirmed report supersedes it.\n'
 'No raw filesystem, private640MiB backup, seed, credential, private key or host mount inventory included.\n'
 'R35S native data mount/reboot/preferences are separate qualifications. Do not flash these proofs.\n')
assert not any(p.name in ('prefix.backup','independent-backup.json') or p.suffix in ('.ext4','.tar') for p in out.rglob('*'))
files=sorted(p for p in out.rglob('*') if p.is_file())
(out/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(out))+'\n' for p in files))
for line in (out/'SHA256SUMS').read_text().splitlines():
    digest,name=line.split('  ',1);assert sha(out/name)==digest,name
out.replace(final);print('Offline C20 fresh-readback proof frozen:',final)
