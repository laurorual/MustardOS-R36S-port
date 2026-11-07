#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C05 public logs: operational audio separately from subjective loudness."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
b=Path(sys.argv[1]).resolve();r=Path(__file__).resolve().parents[2]
u=json.loads((b/'user-confirmation.json').read_text())
assert u['three_beeps_heard'] and u['diagnostic_returned']
d=json.loads((b/'log-collection.json').read_text());assert d['experiment']=='MUOS-R35S-AUDIO-P4-C05'
subprocess.run([sys.executable,str(r/'port/scripts/analyze-phase4-entropy-boot.py'),str(b),'persisted'],check=True,capture_output=True,text=True)
(b/'analysis.json').replace(b/'entropy-analysis.json')
report=d['files']['REPORT.TXT']['text'];a=report.split('AUDIO START\n',1)[1].split('MAPPING\n',1)[0]
stop=report.split('AUDIO STOP\n',1)[1].split('FINAL STATUS\n',1)[0]
for text in ['C05_PLAY_STATUS=0','C05_SAMPLE_STATUS=0','C05_AUDIO_PROBE_OK=1','node.name = "alsa_output.platform-rk817-sound.playback.0.0"']:
 assert text in a,text
assert 'C05_AUDIO_CLEANUP_OK=1' in stop
volume_before=a.split('FILE=software-before.txt\n',1)[1].split('FILE=',1)[0].strip()
volume_unity=a.split('FILE=software-unity.txt\n',1)[1].split('FILE=',1)[0].strip()
volume_restored=a.split('FILE=software-restored.txt\n',1)[1].split('FILE=',1)[0].strip()
assert volume_before==volume_restored and re.fullmatch(r'Volume: 1\.0+',volume_unity)
during=a.split('FILE=during.txt\n',1)[1].split('FILE=',1)[0]
fmt=re.search(r'^format: (S16_LE|S32_LE)$',during,re.M);assert fmt
rate=re.search(r'^rate: (\d+)',during,re.M);assert rate and int(rate[1]) in [32000,44100,48000]
assert re.search(r'^channels: 2$',during,re.M)
assert 'closed' not in during
gain_match=re.search(r'C05_CODEC_PROBE_GAIN=(95|157)',a)
gain=int(gain_match[1]) if gain_match else 95
assert re.search(r'^\s*: values='+str(gain)+','+str(gain)+r'$',during,re.M)
path_match=re.search(r'C05_PLAYBACK_PATH=(SPK_HP|SPK)\b',a)
playback_path=path_match[1] if path_match else 'SPK'
assert re.search(r'^\s*: values='+('3' if playback_path=='SPK_HP' else '1')+r'$',during,re.M)
if playback_path=='SPK_HP':
 restored_path=a.split('FILE=path-restored.txt\n',1)[1].split('FILE=',1)[0]
 assert re.search(r'^\s*: values=1$',restored_path,re.M)
 assert all(label in during for label in ['CODEC_REGISTERS\n','I2S_REGISTERS\n','I2S_CLOCKS\n'])
if gain==157:
 restored=a.split('FILE=codec-restored.txt\n',1)[1].split('FILE=',1)[0]
 assert re.search(r'^\s*: values=95,95$',restored,re.M)
aplay=a.split('FILE=aplay.txt\n',1)[1].split('FILE=',1)[0]
assert not re.search(r'underrun|xrun|broken pipe|Input/output error',aplay,re.I)
alsa_before=stop.split('ALSA BEFORE CORE\n',1)[1].split('ALSA RESTORED\n',1)[0].strip()
alsa_restored=stop.split('ALSA RESTORED\n',1)[1].split('AUDIO FALLBACK STOP\n',1)[0].strip()
assert alsa_before==alsa_restored and alsa_before
mounts=report.split('FINAL MOUNTS\n',1)[1]
assert not any(line.split()[1] in ['/etc/default/muos-core','/opt/muos/device/control/asound.state'] for line in mounts.splitlines())
assert 'ROOT_RO\n1\n' in report and 'C05_LOGGER_STOPPED=1' in report
assert re.search(r'^ID_PATH=platform-rk817-sound$',a,re.M)
graph_text=a.split('ACTIVE AUDIO GRAPH\n',1)[1].split('CORE FAILURE GRAPH\n',1)[0].strip()
graph=json.loads(graph_text)
card=[o for o in graph if o.get('info',{}).get('props',{}).get('device.name')=='alsa_card.platform-rk817-sound']
assert len(card)==1 and card[0]['info']['props']['api.alsa.use-acp'] is False
assert any(o.get('info',{}).get('props',{}).get('node.name')=='alsa_output.platform-rk817-sound.playback.0.0' for o in graph)
result={'scope':'C05 first native core/PipeWire playback cold boot, own kernel, no frontend/hotkeys','passed':True,'audible_three_beeps_confirmed':True,'comfortable_loudness_confirmed':u.get('comfortable_loudness',False),'clean_audio_confirmed':u.get('clean_audio',False),'pcm_format':fmt[1],'channels':2,'rate':int(rate[1]),'hardware_playback_during':[gain,gain],'diagnostic_codec_restored_to_95':gain==157,'card_native_path_identity_and_acp_false':True,'software_unity_override_and_readback_restore_passed':True,'alsa_precore_controls_restored':True,'audio_config_binds_removed':True,'core_input_entropy_stop_root_ro_fsck_stock_health_passed':True,'frontend_audio_hotkeys_network_power_long_stability_tested':False,'seed_material_collected':False,'collection_sha256':hashlib.sha256((b/'log-collection.json').read_bytes()).hexdigest(),'analyzer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
result.update({'hardware_playback_path_during':playback_path,'diagnostic_route_restored_to_SPK':playback_path=='SPK_HP','codec_i2s_clock_metadata_collected':playback_path=='SPK_HP'})
(b/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
