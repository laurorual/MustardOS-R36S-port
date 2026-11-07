#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C05 SPK_HP comparison at the already tested gain157; read-only HW snapshots."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,tempfile

r=Path(__file__).resolve().parents[2];w=r/'build/phase4'
base=w/'linux-diagnostic/audio-gain.39qzpnz_'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((base/'manifest.json').read_text())
assert sha(base/'rootfs.ext4')==m['rootfs_sha256']
s=Path(tempfile.mkdtemp(prefix='audio-route.',dir=w/'linux-diagnostic'))
a=s/'assets';a.mkdir();shutil.copyfile(base/'rootfs.ext4',s/'rootfs.ext4')
run=(base/'assets/usr_libexec_muos-c01-run').read_text()
anchor='software-restored.txt codec-restored.txt result.txt'
assert run.count(anchor)==1
run=run.replace(anchor,'software-restored.txt path-before.txt path-restored.txt codec-restored.txt result.txt')
probe=(r/'port/device/rk-r35s-p0/audio-diagnostic/probe.sh').read_text()
for old,new in [('probe_codec_gain=95','probe_codec_gain=157'),('probe_playback_path=SPK\n','probe_playback_path=SPK_HP\n'),('audio_hardware_debug=0','audio_hardware_debug=1')]:
    assert probe.count(old)==1;probe=probe.replace(old,new)
payload={
 'usr/libexec/muos-audio-functions':(r/'port/device/rk-r35s-p0/audio-diagnostic/functions.sh').read_text(),
 'usr/libexec/muos-audio-probe':probe,'usr/libexec/muos-c01-run':run}
entries=[];commands=[]
for name,text in payload.items():
    p=a/name.replace('/','_');p.write_text(text)
    entries.append({'path':name,'asset':p.name,'sha256':sha(p),'old_sha256':sha(base/'extracted'/name),'mode':0o755})
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
for name in muos-audio-functions muos-audio-probe muos-c01-run; do
 qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh -n "$root/usr/libexec/$name"
done
'''
with (s/'audit.log').open('w') as out:subprocess.run(container+[audit],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=100)
for e in entries:assert sha(s/'extracted'/e['path'])==e['sha256']
assert not (s/'extracted/var/lib/muos-seedrng').exists()
fixtures={}
for case in ['success','player-failure','closed-pcm','software-set-failure','path-set-failure','codec-set-failure','path-restore-failure','codec-restore-failure']:
    f=Path(tempfile.mkdtemp(prefix='fixture-'+case+'.',dir=s));binpath=f/'bin';binpath.mkdir()
    for name,value in {'volume':'0.35','gain':'95,95','path':'1','pcm':('closed' if case=='closed-pcm' else 'format: S32_LE\nchannels: 2\nrate: 48000')}.items():(f/name).write_text(value+'\n')
    for sub,content in {'regmap/0-0020-rk817-codec/registers':'38: 10\n','regmap/ff070000.i2s/registers':'00: 0000001f\n','clk/clk_summary':'clk_i2s1 2 2 12288000\n'}.items():
        p=f/'debug'/sub;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
    script=r'''#!/bin/sh
