#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C05 seedless host blueprint and narrowly bounded boot audio diagnostic."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,tempfile
r=Path(__file__).resolve().parents[2];w=r/'build/phase4';base=w/'linux-diagnostic/native-frontend.urej9y1t'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
meta=json.loads((base/'manifest.json').read_text());assert sha(base/'rootfs.ext4')==meta['rootfs_sha256']
assert not (base/'extracted/var/lib/muos-seedrng').exists()
pre=Path((w/'linux-diagnostic/latest-audio-preflight').read_text().strip());assert sha(pre/'assets/c05-tone.wav')=='959fcac27fe4bb517ea946d3725857c7fa01b61008c1363d6fdda3dfa96c43e8'
s=Path(tempfile.mkdtemp(prefix='native-audio.',dir=w/'linux-diagnostic'));assets=s/'assets';assets.mkdir();shutil.copyfile(base/'rootfs.ext4',s/'rootfs.ext4')
bootstrap=(base/'assets/sbin_muos-ext4-diag').read_text().replace('/etc/muos-frontend-diagnostic','/etc/muos-audio-diagnostic').replace('MUOS-R35S-FRONTEND-P4-C04','MUOS-R35S-AUDIO-P4-C05').replace("'C04 marker missing'","'C05 marker missing'")
run=(base/'assets/usr_libexec_muos-c01-run').read_text().replace('C04','C05').replace('MUOS-R35S-FRONTEND-P4-C05','MUOS-R35S-AUDIO-P4-C05').replace('/etc/muos-frontend-diagnostic','/etc/muos-audio-diagnostic').replace('/run/muos/c04','/run/muos/c05').replace('DIAG06','DIAG07')
a=run.index('# SPDX-License-Identifier: MIT\n# Included in the C05');z=run.index("{\n    echo 'MUOS-R35S-AUDIO-P4-C05'",a)
run=run[:a]+'''if [ "$status" = 0 ]; then
    c05_play > "$state/play.log" 2>&1 || status=1
fi
'''+run[z:]
run=run.replace('c01_state=$state','c01_state=$state\ncore_bound=0\nasound_bound=0\n'+(r/'port/device/rk-r35s-p0/audio-diagnostic/session.sh').read_text())
anchor='''    /usr/libexec/muos-run-bounded "$seconds" "$@"'''
assert anchor in run
run=run.replace(anchor,'''    if [ "$1" = /etc/init.d/S95muos-core ] && [ "$2" = start ]; then
        c05_before_core || return 1
    fi
'''+anchor)
run=run.replace('! pidof muxfrontend muhotkey pipewire wireplumber >/dev/null || status=1','! pidof muxfrontend muhotkey >/dev/null || status=1\n    [ -f /run/muos/core/audio ] || status=1')
run=run.replace("echo 'FRONTEND'; cat \"$state/frontend.log\" 2>/dev/null",'''echo 'AUDIO START'
    cat "$state/play.log" 2>/dev/null
    for name in sink.txt codec.txt before.txt software-before.txt software-unity.txt during.txt aplay.txt after.txt software-restored.txt result.txt; do
        echo "FILE=$name"; cat "/run/muos/c05-audio/$name" 2>/dev/null
    done''')
anchor='c01_stop_chain /etc/init.d >> "$state/services.log" 2>&1 || status=1'
assert anchor in run
run=run.replace(anchor,anchor+'\nc05_audio_cleanup >> "$state/services.log" 2>&1 || status=1')
run=run.replace('for name in muinput dbus-daemon udevd; do','for name in muinput dbus-daemon udevd pipewire wireplumber aplay; do')
run=run.replace("    echo 'FINAL STATUS';",'''    echo 'AUDIO STOP'
    cat "$state/audio-cleanup.txt" 2>/dev/null
    echo 'ALSA BEFORE CORE'; cat "$state/alsa-before.txt" 2>/dev/null
    echo 'ALSA RESTORED'; cat "$state/alsa-restored.txt" 2>/dev/null
    echo 'AUDIO FALLBACK STOP'; cat "$state/audio-stop.txt" 2>/dev/null
    for logfile in /run/muos/core/pipewire.log /run/muos/core/wireplumber.log; do
        echo "$logfile"; tail -c 32768 "$logfile" 2>/dev/null
    done
    echo 'FINAL STATUS';''')
run=run.replace('C05: FRONTEND / INPUT OK','C05: AUDIO / INPUT OK').replace('Frontend stopped. No audio or network.','Audio stopped. No frontend or network.')
payload={'sbin/muos-ext4-diag':bootstrap,'usr/libexec/muos-audio-functions':(r/'port/device/rk-r35s-p0/audio-diagnostic/functions.sh').read_text(),'usr/libexec/muos-audio-probe':(r/'port/device/rk-r35s-p0/audio-diagnostic/probe.sh').read_text(),'usr/libexec/muos-c01-run':run,'etc/muos-audio-diagnostic':'MUOS-R35S-AUDIO-P4-C05\n'}
for name,text in payload.items():(assets/name.replace('/','_')).write_text(text)
shutil.copyfile(pre/'assets/c05-tone.wav',assets/'usr_share_muos-diagnostic_c05-tone.wav')
names=['sbin/muos-ext4-diag','usr/libexec/muos-audio-functions','usr/libexec/muos-audio-probe','usr/share/muos-diagnostic/c05-tone.wav','usr/libexec/muos-c01-run','etc/muos-audio-diagnostic']
entries=[];commands=['mkdir /usr/share/muos-diagnostic']
for name in names:
 p=assets/name.replace('/','_');old=base/'extracted'/name;mode=0o755 if name.startswith(('sbin/','usr/libexec/')) else 0o644
 entries.append({'path':name,'asset':p.name,'sha256':sha(p),'old_sha256':sha(old) if old.is_file() else None,'mode':mode})
 if old.exists():commands.append('rm /'+name)
 commands += [f'write assets/{p.name} /{name}',f'set_inode_field /{name} mode 0{mode|0o100000:o}']
