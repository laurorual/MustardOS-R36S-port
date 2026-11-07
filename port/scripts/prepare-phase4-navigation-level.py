#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C06: adjust only the original navigation WAV, with deterministic peak cap."""
from pathlib import Path
import array,hashlib,json,math,shutil,struct,subprocess,sys,tempfile,wave
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';base=work/'linux-diagnostic/frontend-native-effects.xbxgwf0j'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((base/'manifest.json').read_text());assert sha(base/'rootfs.ext4')==m['rootfs_sha256']
stage=Path(tempfile.mkdtemp(prefix='frontend-navigation-level.',dir=work/'linux-diagnostic'));assets=stage/'assets';assets.mkdir();shutil.copyfile(base/'rootfs.ext4',stage/'rootfs.ext4')
resource='share/theme/MustardOS/sound/navigate.wav';source=base/'extracted/opt/muos'/resource
assert sha(source)=='7b2c53f02bed004fe757302b1838d5c0a4511a479643bf80bff0cddc3eb540d7'
git=['git','-C',str(repo/'refs/muos/internal')]
upstream=subprocess.check_output(git+['show','HEAD:'+resource]);assert hashlib.sha256(upstream).hexdigest()==sha(source)
revision=subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip()
license_data=subprocess.check_output(git+['show','HEAD:LICENSE']);assert b'Version 3, 29 June 2007' in license_data
(stage/'LICENSE.original-resource').write_bytes(license_data)
def read(p):
    with wave.open(str(p),'rb') as w:return array.array('h',w.readframes(w.getnframes())),w.getparams()
x,params=read(source);confirmation,_=read(source.with_name('confirm.wav'))
assert (params.nchannels,params.sampwidth,params.framerate,params.nframes)==(2,2,44100,38016)
energy=sum(v*v for v in x);reference_energy=sum(v*v for v in confirmation);peak=max(map(abs,x))
gain=min(math.sqrt(reference_energy/energy),30000/peak)
y=array.array('h',[round(v*gain) for v in x]);assert max(map(abs,y))<=30000
tone_name='usr/share/muos-diagnostic/c06-navigate-normalized.wav';tone=assets/tone_name.replace('/','_')
raw=source.read_bytes();assert raw[:4]==b'RIFF' and raw[8:12]==b'WAVE'
offset=12;data_chunks=[]
while offset+8<=len(raw):
    size=struct.unpack_from('<I',raw,offset+4)[0]
    assert offset+8+size<=len(raw)
    if raw[offset:offset+4]==b'data':data_chunks.append((offset+8,size))
    offset+=8+size+(size&1)
