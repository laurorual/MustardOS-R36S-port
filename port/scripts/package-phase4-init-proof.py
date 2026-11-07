#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze lifecycle evidence and original service code, excluding GPU runtime."""
from pathlib import Path
import hashlib
import json
import shutil
import tarfile

repo=Path(__file__).resolve().parents[2]
work=repo/'build/phase4'
f=work/'init-services'
foundation=work/'foundation'
assert (foundation/'audit.exit').read_text().strip()=='0'
approved=json.loads((f/'ui-approved.json').read_text())
lifecycle=json.loads((f/'lifecycle-approved.json').read_text())
compiled=json.loads((f/'build-manifest.json').read_text())
assert approved['user_confirmed'] and lifecycle['passed']
assert approved['tested_services']==compiled
for name,h in compiled['inputs'].items():
    assert hashlib.sha256((repo/name).read_bytes()).hexdigest()==h,name
stage=Path((foundation/'latest-staging').read_text().strip())
manifest=json.loads((stage/'staging-manifest.json').read_text())
assert manifest['frontend_autostart'] and not manifest['firmware_boot_tested']
assert manifest['overlay']['init_services']==compiled
assert not (stage/'rootfs/opt/port-probes/service-child').exists()
out=repo/'dist/phase4/init-services-native'
out.mkdir()  # New immutable checkpoint; preserve earlier snapshots.
for name in ['build-manifest.json','lifecycle-approved.json','ui-approved.json','ui-first-approved.json']:
    shutil.copy2(f/name,out/name)
shutil.copytree(f/'bin',out/'bin')
shutil.copytree(foundation/'audit',out/'audit')
shutil.copy2(stage/'staging-manifest.json',out/'image-manifest.json')
shutil.copy2(foundation/'overlay-manifest.json',out/'overlay-manifest.json')
shutil.copy2(work/'graphics-config/output/.config',out/'buildroot.config')
shutil.copy2(repo/'port/packaging/pending-licenses.json',out/'pending-licenses.json')
sessions=[]
for p in sorted(f.glob('init-*.*')):
    if not p.is_dir():continue
    evidence=p/'evidence'
    assert (evidence/'health-after.json').exists(),p
    health=json.loads((evidence/'health-after.json').read_text())
    assert health['taint']=='0' and health['backlight_brightness']==health['backlight_expected']
    assert (evidence/'mixer-before.state').read_bytes()==(evidence/'mixer-after.state').read_bytes()
    dest=out/'sessions'/p.name
    shutil.copytree(evidence,dest)
    shutil.copy2(p/'native-session.log',dest/'native-session.log')
    sessions.append({'session':p.name,'worker_status0':'PHASE4_CORE_WORKER_EXIT_STATUS=0' in (p/'native-session.log').read_text(),
                     'final_visual':p.name==approved['session'],'final_lifecycle':p.name==lifecycle['session']})
with tarfile.open(out/'port-source.tar.gz','w:gz') as archive:
    for p in sorted((repo/'port').rglob('*')):
        if p.is_file() and '__pycache__' not in str(p) and p.suffix!='.pyc':
            archive.add(p,arcname=str(p.relative_to(repo)),recursive=False)
record={'scope':'native lifecycle adapters and supervised UI; not a firmware boot',
        'sessions':sessions,'native_services_tested':True,'user_visual_confirmed':True,
        'candidate_kernel_booted':False,'coldplug_real_boot_tested':False,
        'final_image_native_tested':False,'frontend_autostart_configured':True,
        'private_runtime_included':False,'redistribution_approved':False,'original_help_sound_approved':False}
(out/'native-results.json').write_text(json.dumps(record,indent=2)+'\n')
(out/'NOT-A-FIRMWARE.txt').write_text(
    'Private lifecycle proof and original code; no rootfs image, Mali ELF, vendor ZIP or runtime tar.\n'
    'bin/service-child is a test fixture, absent from the firmware image.\n'
    'Native tests used installed BSP and private namespaces; cold boot/candidate kernel remain untested.\n'
    'Autostart is configured only in the host candidate. No Debian startup was modified.\n'
    'Helpers/source SPDX MIT; native muOS component licenses remain in referenced checkpoints.\n')
with (out/'SHA256SUMS').open('w') as sums:
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.name!='SHA256SUMS':
            with p.open('rb') as stream:sums.write(f'{hashlib.file_digest(stream,"sha256").hexdigest()}  {p.relative_to(out)}\n')
print('Lifecycle proof frozen:',out)
