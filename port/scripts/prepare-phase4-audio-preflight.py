#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Host-only C05 preparation. Emits no installation plan and never uses SSH."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile,wave
r=Path(__file__).resolve().parents[2];work=r/'build/phase4'
base=work/'linux-diagnostic/native-frontend.urej9y1t';root=base/'extracted'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
meta=json.loads((base/'manifest.json').read_text())
assert sha(base/'rootfs.ext4')==meta['rootfs_sha256']
assert not (root/'var/lib/muos-seedrng').exists()
tone=r/'dist/phase4/core-native/core-tone.wav'
expected='959fcac27fe4bb517ea946d3725857c7fa01b61008c1363d6fdda3dfa96c43e8'
assert sha(tone)==expected
assert expected+'  core-tone.wav' in (r/'dist/phase4/core-native/SHA256SUMS').read_text()
s=Path(tempfile.mkdtemp(prefix='audio-preflight.',dir=work/'linux-diagnostic'));(s/'assets').mkdir()
shutil.copyfile(tone,s/'assets/c05-tone.wav')
shutil.copyfile(r/'port/device/rk-r35s-p0/audio-diagnostic/probe.sh',s/'assets/c05-audio-probe')
(s/'assets/c05-core.conf').write_text('audio=1\ninput=1\n')
with wave.open(str(tone),'rb') as w:
    info={'channels':w.getnchannels(),'sample_bytes':w.getsampwidth(),'rate':w.getframerate(),'frames':w.getnframes(),'seconds':w.getnframes()/w.getframerate()}
assert (info['channels'],info['sample_bytes'],info['rate'])==(2,2,48000) and info['seconds']<12
files=['usr/bin/aplay','usr/bin/amixer','usr/bin/wpctl','usr/lib/alsa-lib/libasound_module_pcm_pipewire.so','usr/libexec/muos-core-lifecycle','opt/muos/script/init/S80pipewire.sh']
for f in files:assert (root/f).is_file(),f
container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z','-e','STAGE_REL='+str(s.relative_to(work)),(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c']
code=r'''
root=/work/linux-diagnostic/native-frontend.urej9y1t/extracted
stage=/work/$STAGE_REL
qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh -n "$stage/assets/c05-audio-probe"
for program in aplay amixer wpctl; do
 qemu-aarch64 -cpu cortex-a35 -L "$root" -E LD_BIND_NOW=1 "$root/lib/ld-linux-aarch64.so.1" --list "$root/usr/bin/$program" > "$stage/$program-loader.txt" 2>&1
done
qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/usr/bin/aplay" --version > "$stage/aplay-version.txt"
readelf -h -d "$root/usr/lib/alsa-lib/libasound_module_pcm_pipewire.so" > "$stage/alsa-pipewire-elf.txt"
'''
with (s/'audit.log').open('w') as f:subprocess.run(container+[code],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=30)
record={'scope':'C05 host-only probe/assets preflight; NOT a media-ready payload','host_shell_and_loader_preflight_passed':True,'tone':info,'assets':{str(p.relative_to(s)):sha(p) for p in sorted((s/'assets').iterdir())},'base_manifest_sha256':sha(base/'manifest.json'),'existing_runtime':{f:sha(root/f) for f in files},'probe_source_sha256':sha(r/'port/device/rk-r35s-p0/audio-diagnostic/probe.sh'),'preparer_sha256':sha(Path(__file__)),'seed_material_included':False,'card_or_device_accessed':False,'rootfs_modified':False,'boot_runner_installer_collector_analyzer_integrated':False,'native_audio_tested':False,'audibility_approved':False}
(s/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');(work/'linux-diagnostic/latest-audio-preflight').write_text(str(s)+'\n');print('C05 host-only preparation:',s);print(json.dumps(info))
