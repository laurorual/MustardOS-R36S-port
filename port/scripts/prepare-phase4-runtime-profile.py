#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C10: deterministic reviewed profile payload from pinned, read-only resources."""
from pathlib import Path
import array,hashlib,io,json,math,shutil,struct,subprocess,sys,tempfile,wave
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'runtime-profile';area.mkdir(exist_ok=True)
profile_path=repo/'port/device/rk-r35s-p0/runtime-profile.json';profile=json.loads(profile_path.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert profile['schema']==1 and profile['board']=='rk-r35s-p0' and profile['model']=='R36S-V12 2023-08-18 Panel 0'
assert profile['audio']=={'route':'SPK_HP','codec_gain':215,'pipewire_quantum':1024,'software_volume':100,'boot_policy':3,'overdrive':0}
calibration_path=repo/'port/device/rk-r35s-p0/speaker-calibration.json';calibration=json.loads(calibration_path.read_text())
assert sha(calibration_path)==profile['speaker_calibration_sha256'] and calibration['codec_gain']==215
assert calibration['maximum_clean_and_adequate_user_confirmed'] and calibration['software_max']==100
assert profile['display']=={'brightness':80,'maximum':160,'increment':5} and profile['volume_increment']==5
assert profile['device']['audio/path']==profile['audio']['route'] and profile['device']['screen/bright']=='160'
for key,value in [('settings/general/volume','100'),('settings/general/brightness','80'),('settings/advanced/volume','3'),('settings/advanced/incvolume','5'),('settings/advanced/incbright','5'),('settings/advanced/overdrive','0')]:assert profile['global'][key]==value
proof=repo/'dist/phase4/network-controls-session';checks={n:h for h,n in (line.split('  ',1) for line in (proof/'SHA256SUMS').read_text().splitlines())}
for name in ['analysis.json','native/helpers.txt','native/controls-events.txt']:
 assert sha(proof/name)==checks[name]
assert json.loads((proof/'analysis.json').read_text())['passed']
git=['git','-C',str(repo/'refs/muos/internal'),'show'];revision=profile['upstream_internal_revision']
def resource(name):return subprocess.check_output(git+[revision+':'+name])
nav=resource('share/theme/MustardOS/sound/navigate.wav');confirm=resource('share/theme/MustardOS/sound/confirm.wav');license_data=resource('LICENSE')
assert hashlib.sha256(nav).hexdigest()==profile['sounds']['original_navigation_sha256'] and hashlib.sha256(confirm).hexdigest()==profile['sounds']['confirmation_sha256']
assert b'Version 3, 29 June 2007' in license_data
assert sys.byteorder=='little'
def pcm(data):
 with wave.open(io.BytesIO(data),'rb') as w:
  assert w.getparams()[:3]==(2,2,44100)
  return array.array('h',w.readframes(w.getnframes()))
x=pcm(nav);y=pcm(confirm);gain=min(math.sqrt(sum(v*v for v in y)/sum(v*v for v in x)),30000/max(map(abs,x)))
adjusted=array.array('h',[round(v*gain) for v in x]);assert max(map(abs,adjusted))==30000
offset=12;chunks=[]
while offset+8<=len(nav):
 size=struct.unpack_from('<I',nav,offset+4)[0];assert offset+8+size<=len(nav)
 if nav[offset:offset+4]==b'data':chunks.append((offset+8,size))
 offset+=8+size+(size&1)
assert len(chunks)==1;start,size=chunks[0];assert size==len(adjusted)*2
normalized=nav[:start]+adjusted.tobytes()+nav[start+size:]
assert hashlib.sha256(normalized).hexdigest()==profile['sounds']['adjusted_navigation_sha256']
stage=Path(tempfile.mkdtemp(prefix='profile.',dir=area));source=stage/'source';payload=source/'payload';overlay=payload/'overlay';overlay.mkdir(parents=True)
(profile_copy:=payload/'profile.json').write_bytes(profile_path.read_bytes())
shutil.copyfile(calibration_path,payload/'speaker-calibration.json')
files={}
def put(name,data,mode=0o644):
 p=overlay/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data if isinstance(data,bytes) else data.encode());p.chmod(mode);files[name]={'sha256':sha(p),'mode':mode}
for ns,prefix in [('device','opt/muos/device/config/'),('global','opt/muos/config/'),('system','opt/muos/config/system/')]:
 for name,value in profile[ns].items():put(prefix+name,value+'\n')
put('etc/default/muos-core','audio=1\ninput=1\naudio_quantum=1024\n');put('etc/default/muos-ui','enabled=0\nhotkeys=1\n')
put('opt/muos/device/control/asound.state',"""# SPDX-License-Identifier: MIT
# Observed Panel0 bring-up route/gain; acoustic maximum is not calibrated.
state.rockchiprk817co {
  control.1 {
    iface MIXER
    name 'Playback Path'
    value SPK_HP
  }
  control.3 {
    iface MIXER
    name 'Playback Volume'
    value.0 215
    value.1 215
  }
}
""")
put('opt/muos/share/hotkey/r35s-bringup.json',(repo/'port/device/rk-r35s-p0/session-hotkeys.json').read_bytes())
for name,data in [('navigate',normalized),('info_open',confirm),('info_close',confirm)]:put('opt/muos/share/theme/MustardOS/sound/'+name+'.wav',data)
shutil.copyfile(repo/'port/LICENSE',source/'LICENSE.port');(source/'LICENSE.upstream').write_bytes(license_data)
original=payload/'source-resources';original.mkdir();(original/'navigate.wav').write_bytes(nav);(original/'confirm.wav').write_bytes(confirm)
notice={'revision':revision,'license':'GPL-3.0, upstream root LICENSE; no subtree exception identified in prior asset audit','navigation_gain':gain,'navigation_gain_db':20*math.log10(gain),'navigation_peak':30000,'clipped_samples':0,'riff_non_audio_bytes_retained':True,'help_substitution':'confirm copied into info_open/info_close, as reviewed; original help remains a known limitation','original_sha256':{'navigate.wav':hashlib.sha256(nav).hexdigest(),'confirm.wav':hashlib.sha256(confirm).hexdigest()}}
(payload/'resource-provenance.json').write_text(json.dumps(notice,indent=2)+'\n')
meta={'schema':1,'profile_sha256':sha(profile_copy),'ui_autostart':False,'files':files,'upstream_resource_revision':revision,'approved_c09_analysis_sha256':checks['analysis.json'],'source_code':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/scripts/apply-phase4-runtime-profile.py',repo/'port/device/rk-r35s-p0/session-hotkeys.json']}}
(payload/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
(stage/'manifest.json').write_text(json.dumps({'profile':profile['name'],'overlay_files':len(files),'payload_manifest_sha256':sha(payload/'manifest.json'),'preparation_passed':True,'native_recipe_profile_tested':False,'private_data_included':False},indent=2)+'\n')
link=area/'source';pending=area/'source.pending';pending.unlink(missing_ok=True);pending.symlink_to(source.relative_to(area),target_is_directory=True);pending.replace(link)
(area/'latest-profile').write_text(str(stage)+'\n');print('C10 reviewed profile generated:',stage)
