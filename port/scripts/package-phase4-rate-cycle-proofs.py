#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze negative C32 rate renegotiation and complete restoration evidence."""
from pathlib import Path
import json,shutil,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
stage=work/'audio-buffers/session.3rmqqwti'
report=json.loads((stage/'rate-cycle-analysis.json').read_text())
assert report['diagnostic_completed'] and not report['audio_recovered']
assert report['force_rate_zero_restored']
assert report['rates']['restored']['frames_per_second'] is None
for name in ['before','forced48000']:assert abs(report['rates'][name]['ratio_to_declared']-.5)<.01
assert json.loads((stage/'analysis.json').read_text())['passed']
assert (stage/'final-health.exit').read_text().strip()=='0'
assert sha(stage/'rate-cycle-native.sh')==json.loads((stage/'rate-cycle-intent.json').read_text())['source_sha256']
assert sha(stage/'runner-source.py')==json.loads((stage/'session.json').read_text())['source_sha256']
destination=repo/'dist/phase4/audio-rate-cycle';assert not destination.exists()
public=Path(tempfile.mkdtemp(prefix='rate-cycle-proof.',dir=work/'audio-clock-audit'))
def copy(path,rel):
    assert path.is_file() and not path.is_symlink() and path.stat().st_size<262144,path
    target=public/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
for name in ['session.json','generation.json','analysis.json','rate-cycle-intent.json','rate-cycle-result.json',
             'rate-cycle-analysis.json','rate-cycle-native.sh','runner-source.py']:
    copy(stage/name,name)
for label in ['rate-cycle-prepare','rate-cycle','after-rate-cycle','stop','health','final-health']:
    for ext in ['sh','stdout','stderr','exit']:copy(stage/(label+'.'+ext),label+'.'+ext)
for name in ['result','report.txt','preferences-loaded.txt','preferences-saved.txt','mixer-before.txt','mixer-after.txt',
             'brightness-before.txt','brightness-after.txt','drm-before.txt','drm-after.txt','volume-before.sha256',
             'volume-after.sha256','wireplumber-before.sha256','wireplumber-after.sha256']:
    copy(stage/'collected'/name,'collected/'+name)
for name in ['port/device/rk-r35s-p0/audio-buffers/rate-cycle.sh',
             'port/scripts/phase4-audio-buffers.py','port/scripts/analyze-phase4-rate-cycle.py',
             'port/scripts/package-phase4-rate-cycle-proofs.py']:
    copy(repo/name,'source/'+name)
(public/'analysis.json').write_text(json.dumps({'passed':True,'scope':'negative diagnostic and restoration only',
    'boot_sequence':57,'audio_recovered':False,'audio_qualified':False,'rates':report['rates'],
    'restored_force_rate':0,'root_ro':True,'saved_pair':[55,70],'microphone_opened':False,
    'native_configuration_changed_by_C32':False,'new_reboot_or_image':False,
    'session_players_and_RAM_cleaned':True},indent=2)+'\n')
(public/'NOTICE.txt').write_text('C32 failed to recover audio: roughly half nominal rate persists; restored samples crossed PCM restarts and are not a valid rate measurement. Metadata force-rate0 restored, session stopped/restored, rootRO and preference55/70 verified. No rootfs/blob/raw audio, microphone capture, private backup/seed/key/network credential.\n')
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,destination);print('C32 negative diagnostic proof frozen:',destination)
