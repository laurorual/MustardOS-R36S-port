#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C77 freeze sanitized implementation and successful native session receipts."""
from pathlib import Path
import json, re, shutil, tempfile
from phase4_installed_core_session import *
from phase4_candidate import sums

historical()
stage = Path((AREA / 'latest-load').read_text().strip())
checks = Path((AREA / 'latest-checks').read_text().strip())
guard = Path((AREA / 'latest-native-guard').read_text().strip())
reports = {'checks':json.loads((checks/'analysis.json').read_text()),
           'guard':json.loads((guard/'analysis.json').read_text()),
           'load':json.loads((stage/'analysis.json').read_text()),
           'technical':json.loads((stage/'technical-analysis.json').read_text()),
           'physical':json.loads((stage/'physical-observation.json').read_text()),
           'final':json.loads((stage/'final-audit.json').read_text())}
assert all(r['passed'] for r in reports.values())
r = reports['load']; f = reports['final']; physical = reports['physical']
assert r['checks_analysis_sha256'] == sha(checks/'analysis.json')
assert r['installed_core_used'] and not r['core_ELF_transferred'] and r['state_namespace'] == 'gambatte'
assert r['installed_host_used'] and not r['host_ELF_transferred'] and not r['store_ELF_transferred']
assert r['game_uses_installed_provider4'] and r['process_maps_confirmed']
assert r['store_byte_identical_to_C63'] and not r['new_save_requested']
assert r['RAM_removed'] and r['root_ro'] and not r['agent_requested_reboot']
assert reports['technical']['session_analysis_sha256'] == physical['session_analysis_sha256'] == sha(stage/'analysis.json')
for key in ['image_and_navigation_confirmed','sound_clean_and_audible_confirmed',
            'restore_to_saved_position_confirmed','launcher_return_confirmed']:
    assert physical[key] is True
assert not physical['new_save_requested']
for n, h in f['recorded_receipts_sha256'].items(): assert sha(stage/n) == h
assert reports['guard']['observation_sha256'] == r['observation_sha256']
assert reports['guard']['checks_analysis_sha256'] == r['checks_analysis_sha256']
public = Path(tempfile.mkdtemp(prefix='public.',dir=AREA))
sources = {Path(__file__), REPO/'docs/analysis/phase4-installed-core-session.md'}
def clean(value):
    if isinstance(value,dict):
        return {k: ('private' if k in {'ROM_sha256','private_identity','kernel_boot_id'} else clean(v)) for k,v in value.items()}
    if isinstance(value,list): return [clean(v) for v in value]
    return value
for label, report in reports.items():
    dest=public/label;dest.mkdir()
    (dest/'analysis.json').write_text(json.dumps(clean(report),indent=2,ensure_ascii=False)+'\n')
    for n,h in report.get('source_sha256',{}).items():
        assert sha(REPO/n)==h,n
        sources.add(REPO/n)
for ext in ['py','stdout','stderr','exit']:
    shutil.copyfile(checks/('fixtures.'+ext),public/'checks'/('fixtures.'+ext))
for n in ['watch-maps.stdout','native-provider-ABI.stdout','installed-host-check.stdout']:
    shutil.copyfile(stage/n,public/'load'/n)
shutil.copyfile(stage/'collected/state-metadata.txt',public/'load/state-metadata.txt')
shutil.copyfile(guard/'dispatcher-check.stdout',public/'guard/dispatcher-check.stdout')
markers=[]
for name in ['core.log','game.log','return.log','store-seed.log','store-verify.log']:
    markers += [l for l in (stage/'collected'/name).read_text().splitlines()
                if re.match(r'^(C(44|45|46|50|51|53|58|77)_|RETRO_RUNNER_EXIT=)',l)]
(public/'load/markers.txt').write_text('\n'.join(markers)+'\n')
for source in sorted(sources):
    dest=public/'source'/source.relative_to(REPO);dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,dest)
parents={n:sha(proof(n)/'SHA256SUMS') for n in ['installed-provider-session','gambatte-package','gambatte-installed','provider-upgrade-native']}
(public/'analysis.json').write_text(json.dumps({'passed':True,'experiment':'C77_NATIVE_INSTALLED_CORE_CALLER',
    'boot_sequence':r['boot_sequence'],'core_path':CORE,'core_sha256':r['core_sha256'],
    'installed_host_and_provider4_and_core_used':True,'core_ELF_transferred':False,
    'host_ELF_transferred':False,'store_ELF_transferred':False,'state_namespace':'gambatte',
    'on_card_snapshot_renamed_or_modified':False,'checks':reports['checks']['case_count'],
    'physical_image_input_audio_restore_and_return_confirmed':True,
    'root_read_only':True,'RAM_removed':True,'new_save_requested':False,'reboot_requested':False,
    'permanent_frontend_or_general_dispatcher_qualified':False,'long_run_or_power_loss_qualified':False,
    'combined_license_review_pending':True,'redistribute':False,
    'raw_ROM_state_UUID_ELF_or_private_identity_included':False,'parent_proofs_sha256':parents},indent=2)+'\n')
for p in public.rglob('*'):
    assert not p.is_symlink()
    if p.is_file():
        assert p.suffix.lower() not in {'.gb','.so','.img','.ext4','.png','.wav','.state','.srm','.sav','.bundle','.ini','.tar','.gz'}
        data=p.read_bytes();assert not data.startswith(b'\x7fELF')
        assert not any(v.encode() in data for v in [r['private_identity'],r['ROM_sha256'],r['kernel_boot_id']]),p
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
out=REPO/'dist/phase4/installed-core-session';assert not out.exists()
shutil.move(public,out)
for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h
print('C77 sanitized native proof frozen:',out)
