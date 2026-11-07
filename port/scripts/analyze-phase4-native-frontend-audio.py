#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C06 public logs and physical UI/audio confirmation; never read seed material."""
from pathlib import Path
import hashlib,json,re,subprocess,sys

b=Path(sys.argv[1]).resolve();repo=Path(__file__).resolve().parents[2]
u=json.loads((b/'user-confirmation.json').read_text())
for name in ['menu_legible_oriented','info_config_help_navigation_passed','navigation_confirmation_help_audible','diagnostic_returned']:
    assert u[name],name
d=json.loads((b/'log-collection.json').read_text());assert d['experiment']=='MUOS-R35S-FRONTEND-AUDIO-P4-C06'
p=subprocess.run([sys.executable,str(repo/'port/scripts/analyze-phase4-entropy-boot.py'),str(b),'persisted'],capture_output=True,text=True)
(b/'entropy-analysis.stderr').write_text(p.stderr);assert p.returncode==0,p.stderr
(b/'analysis.json').replace(b/'entropy-analysis.json')
r=d['files']['REPORT.TXT']['text']
frontend=r.split('FRONTEND\n',1)[1].split('AUDIO START\n',1)[0]
assert 'C06_EFFECTS_CONTROL_TONE=1' not in frontend, 'Use the controlled comparison analyzer for synthetic effects'
native_effects='C06_NATIVE_NAV_CONFIRM=1' in frontend
adapted_navigation='C06_NAV_WAVE_ADJUSTED=1' in frontend
if native_effects or adapted_navigation:
    for text in ['C06_REFERENCE=reference-48 RATE=48000 STATUS=0','C06_REFERENCE=reference-44 RATE=44100 STATUS=0']:assert text in frontend
for text in ['UI_WINDOW_STARTED','UI_WINDOW_ENDED','C06_UI_STOPPED=1','STOP reason=stop signal=15','FIRST_PAINT','SDL_AUDIODRIVER=pipewire','C06_HELP_CONTROL_WAV=1','C06_AUDIO_GRACE_SECONDS=3','C06_BOOT_VOLUME_POLICY=3','C06_CONFIG_VOLUME=100']:
    assert text in frontend,text
assert 'CHILD hotkey ' not in frontend and not re.search(r'^EXIT \d+ status=',frontend,re.M)
identity=re.search(r'UI_ID manager=(\d+) frontend=(\d+) parent=(\d+)',frontend);assert identity and identity[1]==identity[3]
modules=list(dict.fromkeys(re.findall(r'^UI_MODULE=(\S+)$',frontend,re.M)))
assert {'muxlaunch','muxinfo','muxconfig'}<=set(modules),modules
before=frontend.split('DRM_BEFORE\n',1)[1].splitlines()[0]
after=frontend.split('DRM_AFTER\n',1)[1].splitlines()[0]
assert before==after and 'size=640x480' in before
audio=r.split('AUDIO START\n',1)[1].split('MAPPING\n',1)[0]
pcm=[]
for name in ['ui-during.txt','ui-before-stop.txt']:
    section=audio.split('FILE='+name+'\n',1)[1].split('FILE=',1)[0].split('ACTIVE AUDIO GRAPH\n',1)[0]
    fmt=re.search(r'^format: (S16_LE|S32_LE)$',section,re.M);assert fmt
    rate=re.search(r'^rate: (44100|48000) ',section,re.M);assert rate
    assert re.search(r'^channels: 2$',section,re.M)
    assert re.search(r'^\s*: values=157,157$',section,re.M)
    assert re.search(r'^\s*: values=3$',section,re.M)
    assert re.search(r'^Volume: 1\.0+$',section,re.M)
    pcm.append({'snapshot':name,'format':fmt[1],'rate':int(rate[1]),'channels':2})
graph=json.loads(audio.split('ACTIVE AUDIO GRAPH\n',1)[1].split('CORE FAILURE GRAPH\n',1)[0].strip())
card=[o for o in graph if o.get('info',{}).get('props',{}).get('device.name')=='alsa_card.platform-rk817-sound']
assert len(card)==1 and card[0]['info']['props']['api.alsa.use-acp'] is False
assert any(o.get('info',{}).get('props',{}).get('node.name')=='alsa_output.platform-rk817-sound.playback.0.0' for o in graph)
stop=r.split('AUDIO STOP\n',1)[1].split('FINAL STATUS\n',1)[0]
assert 'C06_AUDIO_CLEANUP_OK=1' in stop
alsa_before=stop.split('ALSA BEFORE CORE\n',1)[1].split('ALSA RESTORED\n',1)[0].strip()
alsa_restored=stop.split('ALSA RESTORED\n',1)[1].split('AUDIO FALLBACK STOP\n',1)[0].strip()
assert alsa_before==alsa_restored and alsa_before
restore=stop.split('PERSISTENT CONFIG RESTORE\n',1)[1].split('CACHE RESTORED\n',1)[0].strip().splitlines()
assert len(restore)==(13 if native_effects or adapted_navigation else 10) and all(x.endswith(': OK') for x in restore),restore
assert 'C06_RESTORED_CACHE_PATH=SPK\n' in stop and 'C06_RESTORED_CACHE_VOLUME=35\n' in stop
assert 'C06_RESTORED_CACHE_BOOT_VOLUME=2\n' in stop
assert 'ROOT_RO\n1\n' in r and 'C06_LOGGER_STOPPED=1' in r
mounts=r.split('FINAL MOUNTS\n',1)[1]
targets={'/etc/default/muos-ui','/etc/default/muos-core','/opt/muos/device/control/asound.state','/opt/muos/config','/opt/muos/device/config',*[f'/opt/muos/share/theme/MustardOS/sound/{name}.wav' for name in ['info_open','info_close']]}
assert not any(len(x.split())>=2 and x.split()[1] in targets for x in mounts.splitlines())
assert not re.search(r'Could not restore CRTC|segmentation fault|SIGSEGV|first_paint_timeout|input_or_core_lost',frontend,re.I)
result={'scope':'C06 one native supervised frontend/audio cold boot on own kernel; no hotkeys',
 'passed':True,'fresh_first_paint_parent_service_and_physical_navigation_verified':True,
 'physical_navigation_confirmation_control_help_audio_confirmed':True,'observed_modules':modules,
 'audio_backend':'SDL/PipeWire','audio_snapshots':pcm,'codec_gain':157,'playback_path':'SPK_HP','software_volume':'unity',
 'ui_window_target_seconds':90,'audio_grace_seconds':3,'grace_is_not_an_instrumented_drain_proof':True,
 'last_confirmation_complete_user_confirmed':u.get('last_confirmation_complete',False),
 'controlled_stop_drm_and_alsa_precore_restore_passed':True,'original_config_profile_and_help_wave_hashes_preserved':True,
 'original_cache_path_SPK_volume35_restored':True,'temporary_binds_removed':True,
 'root_ro_entropy_input_logger_stop_fsck_stock_health_passed':True,
 'original_help_audio_headphones_hotkeys_power_network_content_long_stability_tested':False,
 'original_theme_navigation_tested':not adapted_navigation,'original_theme_confirmation_back_tested':True,
 'navigation_linear_peak_limited_adaptation_tested':adapted_navigation,'diagnostic_help_uses_original_confirm_wave':True,
 'rate_reference_activity_preceded_navigation':native_effects or adapted_navigation,'final_loudness_calibrated':False,
 'seed_material_collected':False,'collection_sha256':hashlib.sha256((b/'log-collection.json').read_bytes()).hexdigest(),
 'analyzer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(b/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
