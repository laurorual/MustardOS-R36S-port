#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C50 native-exit proof, excluding private content and binaries."""
from pathlib import Path
import json,re,shutil,tempfile
from phase4_candidate import sha,sums
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'gb-exit'
out=repo/'dist/phase4/gameboy-hotkey-exit';assert not out.exists()
proof=repo/'dist/phase4/gameboy-private-content'
for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h
public=Path(tempfile.mkdtemp(prefix='public.',dir=area))
def sanitize(v):
    if isinstance(v,dict):return {k:('private' if k=='ROM_sha256' else sanitize(x)) for k,x in v.items()}
    if isinstance(v,list):return [sanitize(x) for x in v]
    return v
stages={name:Path((area/('latest-'+key)).read_text().strip()) for name,key in [
    ('host','host'),('checks','checks'),('dispatch-checks','dispatch-checks'),('deadline','deadline'),('observe','observe')]}
for label,source in stages.items():
    r=json.loads((source/'analysis.json').read_text());assert r['passed']
    for n,h in r['source_sha256'].items():assert sha(repo/n)==h
    target=public/label;target.mkdir()
    (target/'analysis.json').write_text(json.dumps(sanitize(r),indent=2)+'\n')
    for name in ['exit-analysis.json','physical-observation.json']:
        if (source/name).is_file():
            (target/name).write_text(json.dumps(sanitize(json.loads((source/name).read_text())),indent=2,ensure_ascii=False)+'\n')
    if label in {'deadline','observe'}:
        a=json.loads((source/'exit-analysis.json').read_text())
        assert r['cleanup_passed'] and r['RAM_removed'] and r['boot_sequence']==68
        assert a['reason']==('hotkey' if label=='observe' else 'deadline') and a['technical_launcher_return']
        assert a['audio_underruns']==0 and a['audio_missing_frames']==0
        assert sha(source/'analysis.json')==a['session_analysis_sha256']
        assert sha(source/'collected/game.log')==a['game_log_sha256']
        assert sha(source/'collected/performance.csv')==a['performance_csv_sha256']
        lines=[]
        for name in ['game.log','core.log','return.log']:
            lines.extend(s for s in (source/'collected'/name).read_text().splitlines() if re.match(r'^(C50_|C44_|C46_|C45_|RETRO_RUNNER_EXIT=)',s))
        (target/'markers.txt').write_text('\n'.join(lines)+'\n')
    if label=='checks':
        text=(source/'check.stdout').read_text()
        (target/'markers.txt').write_text('\n'.join(s for s in text.splitlines() if re.match(r'^C(41|44|47|50)_',s))+'\n')
physical=json.loads((stages['observe']/'physical-observation.json').read_text());assert physical['qualified']
for source in [*repo.glob('port/scripts/*phase4*gb-exit*.py'),*repo.glob('port/device/rk-r35s-p0/gb-exit/*.sh'),
               repo/'port/diagnostics/phase4-diagnostic-exit.h',repo/'port/diagnostics/phase4-hotkey-exit-check.c',
               repo/'port/patches/0015-muxretro-diagnostic-hotkey-exit.patch',repo/'docs/archive/phase4/phase4-gb-hotkey-exit.md']:
    target=public/'source'/source.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
report={'experiment':'C50_NATIVE_HOTKEY_EXIT','native_deadline_fallback_passed':True,
        'native_Fn_Start_and_physical_return_qualified':True,'cleanup_passed':True,
        'private_ROM_included':False,'images_PCM_states_binaries_included':False,
        'core_ROM_C49_proof_preserved':True,'installed_files_modified':False,'rebooted':False,
        'persistent_saves_enabled':False,'long_run_and_new_boot_qualified':False}
(public/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
assert not any(p.suffix.lower() in {'.gb','.gbc','.so','.img','.png','.wav','.sav','.srm'} for p in public.rglob('*'))
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out)
for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h
print('C50 proof frozen and verified:',out)
