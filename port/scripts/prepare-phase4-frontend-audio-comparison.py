#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C06 rate/effect comparison; bounded original controlled tone, same codec gain."""
from pathlib import Path
import array,hashlib,json,math,shutil,subprocess,sys,tempfile,wave

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';base=work/'linux-diagnostic/frontend-audio-policy.hwhmotll'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((base/'manifest.json').read_text());assert sha(base/'rootfs.ext4')==m['rootfs_sha256']
stage=Path(tempfile.mkdtemp(prefix='frontend-audio-compare.',dir=work/'linux-diagnostic'));assets=stage/'assets';assets.mkdir()
shutil.copyfile(base/'rootfs.ext4',stage/'rootfs.ext4')
original=base/'extracted/usr/share/muos-diagnostic/c05-tone.wav'
assert sha(original)=='959fcac27fe4bb517ea946d3725857c7fa01b61008c1363d6fdda3dfa96c43e8'
with wave.open(str(original),'rb') as w:
    assert (w.getnchannels(),w.getsampwidth(),w.getframerate())==(2,2,48000)
    source=array.array('h',w.readframes(w.getnframes()))[::2]
samples=array.array('h')
for i in range(11025):
    pos=i*48000/44100;index=int(pos);fraction=pos-index
    value=source[index]*(1-fraction)+source[index+1]*fraction
    fade=min(1.0,i/220,(11024-i)/220)
    value=round(value*max(0,fade));samples.extend([value,value])
tone_name='usr/share/muos-diagnostic/c06-control-tone.wav';tone=assets/tone_name.replace('/','_')
with wave.open(str(tone),'wb') as w:w.setparams((2,2,44100,0,'NONE','not compressed'));w.writeframes(samples.tobytes())
peak=max(map(abs,samples));rms=math.sqrt(sum(x*x for x in samples)/len(samples));assert peak<=6553 and rms>4000
tone_metadata={'source_sha256':sha(original),'sha256':sha(tone),'rate':44100,'channels':2,'sample_width':2,'frames':11025,'duration_seconds':0.25,'peak':peak,'rms':rms,'method':'first 250ms of known C05 tone, linear resampling, additional 5ms end fades, no amplification','stereo_samples_identical':True}
(stage/'control-tone.json').write_text(json.dumps(tone_metadata,indent=2)+'\n')
session_name='usr/libexec/muos-c06-session';shutil.copyfile(repo/'port/device/rk-r35s-p0/frontend-audio-diagnostic/session.sh',assets/session_name.replace('/','_'))
runner_name='usr/libexec/muos-c01-run';run=(base/'extracted'/runner_name).read_text()
anchor='for name in ui-during.txt ui-before-stop.txt; do';assert run.count(anchor)==1
run=run.replace(anchor,'for name in ui-during.txt ui-before-stop.txt reference-48-during.txt reference-48-aplay.txt reference-44-during.txt reference-44-aplay.txt; do')
(assets/runner_name.replace('/','_')).write_text(run)
entries=[];commands=[]
for name in [tone_name,session_name,runner_name]:
    p=assets/name.replace('/','_');old=base/'extracted'/name;mode=0o644 if name==tone_name else 0o755
    entries.append({'path':name,'asset':p.name,'sha256':sha(p),'old_sha256':sha(old) if old.is_file() else None,'mode':mode})
    if old.exists():commands.append('rm /'+name)
    commands += [f'write assets/{p.name} /{name}',f'set_inode_field /{name} mode 0{mode|0o100000:o}']
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
for name in muos-c06-session muos-c01-run; do qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh -n "$root/usr/libexec/$name"; done
'''
with (stage/'audit.log').open('w') as out:subprocess.run(container+[audit],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=100)
assert all(sha(stage/'extracted'/e['path'])==e['sha256'] for e in entries)
assert not (stage/'extracted/var/lib/muos-seedrng').exists()
required={k:v for k,v in m['unchanged_required'].items() if k!=runner_name}
required.update({n:sha(base/'extracted'/n) for n in ['usr/share/muos-diagnostic/c05-tone.wav','opt/muos/share/theme/MustardOS/sound/back.wav','opt/muos/share/theme/MustardOS/sound/navigate.wav']})
plan={'experiment':m['experiment'],'diagnostic_revision_update':2,'authorized_secondary_c06_revision':True,'installer_sha256':sha(repo/'port/scripts/install-phase4-service-diagnostic.py'),'entries':entries,'unchanged_required':required}
(stage/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
inputs=['port/scripts/prepare-phase4-frontend-audio-comparison.py','port/device/rk-r35s-p0/frontend-audio-diagnostic/session.sh','port/scripts/check-phase4-frontend-audio-hooks.py','port/scripts/install-phase4-service-diagnostic.py']
record={**plan,'base_manifest_sha256':sha(base/'manifest.json'),'rootfs_sha256':sha(stage/'rootfs.ext4'),'host_audit_passed':True,'seed_material_included':False,'physical_audio_comparison_tested':False,'hardware_gain_157_route_SPK_HP_software_unity_unchanged':True,'control_tone':tone_metadata,'hook_fixtures':json.loads((stage/'hook-fixtures.json').read_text()),'port_inputs':{n:sha(repo/n) for n in inputs}}
(stage/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');(work/'linux-diagnostic/latest-frontend-audio-comparison').write_text(str(stage)+'\n')
print('C06 rate/effect comparison audited:',stage)
