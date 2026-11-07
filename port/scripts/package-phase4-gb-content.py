#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C49 allowlisted proof: no commercial ROM, frames, PCM or save state."""
from pathlib import Path
import json, re, shutil, tempfile
from phase4_candidate import sha, sums
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'gb-core'
out=repo/'dist/phase4/gameboy-private-content';assert not out.exists()
proof=repo/'dist/phase4/nes-performance-gb-preparation'
for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h
build=Path((area/'latest').read_text().strip());br=json.loads((build/'analysis.json').read_text())
api=Path((area/'latest-api').read_text().strip());ar=json.loads((api/'analysis.json').read_text())
assert br['passed'] and ar['passed'] and ar['build_stage']==str(build)
assert sha(Path(br['source_stage'])/'gambatte_libretro.so')==br['core_sha256']
rom=repo/'port/roms/gb/Super Mario Land (World) (Rev 1).gb';assert sha(rom)==ar['ROM_sha256']
stage=Path(tempfile.mkdtemp(prefix='public.',dir=area))
def public_report(value):
    if isinstance(value,dict):return {k:('private' if k=='ROM_sha256' else public_report(v)) for k,v in value.items()}
    if isinstance(value,list):return [public_report(v) for v in value]
    return value
def copy_report(source,target):
    value=json.loads(source.read_text());target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(public_report(value),indent=2,ensure_ascii=False)+'\n')
stages={'API':api,'launcher-checks':Path((area/'latest-checks').read_text().strip()),
        'session-checks':Path((area/'latest-dispatch-checks').read_text().strip()),
        'native-API':Path((area/'latest-cycle').read_text().strip()),
        'profile':Path((area/'latest-profile').read_text().strip()),
        'observe':Path((area/'latest-observe').read_text().strip())}
for label,source in stages.items():
    r=json.loads((source/'analysis.json').read_text());assert r['passed']
    for n,h in r['source_sha256'].items():
        # The native API ran before the host-side dispatch-check gate was added.
        # Its capsule/worker/assets were identical; its original controller hash
        # remains in the report, not falsely replaced by the current one.
        if label=='native-API' and n=='port/scripts/run-phase4-gb-content.py':continue
        assert sha(repo/n)==h,(label,n)
    if label in {'native-API','profile','observe'}:
        assert r['cleanup_passed'] and r['RAM_removed'] and r['boot_sequence']==68
        assert r['core_sha256']==br['core_sha256'] and r['ROM_sha256']==ar['ROM_sha256']
    copy_report(source/'analysis.json',stage/label/'analysis.json')
    for name in ['performance-analysis.json','physical-observation.json','PCM-clock.json']:
        if (source/name).exists():copy_report(source/name,stage/label/name)
    if label in {'profile','observe'}:
        analysis=json.loads((source/'performance-analysis.json').read_text())
        assert sha(source/'analysis.json')==analysis['session_analysis_sha256']
        assert sha(source/'collected/game.log')==analysis['game_log_sha256']
        assert sha(source/'collected/performance.csv')==analysis['performance_csv_sha256']
        assert int(analysis['metrics']['audio_underruns'])==0
        assert analysis['approximate_frames_per_second']>=58.5
    lines=[]
    for p in [source/'check.stdout',source/'collected/gb-api.log',source/'collected/game.log',source/'collected/core.log',source/'collected/return.log']:
        if p.is_file():lines.extend(line for line in p.read_text().splitlines() if re.match(r'^(C49_|C44_|C46_|C45_|RETRO_RUNNER_EXIT=)',line))
    (stage/label/'markers.txt').write_text('\n'.join(lines)+'\n')
observe=stages['observe'];physical=json.loads((observe/'physical-observation.json').read_text())
clock=json.loads((observe/'PCM-clock.json').read_text());assert physical['qualified'] and clock['relative_error']<0.005
for source in [*repo.glob('port/scripts/*phase4*gb*.py'),*repo.glob('port/device/rk-r35s-p0/gb-core/*.sh'),
               repo/'port/diagnostics/phase4-gb-core-check.c',repo/'docs/analysis/phase4-gb-content.md']:
    target=stage/'source'/source.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
copy_report(build/'analysis.json',stage/'core-preparation.json')
report={'experiment':'C49_PRIVATE_GB_CONTENT','functional_native_test_passed':True,
        'short_audio_video_controls_qualified':True,'technical_launcher_return_passed':True,
        'physical_launcher_return_explicit':False,'ROM_included':False,'commercial_frames_PCM_saves_included':False,
        'core_and_host_rebuilt':False,'installation_changed':False,'rebooted':False,
        'long_run_new_boot_and_persistence_qualified':False,'original32_preserved':True}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
assert not any(p.suffix.lower() in {'.gb','.gbc','.nes','.img','.so','.png','.wav','.srm','.sav'} for p in stage.rglob('*'))
(stage/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(stage))+'\n' for p in sorted(stage.rglob('*')) if p.is_file()))
shutil.move(stage,out)
for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h
print('C49 allowlisted proof verified:',out)
