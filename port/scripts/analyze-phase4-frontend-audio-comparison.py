#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C06 controlled-rate/effect evidence; never approve untested original assets."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
b=Path(sys.argv[1]).resolve();repo=Path(__file__).resolve().parents[2]
u=json.loads((b/'user-confirmation.json').read_text())
for k in ['baseline_48_three_beeps_heard','ui_44_three_beeps_heard','controlled_dpad_confirm_back_help_beeps_heard','menu_appeared','diagnostic_returned']:assert u[k],k
d=json.loads((b/'log-collection.json').read_text());assert d['experiment']=='MUOS-R35S-FRONTEND-AUDIO-P4-C06'
p=subprocess.run([sys.executable,str(repo/'port/scripts/analyze-phase4-entropy-boot.py'),str(b),'persisted'],capture_output=True,text=True)
(b/'entropy-analysis.stderr').write_text(p.stderr);assert p.returncode==0,p.stderr
(b/'analysis.json').replace(b/'entropy-analysis.json')
r=d['files']['REPORT.TXT']['text'];f=r.split('FRONTEND\n',1)[1].split('AUDIO START\n',1)[0]
for text in ['C06_REFERENCE=reference-48 RATE=48000 STATUS=0','C06_REFERENCE=reference-44 RATE=44100 STATUS=0','C06_EFFECTS_CONTROL_TONE=1','C06_UI_STOPPED=1','UI_WINDOW_ENDED','STOP reason=stop signal=15','SDL_AUDIODRIVER=pipewire']:assert text in f,text
ids=re.search(r'UI_ID manager=(\d+) frontend=(\d+) parent=(\d+)',f);assert ids and ids[1]==ids[3]
assert 'CHILD hotkey ' not in f and not re.search(r'^EXIT \d+ status=',f,re.M)
modules=list(dict.fromkeys(re.findall(r'^UI_MODULE=(\S+)$',f,re.M)));assert {'muxlaunch','muxinfo','muxconfig'}<=set(modules)
assert f.split('DRM_BEFORE\n')[1].splitlines()[0]==f.split('DRM_AFTER\n')[1].splitlines()[0]
a=r.split('AUDIO START\n')[1].split('MAPPING\n')[0]
for name,rate in [('ui-during',44100),('ui-before-stop',44100),('reference-48-during',48000),('reference-44-during',44100)]:
 s=a.split('FILE='+name+'.txt\n')[1].split('FILE=')[0].split('ACTIVE AUDIO GRAPH\n')[0]
 assert re.search(r'^format: S32_LE$',s,re.M) and re.search(r'^rate: '+str(rate)+' ',s,re.M)
 for pattern in [r'^channels: 2$',r'^\s*: values=157,157$',r'^\s*: values=3$',r'^Volume: 1\.0+$']:assert re.search(pattern,s,re.M),(name,pattern)
stop=r.split('AUDIO STOP\n')[1].split('FINAL STATUS\n')[0];assert 'C06_AUDIO_CLEANUP_OK=1' in stop
assert stop.split('ALSA BEFORE CORE\n')[1].split('ALSA RESTORED\n')[0].strip()==stop.split('ALSA RESTORED\n')[1].split('AUDIO FALLBACK STOP\n')[0].strip()
restore=stop.split('PERSISTENT CONFIG RESTORE\n')[1].split('CACHE RESTORED\n')[0].strip().splitlines();assert len(restore)==13 and all(x.endswith(': OK') for x in restore)
assert 'C06_LOGGER_STOPPED=1' in r and 'ROOT_RO\n1\n' in r
targets=['/etc/default/muos-ui','/etc/default/muos-core','/opt/muos/config','/opt/muos/device/config','/opt/muos/device/control/asound.state']+[f'/opt/muos/share/theme/MustardOS/sound/{n}.wav' for n in ['confirm','back','navigate','info_open','info_close']]
assert not any(len(x.split())>1 and x.split()[1] in targets for x in r.split('FINAL MOUNTS\n')[1].splitlines())
result={'scope':'C06 controlled 48k/44.1k references and synthetic UI effects only','controlled_comparison_passed':True,'original_theme_frontend_audio_approved':False,'physical_both_rates_and_controlled_effects_heard':True,'volume_still_low_user_reported':True,'gain':157,'path':'SPK_HP','software':'unity','observed_modules':modules,'both_rate_and_event_checks_passed':True,'original_13_hashes_alsa_binds_logger_root_ro_entropy_input_fsck_stock_health_passed':True,'resource_change_and_prior_audio_activity_not_isolated_yet':True,'seed_material_collected':False,'collection_sha256':hashlib.sha256((b/'log-collection.json').read_bytes()).hexdigest(),'analyzer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(b/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
