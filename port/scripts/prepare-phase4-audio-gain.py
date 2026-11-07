#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C05 diagnostic codec157 with readback restoration; no boot preset changes."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,tempfile
r=Path(__file__).resolve().parents[2];w=r/'build/phase4';base=w/'linux-diagnostic/audio-enumerate.cmak5i25'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((base/'manifest.json').read_text());assert sha(base/'rootfs.ext4')==m['rootfs_sha256']
s=Path(tempfile.mkdtemp(prefix='audio-gain.',dir=w/'linux-diagnostic'));a=s/'assets';a.mkdir();shutil.copyfile(base/'rootfs.ext4',s/'rootfs.ext4')
run=(base/'assets/usr_libexec_muos-c01-run').read_text().replace('software-restored.txt result.txt','software-restored.txt codec-restored.txt result.txt')
probe=(r/'port/device/rk-r35s-p0/audio-diagnostic/probe.sh').read_text();assert 'probe_codec_gain=95' in probe
payload={'usr/libexec/muos-audio-functions':(r/'port/device/rk-r35s-p0/audio-diagnostic/functions.sh').read_text(),'usr/libexec/muos-audio-probe':probe.replace('probe_codec_gain=95','probe_codec_gain=157'),'usr/libexec/muos-c01-run':run}
entries=[];commands=[]
for name,text in payload.items():
 p=a/name.replace('/','_');p.write_text(text);entries.append({'path':name,'asset':p.name,'sha256':sha(p),'old_sha256':sha(base/'extracted'/name),'mode':0o755})
 commands += ['rm /'+name,f'write assets/{p.name} /{name}',f'set_inode_field /{name} mode 0100755']
(s/'debugfs.commands').write_text('\n'.join(commands)+'\n')
container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{w}:/work:rw,z','-e','STAGE_REL='+str(s.relative_to(w)),(w/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c']
audit=r'''
cd /work/$STAGE_REL
debugfs -w -f debugfs.commands rootfs.ext4 > debugfs.log 2>&1
e2fsck -fn rootfs.ext4 > fsck.log 2>&1
mkdir extracted
/work/graphics-config/output/host/bin/fakeroot debugfs -R "rdump / $PWD/extracted" rootfs.ext4 > extract.log 2>&1
root=$PWD/extracted
for name in muos-audio-functions muos-audio-probe muos-c01-run; do qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh -n "$root/usr/libexec/$name"; done
'''
with (s/'audit.log').open('w') as f:subprocess.run(container+[audit],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=100)
for e in entries:assert sha(s/'extracted'/e['path'])==e['sha256']
assert not (s/'extracted/var/lib/muos-seedrng').exists()
fixtures={}
for case in ['success','player-failure','closed-pcm','software-set-failure']:
 f=Path(tempfile.mkdtemp(prefix='fixture-'+case+'.',dir=s));binpath=f/'bin';binpath.mkdir();(f/'volume').write_text('0.35\n');(f/'gain').write_text('95,95\n');(f/'pcm').write_text('closed\n' if case=='closed-pcm' else 'format: S32_LE\nchannels: 2\nrate: 48000\n')
 script='''#!/bin/sh
case "${0##*/}" in
 wpctl) case "$1" in
  inspect) echo 'node.name = "alsa_output.platform-rk817-sound.playback.0.0"' ;;
  get-volume) printf 'Volume: %s\\n' "$(cat "$FIXTURE/volume")" ;;
  set-volume) if [ "$3" = 1.0 ]; then [ "$CASE" != software-set-failure ] || exit 1; echo 1.00 > "$FIXTURE/volume"; else echo "$3" > "$FIXTURE/volume"; fi ;;
 esac ;;
 amixer) if [ "$3" = cset ]; then echo "$5" > "$FIXTURE/gain"; fi; printf ' : values=%s\\n' "$(cat "$FIXTURE/gain")" ;;
 aplay) sleep 1; [ "$CASE" != player-failure ] ;;
esac
'''
 for name in ['wpctl','amixer','aplay']:(binpath/name).write_text(script);(binpath/name).chmod(0o755)
 bound=f/'bounded';bound.write_text('#!/bin/sh\nshift\nexec "$@"\n');bound.chmod(0o755)
 test='''. "$POLICY"
state=$FIXTURE;bounded=$FIXTURE/bounded;pcm=$FIXTURE/pcm;tone=fixture;probe_codec_gain=157;saved_volume=;saved_codec=;sampler=
audio_play
rc=$?
audio_restore_all || exit 8
exit "$rc"
'''
 x=subprocess.run(['sh','-c',test],env={**os.environ,'PATH':str(binpath)+':'+os.environ['PATH'],'CASE':case,'FIXTURE':str(f),'POLICY':str(r/'port/device/rk-r35s-p0/audio-diagnostic/functions.sh')},capture_output=True,text=True)
 assert (x.returncode==0)==(case=='success'),(case,x.stdout,x.stderr)
 assert (f/'gain').read_text().strip()=='95,95' and (f/'volume').read_text().strip()=='0.35',case
 fixtures[case]={'expected_outcome_passed':True,'exit':x.returncode,'codec95_restored':True,'software_restored':True}
required={**m['unchanged_required'],'usr/lib/udev/rules.d/79-muos-rk817-path.rules':sha(base/'extracted/usr/lib/udev/rules.d/79-muos-rk817-path.rules')}
plan={'experiment':m['experiment'],'diagnostic_revision_update':4,'authorized_secondary_c05_revision':True,'installer_sha256':sha(r/'port/scripts/install-phase4-service-diagnostic.py'),'entries':entries,'unchanged_required':required}
(s/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
record={**plan,'base_manifest_sha256':sha(base/'manifest.json'),'rootfs_sha256':sha(s/'rootfs.ext4'),'host_audit_passed':True,'gain_restore_fixtures':fixtures,'seed_material_included':False,'native_audio_audibility_tested':False,'diagnostic_gain':157,'restored_gain':95,'persistent_profile_gain_changed':False,'port_inputs':{n:sha(r/n) for n in ['port/scripts/prepare-phase4-audio-gain.py','port/device/rk-r35s-p0/audio-diagnostic/functions.sh','port/device/rk-r35s-p0/audio-diagnostic/probe.sh','port/scripts/install-phase4-service-diagnostic.py']}}
(s/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');(w/'linux-diagnostic/latest-audio-gain').write_text(str(s)+'\n');print('C05 temporary gain157 audited:',s)
