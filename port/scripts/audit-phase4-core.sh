#!/usr/bin/env bash
# Inspect/repackage the additive core rootfs. No SSH or device access.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
output="$repo/dist/phase4/core-native"
[[ $(cat "$work/core/build.exit") == 0 ]]
[[ $(podman inspect --format '{{.State.Running}}' muos-r35s-phase4-core) == false ]]
mkdir -p "$work/core/audit" "$work/core/qemu-vars/config/probe" "$work/core/qemu-vars/device" \
    "$work/core/qemu-vars/run" "$work/core/qemu-vars/kiosk" "$work/core/qemu-vars/system"
printf '1\n' > "$work/core/qemu-vars/config/probe/value"
python3 - "$work/core/image-rootfs" <<'PY'
from pathlib import Path
import shutil, sys
root=Path(sys.argv[1])
if root.exists():
    shutil.rmtree(root)
root.mkdir()
root.with_suffix('.fakeroot').unlink(missing_ok=True)
PY
python3 "$repo/port/scripts/verify-phase4-rootfs.py" "$work/rootfs-output" > "$work/core/audit/rootfs.json"
podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
    --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev -v "$work:/work:rw,z" \
    "$(cat "$work/rootfs-container.iid")" sh -eu -c '
    # Buildroot removes its finalized per-filesystem tree after mkfs. Extract
    # the actual image read-only via debugfs; do not stage raw TARGET_DIR.
    fakeroot=/work/rootfs-output/host/bin/fakeroot
    "$fakeroot" -s /work/core/image-rootfs.fakeroot debugfs -R "rdump / /work/core/image-rootfs" /work/rootfs-output/images/rootfs.ext4 > /work/core/audit/image-extract.txt 2>&1
    target=/work/core/image-rootfs
    prefix=/work/rootfs-output/host/bin/aarch64-buildroot-linux-gnu-
    for program in muvarctl muinput mulog; do
        "${prefix}readelf" -h -l -d -V "$target/opt/muos/frontend/$program" > /work/core/audit/"$program".elf.txt
    done
    qemu-aarch64 -cpu cortex-a35 -L "$target" "$target/opt/muos/frontend/muinput" --list-devices > /work/core/audit/muinput-qemu.txt
    qemu-aarch64 -cpu cortex-a35 -L "$target" "$target/opt/muos/bin/fnv1a" abc > /work/core/audit/fnv1a-qemu.txt
    [ "$(cat /work/core/audit/fnv1a-qemu.txt)" = 1a47e90b ]
    export MUOS_CONF_GLOBAL=/work/core/qemu-vars/config MUOS_CONF_DEVICE=/work/core/qemu-vars/device
    export MUOS_CONF_KIOSK=/work/core/qemu-vars/kiosk MUOS_CONF_SYSTEM=/work/core/qemu-vars/system
    export MUOS_RUN_DIR=/work/core/qemu-vars/run
    qemu-aarch64 -cpu cortex-a35 -L "$target" "$target/opt/muos/frontend/muvarctl" build
    qemu-aarch64 -cpu cortex-a35 -L "$target" "$target/opt/muos/frontend/muvarctl" set global probe/value 2
    result=$(qemu-aarch64 -cpu cortex-a35 -L "$target" "$target/opt/muos/frontend/muvarctl" get global probe/value)
    [ "$result" = 2 ]
    printf "build/set/get=OK\n" > /work/core/audit/muvarctl-qemu.txt
    e2fsck -fn /work/rootfs-output/images/rootfs.ext4 > /work/core/audit/e2fsck.txt 2>&1
    "$fakeroot" -i /work/core/image-rootfs.fakeroot tar -C "$target" --exclude=./dev --exclude=./proc --exclude=./sys \
        --exclude=./tmp --exclude=./run -czf /work/core/core-staging.tar.gz .
    ' > "$work/core/audit/run.log" 2>&1
python3 - "$repo" "$work" <<'PY'
from pathlib import Path
import ast, json, math, struct, sys, wave
repo,work=map(Path,sys.argv[1:])
root=work/'core/image-rootfs'
assert '/dev/root / ext4' in (root/'etc/fstab').read_text()
assert any(line.startswith('dbus:') for line in (root/'etc/passwd').read_text().splitlines())
assert not (root/'opt/muos/script/init/sysinit').exists()
assert sorted(p.name for p in (root/'etc/init.d').glob('*pipewire*'))==[]
assert (root/'etc/init.d/S95muos-core').read_bytes()==(repo/'port/device/rk-r35s-p0/S95muos-core').read_bytes()
for name in ['phase4-core-session.py','phase4-core-namespace.py']:
    ast.parse((repo/'port/scripts'/name).read_text())
tone=work/'core/core-tone.wav'
with wave.open(str(tone),'wb') as wav:
    wav.setparams((2,2,48000,0,'NONE','not compressed'))
    frames=bytearray()
    for beep in range(3):
        for i in range(48000):
            # 300 ms at 1200 Hz, then 700 ms silence; short fades avoid clicks.
            envelope=max(0,min(1,i/240,(14400-i)/240)) if i<14400 else 0
            sample=round(0.2*32767*envelope*math.sin(2*math.pi*1200*i/48000))
            frames+=struct.pack('<hh',sample,sample)
    wav.writeframes(frames)
PY
# Stage the actual image contents, including Buildroot-generated users.
# The diagnostic tone stays outside the image.
mkdir -p "$output"
cp --reflink=auto --sparse=always "$work/rootfs-output/images/rootfs.ext4" "$output/rootfs.ext4"
cp "$work/core/source-manifest.json" "$output/"
cp "$work/core/audit/"* "$output/"
cp "$work/core/core-tone.wav" "$repo/port/scripts/phase4-core-session.py" \
    "$repo/port/scripts/phase4-core-namespace.py" "$output/"
cp "$work/core/"*-source.tar "$output/"
cp "$work/rootfs-output/.config" "$output/buildroot.config"
cp "$work/core/core-staging.tar.gz" "$output/"
tar -C "$repo" --exclude=__pycache__ --exclude='*.pyc' -czf "$output/port-source.tar.gz" port
printf '%s\n' 'EXPERIMENTAL CORE ROOTFS; NOT A FLASHABLE FIRMWARE.' \
    'Full muOS sysinit/frontend/GPU/boot chain are not integrated.' \
    'Native core tests use private namespaces in RAM, not a boot of this image.' > "$output/NOT-FOR-DEVICE-BOOT.txt"
(cd "$output" && sha256sum core-staging.tar.gz phase4-core-session.py phase4-core-namespace.py core-tone.wav > session-SHA256SUMS)
python3 - "$work" "$output" <<'PY'
from pathlib import Path
import json, sys, hashlib
work,out=map(Path,sys.argv[1:])
manifest={'purpose':'core/cache/audio bring-up', 'full_muos_sysinit':False,'boot_tested':False,
          'qemu_utilities_passed':True,'native_core_tested':False,'native_audio_tested':False,
          'container_image_id':(work/'rootfs-container.iid').read_text().strip(),
          'rootfs':json.loads((work/'core/audit/rootfs.json').read_text()),
          'source_manifest':json.loads((work/'core/source-manifest.json').read_text())}
(out/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with (out/'SHA256SUMS').open('w') as sums:
 for path in sorted(out.rglob('*')):
  if path.is_file() and path.name!='SHA256SUMS':
   with path.open('rb') as f: sha=hashlib.file_digest(f,'sha256').hexdigest()
   sums.write(f'{sha}  {path.relative_to(out)}\n')
PY
echo "Core host audit and staging package: $output"
