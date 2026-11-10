#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C48 measurements and GB preparation, never ELF/ROM/private data."""
from pathlib import Path
import json, re, shutil, tempfile
from phase4_candidate import sha, sums
repo=Path(__file__).resolve().parents[2]
work=repo/'build/phase4';area=work/'nes-profile'
out=repo/'dist/phase4/nes-performance-gb-preparation'
assert not out.exists()
for proof in ['nes-core-content','nes-core-performance-observation']:
    root=repo/'dist/phase4'/proof
    for n,h in sums(root/'SHA256SUMS').items():assert sha(root/n)==h
names=['profile.yf08v2yo','profile.n6v405bs','profile.9_nz67mi','profile.6gk6ijxb','profile.3gmb7osf']
stage=Path(tempfile.mkdtemp(prefix='public.',dir=area))
summary=[]
for name in names:
    source=area/name;r=json.loads((source/'analysis.json').read_text())
    analysis=json.loads((source/'performance-analysis.json').read_text())
    assert r['passed'] and r['cleanup_passed'] and r['RAM_removed'] and r['boot_sequence']==68
    assert sha(source/'analysis.json')==analysis['session_analysis_sha256']
    assert sha(source/'collected/performance.csv')==analysis['performance_csv_sha256']
    assert sha(source/'collected/game.log')==analysis['game_log_sha256']
    target=stage/name;target.mkdir()
    for f in ['analysis.json','performance-analysis.json']:
        shutil.copyfile(source/f,target/f)
    log=(source/'collected/game.log').read_text()
    (target/'markers.txt').write_text('\n'.join(s for s in log.splitlines() if re.search(
        r'^C44_|^C48_CALLBACK |Audio device opened|Audio ring underran|GL swap interval',s))+'\n')
    summary.append({'stage':name,'frames':analysis['frames'],
                    'approximate_frames_per_second':analysis['approximate_frames_per_second'],
                    'audio_underruns':int(analysis['metrics']['audio_underruns'])})
for label,source in [
    ('callback-host',area/'host.8edb4imb'),('pacing-host',area/'pacing-host.5v5cxz55'),
    ('optimized-core',area/'core.uu8rr3el'),('callback-check',area/'callback-check.55vps9yq'),
    ('dispatch-check',Path((area/'latest-dispatch-checks').read_text().strip())),
    ('gb-preparation',Path((work/'gb-core/latest').read_text().strip()))]:
    r=json.loads((source/'analysis.json').read_text());assert r['passed']
    for n,h in r['source_sha256'].items():assert sha(repo/n)==h
    target=stage/label;target.mkdir();shutil.copyfile(source/'analysis.json',target/'analysis.json')
    for f in ['build.sh','check.sh','optimization.mk']:
        if (source/f).is_file():shutil.copyfile(source/f,target/f)
    if label=='gb-preparation':assert not r['ROM_loaded'] and not r['ROM_copied']
# Exact current coordinator/capsule source was used for the last native profile.
last=json.loads((area/names[-1]/'analysis.json').read_text())
for n,h in last['source_sha256'].items():assert sha(repo/n)==h
files=[repo/'docs/archive/phase4/phase4-nes-performance.md',Path(__file__),
       *repo.glob('port/scripts/*phase4*profile*.py'),
       repo/'port/scripts/build-phase4-pacing-host.py',repo/'port/scripts/build-phase4-nes-optimized.py',
       repo/'port/scripts/build-phase4-gb-core.py',
       repo/'port/diagnostics/phase4-core-callback-profile.h',
       repo/'port/diagnostics/phase4-callback-profile-check.c',repo/'port/diagnostics/phase4-gb-identity-check.c',
       repo/'port/patches/0013-muxretro-callback-profile.patch',
       repo/'port/patches/0014-muxretro-diagnostic-software-pacing.patch',
       *repo.glob('port/device/rk-r35s-p0/nes-profile/*.sh')]
for p in sorted(set(files)):
    target=stage/'source'/p.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
report={'experiment':'C48_PROFILE_AND_GB_PREPARATION','native_profiles':summary,
        'performance_qualified':False,'candidates_installed':False,'physical_observation_performed':False,
        'GB_QEMU_metadata_loader_only':True,'GB_ROM_loaded':False,'GB_ROM_copied':False,
        'C47_proofs_preserved':True,'original32_preserved':True,'SDK_baseline_preserved':True}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
assert not any(p.suffix in {'.so','.gb','.nes','.img'} for p in stage.rglob('*'))
(stage/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(stage))+'\n' for p in sorted(stage.rglob('*')) if p.is_file()))
shutil.move(stage,out)
for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h
print('C48 proof frozen and checksummed:',out)