(s/'debugfs.commands').write_text('\n'.join(commands)+'\n')
container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{w}:/work:rw,z','-e','STAGE_REL='+str(s.relative_to(w)),(w/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c']
audit=r'''
cd /work/$STAGE_REL
debugfs -w -f debugfs.commands rootfs.ext4 > debugfs.log 2>&1
e2fsck -fn rootfs.ext4 > fsck.log 2>&1
mkdir extracted
/work/graphics-config/output/host/bin/fakeroot debugfs -R "rdump / $PWD/extracted" rootfs.ext4 > extract.log 2>&1
root=$PWD/extracted
for file in sbin/muos-ext4-diag usr/libexec/muos-c01-run usr/libexec/muos-audio-probe usr/libexec/muos-audio-functions; do
 qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh -n "$root/$file"
done
for file in usr/bin/aplay usr/bin/amixer usr/bin/wpctl usr/sbin/alsactl; do
 name=${file##*/}
 qemu-aarch64 -cpu cortex-a35 -L "$root" -E LD_BIND_NOW=1 "$root/lib/ld-linux-aarch64.so.1" --list "$root/$file" > "$name-loader.txt" 2>&1
done
'''
with (s/'audit.log').open('w') as f:subprocess.run(container+[audit],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=100)
for e in entries:assert sha(s/'extracted'/e['path'])==e['sha256']
assert not (s/'extracted/var/lib/muos-seedrng').exists()
# Execute the real playback policy with fake commands/files; never touch audio.
fixtures={}
for case in ['success','player-failure','wrong-sink','wrong-gain','closed-pcm']:
 f=s/('fixture-'+case);f.mkdir();binpath=f/'bin';binpath.mkdir();(f/'volume').write_text('0.35\n');(f/'pcm').write_text('closed\n' if case=='closed-pcm' else 'format: S32_LE\nchannels: 2\nrate: 48000 (48000/1)\n')
 script='''#!/bin/sh
case "${0##*/}" in
 wpctl) case "$1" in
  inspect) if [ "$CASE" = wrong-sink ]; then echo 'node.name = "wrong"'; else echo 'node.name = "alsa_output.platform-rk817-sound.playback.0.0"'; fi ;;
  get-volume) printf 'Volume: %s\\n' "$(cat "$FIXTURE/volume")" ;;
  set-volume) if [ "$3" = 1.0 ]; then echo 1.00 > "$FIXTURE/volume"; else echo "$3" > "$FIXTURE/volume"; fi ;;
 esac ;;
 amixer) if [ "$CASE" = wrong-gain ]; then echo ' : values=94,94'; else echo ' : values=95,95'; fi ;;
 aplay) sleep 1; [ "$CASE" != player-failure ] ;;
esac
'''
 for n in ['wpctl','amixer','aplay']:(binpath/n).write_text(script);(binpath/n).chmod(0o755)
 bound=f/'bounded';bound.write_text('#!/bin/sh\nshift\nexec "$@"\n');bound.chmod(0o755)
 test='''. "$POLICY"
state=$FIXTURE;bounded=$FIXTURE/bounded;pcm=$FIXTURE/pcm;tone=fixture.wav;saved_volume=;sampler=
audio_play
rc=$?
audio_restore_volume || exit 8
exit "$rc"
'''
 x=subprocess.run(['sh','-c',test],env={**os.environ,'PATH':str(binpath)+':'+os.environ['PATH'],'CASE':case,'FIXTURE':str(f),'POLICY':str(r/'port/device/rk-r35s-p0/audio-diagnostic/functions.sh')},capture_output=True,text=True)
 assert (x.returncode==0)==(case=='success'),(case,x.stdout,x.stderr)
 assert (f/'volume').read_text().strip()=='0.35',case
 fixtures[case]={'expected_outcome_passed':True,'exit':x.returncode,'software_volume_restored':True}
required=['usr/libexec/muos-entropy-functions','etc/init.d/S05muos-entropy','usr/libexec/muos-core-lifecycle','etc/init.d/S95muos-core','opt/muos/script/init/S80pipewire.sh','usr/lib/alsa-lib/libasound_module_pcm_pipewire.so','opt/muos/device/control/asound.state']
plan={'experiment':'MUOS-R35S-AUDIO-P4-C05','authorized_secondary_c05_install':True,'installer_sha256':sha(r/'port/scripts/install-phase4-service-diagnostic.py'),'entries':entries,'unchanged_required':{n:sha(base/'extracted'/n) for n in required}}
(s/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
record={**plan,'base_manifest_sha256':sha(base/'manifest.json'),'rootfs_sha256':sha(s/'rootfs.ext4'),'host_audit_passed':True,'policy_fixtures':fixtures,'seed_material_included':False,'binaries_rebuilt':False,'native_audio_tested':False,'hardware_gain_reference':[95,95],'diagnostic_software_gain':'unity; previous wpctl level restored','port_inputs':{n:sha(r/n) for n in ['port/scripts/prepare-phase4-native-audio.py','port/scripts/install-phase4-service-diagnostic.py','port/device/rk-r35s-p0/audio-diagnostic/functions.sh','port/device/rk-r35s-p0/audio-diagnostic/probe.sh','port/device/rk-r35s-p0/audio-diagnostic/session.sh']}}
(s/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');(w/'linux-diagnostic/latest-native-audio').write_text(str(s)+'\n');print('C05 payload audited; native audio pending:',s)