assert len(data_chunks)==1
start,size=data_chunks[0];assert size==len(y)*2
result=raw[:start]+y.tobytes()+raw[start+size:]
assert result[:start]==raw[:start] and result[start+size:]==raw[start+size:]
tone.write_bytes(result)
assert tone.stat().st_size==152142 and sha(tone)=='adac78795e6810ce5d17effa5593e9de87051d3ef36231ba9d530921951bb3ee'
check,after=read(tone);assert check==y and after==params
provenance={'source':'refs/muos/internal/'+resource,'source_revision':revision,'source_sha256':sha(source),'resource_license':'GPL-3.0 as supplied by upstream root LICENSE; no subtree override identified','license_sha256':hashlib.sha256(license_data).hexdigest(),'modification':'constant linear amplitude only; no resampling/trimming/EQ; RIFF ancillary chunks unchanged; peak limited to30000','gain':gain,'gain_db':20*math.log10(gain),'before_peak':peak,'after_peak':max(map(abs,y)),'before_rms':math.sqrt(energy/len(x)),'after_rms':math.sqrt(sum(v*v for v in y)/len(y)),'event_energy_ratio_to_confirmation':sum(v*v for v in y)/reference_energy,'clipped_samples':0,'rate':params.framerate,'channels':params.nchannels,'frames':params.nframes,'sample_width':params.sampwidth,'data_offset':start,'non_audio_bytes_unchanged':True,'sha256':sha(tone),'physical_loudness_calibrated':False}
(stage/'navigation-level.json').write_text(json.dumps(provenance,indent=2)+'\n')
(stage/'NOTICE.navigation.txt').write_text('Original navigation resource: MustardOS/internal, '+resource+', revision '+revision+'. Adaptation for private R35S bring-up: constant linear amplitude with peak cap30000; original duration/rate/channels retained. Source and generated hashes are in navigation-level.json. Upstream GPLv3 LICENSE retained as LICENSE.original-resource.\n')
name='usr/libexec/muos-c06-session';text=(repo/'port/device/rk-r35s-p0/frontend-audio-diagnostic/session.sh').read_text()
for old,new in [('c06_control_effects=1','c06_control_effects=0'),('c06_nav_adjusted=0','c06_nav_adjusted=1')]:assert text.count(old)==1;text=text.replace(old,new)
(assets/name.replace('/','_')).write_text(text)
entries=[];commands=[]
for n in [tone_name,name]:
    p=assets/n.replace('/','_');old=base/'extracted'/n;mode=0o644 if n==tone_name else 0o755
    entries.append({'path':n,'asset':p.name,'sha256':sha(p),'old_sha256':sha(old) if old.is_file() else None,'mode':mode})
    if old.exists():commands.append('rm /'+n)
    commands += [f'write assets/{p.name} /{n}',f'set_inode_field /{n} mode 0{mode|0o100000:o}']
(stage/'debugfs.commands').write_text('\n'.join(commands)+'\n')
subprocess.run([sys.executable,str(repo/'port/scripts/check-phase4-frontend-audio-hooks.py'),str(stage)],check=True)
container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z','-e','STAGE_REL='+str(stage.relative_to(work)),(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c']
audit=r'''
cd /work/$STAGE_REL
debugfs -w -f debugfs.commands rootfs.ext4 > debugfs.log 2>&1
e2fsck -fn rootfs.ext4 > fsck.log 2>&1
mkdir extracted
/work/graphics-config/output/host/bin/fakeroot debugfs -R "rdump / $PWD/extracted" rootfs.ext4 > extract.log 2>&1
root=$PWD/extracted
qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh -n "$root/usr/libexec/muos-c06-session"
'''
with (stage/'audit.log').open('w') as out:subprocess.run(container+[audit],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=100)
assert all(sha(stage/'extracted'/e['path'])==e['sha256'] for e in entries)
assert not (stage/'extracted/var/lib/muos-seedrng').exists()
assert sha(stage/'extracted/opt/muos'/resource)==sha(source)
assert (stage/'extracted/usr/share/licenses/muos-core/LICENSE').read_bytes()==license_data
plan={'experiment':m['experiment'],'diagnostic_revision_update':4,'authorized_secondary_c06_revision':True,'installer_sha256':sha(repo/'port/scripts/install-phase4-service-diagnostic.py'),'entries':entries,'unchanged_required':m['unchanged_required']}
(stage/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
inputs=['port/scripts/prepare-phase4-navigation-level.py','port/device/rk-r35s-p0/frontend-audio-diagnostic/session.sh','port/scripts/check-phase4-frontend-audio-hooks.py','port/scripts/install-phase4-service-diagnostic.py']
record={**plan,'base_manifest_sha256':sha(base/'manifest.json'),'rootfs_sha256':sha(stage/'rootfs.ext4'),'host_audit_passed':True,'seed_material_included':False,'physical_navigation_level_tested':False,'only_navigation_waveform_changed':True,'gain_route_rates_reference_activity_unchanged':True,'navigation_level':provenance,'hook_fixtures':json.loads((stage/'hook-fixtures.json').read_text()),'port_inputs':{n:sha(repo/n) for n in inputs}}
(stage/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');(work/'linux-diagnostic/latest-frontend-navigation-level').write_text(str(stage)+'\n')
print('C06 navigation-only level adjustment audited:',stage)