case "${0##*/}" in
 wpctl) case "$1" in
  inspect) echo 'node.name = "alsa_output.platform-rk817-sound.playback.0.0"' ;;
  get-volume) printf 'Volume: %s\n' "$(cat "$FIXTURE/volume")" ;;
  set-volume) if [ "$3" = 1.0 ]; then [ "$CASE" != software-set-failure ] || exit 1; echo 1.00 > "$FIXTURE/volume"; else echo "$3" > "$FIXTURE/volume"; fi ;;
 esac ;;
 amixer)
  case "$4" in
   'name=Playback Path')
    if [ "$3" = cset ]; then
     case "$5" in SPK_HP) echo 3 > "$FIXTURE/path"; [ "$CASE" != path-set-failure ] || exit 1 ;;
      SPK) if [ "$CASE" = path-restore-failure ] && [ ! -f "$FIXTURE/failed-once" ]; then touch "$FIXTURE/failed-once"; exit 1; fi; echo 1 > "$FIXTURE/path" ;;
     esac
    fi
    echo " ; Item #3 'SPK_HP'"; printf ' : values=%s\n' "$(cat "$FIXTURE/path")" ;;
   'name=Playback Volume')
    if [ "$3" = cset ]; then
     if [ "$5" = 95,95 ] && [ "$CASE" = codec-restore-failure ] && [ ! -f "$FIXTURE/failed-once" ]; then touch "$FIXTURE/failed-once"; exit 1; fi
     echo "$5" > "$FIXTURE/gain"
     if [ "$5" = 157,157 ]; then [ "$CASE" != codec-set-failure ] || exit 1; fi
    fi
    printf ' : values=%s\n' "$(cat "$FIXTURE/gain")" ;;
   *) echo ' : values=off' ;;
  esac ;;
 aplay) sleep 1; [ "$CASE" != player-failure ] ;;
esac
'''
    for name in ['wpctl','amixer','aplay']:(binpath/name).write_text(script);(binpath/name).chmod(0o755)
    bound=f/'bounded';bound.write_text('#!/bin/sh\nshift\nexec "$@"\n');bound.chmod(0o755)
    test=r'''. "$POLICY"
state=$FIXTURE;bounded=$FIXTURE/bounded;pcm=$FIXTURE/pcm;tone=fixture
probe_codec_gain=157;probe_playback_path=SPK_HP;audio_hardware_debug=1;debug_root=$FIXTURE/debug
saved_volume=;saved_codec=;saved_path=;sampler=
audio_play
rc=$?
audio_restore_all || exit 8
exit "$rc"
'''
    x=subprocess.run(['sh','-c',test],env={**os.environ,'PATH':str(binpath)+':'+os.environ['PATH'],'CASE':case,'FIXTURE':str(f),'POLICY':str(r/'port/device/rk-r35s-p0/audio-diagnostic/functions.sh')},capture_output=True,text=True)
    assert (x.returncode==0)==(case=='success'),(case,x.stdout,x.stderr)
    assert all((f/name).read_text().strip()==value for name,value in {'gain':'95,95','volume':'0.35','path':'1'}.items()),case
    if case=='success':
        during=(f/'during.txt').read_text();assert 'CODEC_REGISTERS\n38: 10' in during and ': values=3' in during
        assert 'C05_PLAYBACK_PATH=SPK_HP' in (f/'result.txt').read_text()
    fixtures[case]={'expected_outcome_passed':True,'exit':x.returncode,'codec95_software035_routeSPK_restored':True}
plan={'experiment':m['experiment'],'diagnostic_revision_update':5,'authorized_secondary_c05_revision':True,'installer_sha256':sha(r/'port/scripts/install-phase4-service-diagnostic.py'),'entries':entries,'unchanged_required':m['unchanged_required']}
(s/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
inputs=['port/scripts/prepare-phase4-audio-route.py','port/device/rk-r35s-p0/audio-diagnostic/functions.sh','port/device/rk-r35s-p0/audio-diagnostic/probe.sh','port/scripts/install-phase4-service-diagnostic.py']
record={**plan,'base_manifest_sha256':sha(base/'manifest.json'),'rootfs_sha256':sha(s/'rootfs.ext4'),'host_audit_passed':True,'route_restore_fixtures':fixtures,'seed_material_included':False,'native_audio_audibility_tested':False,'diagnostic_gain':157,'diagnostic_route':'SPK_HP','restored_gain':95,'restored_route':'SPK','persistent_profile_changed':False,'read_only_codec_i2s_clock_snapshots':True,'port_inputs':{n:sha(r/n) for n in inputs}}
(s/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
(w/'linux-diagnostic/latest-audio-route').write_text(str(s)+'\n')
print('C05 transient SPK_HP audited:',s)
