#!/usr/bin/env bash
# Private host/QEMU audit and RAM staging; never install or boot this image.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
f="$work/foundation"
[[ $(cat "$f/image.exit") == 0 && $(cat "$f/frontend-compile.exit") == 0 ]]
[[ $(podman inspect --format '{{.State.Running}}' muos-r35s-phase4-graphics) == false ]]
mkdir -p "$f/audit"
rm -f "$f/audit.exit"
python3 "$repo/port/scripts/verify-phase4-rootfs.py" "$work/graphics-config/output" > "$f/audit/rootfs.json"
stage=$(mktemp -d "$f/staging.XXXXXX")
mkdir "$stage/rootfs"
printf '%s\n' "$stage" > "$f/latest-staging-attempt"
export FOUNDATION_STAGE_REL=${stage#"$work/"}
podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
 --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev -e FOUNDATION_STAGE_REL \
 -v "$work:/work:rw,z" -v "$repo/port:/port:ro,z" "$(cat "$work/rootfs-container.iid")" sh -eu -c '
 out=/work/graphics-config/output
 stage=/work/$FOUNDATION_STAGE_REL
 target=$stage/rootfs
 audit=/work/foundation/audit
 sdk=$out/host
 "$sdk/bin/fakeroot" -s "$stage/metadata.fakeroot" debugfs -R "rdump / $target" "$out/images/rootfs.ext4" > "$audit/image-extract.txt" 2>&1
 export PKG_CONFIG_LIBDIR="$sdk/aarch64-buildroot-linux-gnu/sysroot/usr/lib/pkgconfig:$sdk/aarch64-buildroot-linux-gnu/sysroot/usr/share/pkgconfig"
 export PKG_CONFIG_SYSROOT_DIR="$sdk/aarch64-buildroot-linux-gnu/sysroot"
 prefix=$sdk/bin/aarch64-buildroot-linux-gnu-
 timeout 30 env -i PATH=/usr/bin:/bin qemu-aarch64 -cpu cortex-a35 -L "$target" \
   "$target/bin/busybox" --list > "$audit/busybox-applets.txt"
 grep -qx stat "$audit/busybox-applets.txt"
 "$sdk/bin/pkg-config" --modversion sdl2 egl glesv2 gbm libdrm > "$audit/pkgconfig-versions.txt"
 "${prefix}gcc" -Wall -Wextra -Werror -O2 -mcpu=cortex-a35 /port/probes/phase4-gbm-contract.c \
   $("$sdk/bin/pkg-config" --cflags --libs gbm) -o "$audit/gbm-contract"
 "${prefix}gcc" -Wall -Wextra -Werror -O2 -mcpu=cortex-a35 /port/probes/phase4-graphics-contract.c \
   -Wl,--no-as-needed $("$sdk/bin/pkg-config" --cflags --libs sdl2 egl glesv2 gbm libdrm) -ldl -o "$audit/graphics-contract"
 "${prefix}gcc" -Wall -Wextra -Werror -O2 -mcpu=cortex-a35 /port/probes/phase4-frontend-contract.c -ldl -o "$audit/frontend-contract"
 for probe in gbm-contract graphics-contract frontend-contract; do
  timeout 30 env -i PATH=/usr/bin:/bin qemu-aarch64 -cpu cortex-a35 -L "$target" \
   -E LD_BIND_NOW=1 -E LD_LIBRARY_PATH="$target/opt/muos/frontend/lib" "$audit/$probe" > "$audit/$probe-qemu.txt" 2>&1
 done
 for name in muxfrontend muhotkey mubattery muinput; do
  "${prefix}readelf" -h -l -d -V "$target/opt/muos/frontend/$name" > "$audit/$name.elf.txt"
  timeout 30 env -i PATH=/usr/bin:/bin qemu-aarch64 -cpu cortex-a35 -L "$target" \
   "$target/lib/ld-linux-aarch64.so.1" --list "$target/opt/muos/frontend/$name" > "$audit/$name-loader-qemu.txt" 2>&1
 done
 if [ -f "$target/opt/muos/frontend/muos-sdl-map" ]; then
  for name in muxfrontend muhotkey mubattery muos-sdl-map lib/libplutosvg.so lib/libui.so lib/libmuxcom.so lib/libmuxmod.so; do
   # Buildroot applies ROOTFS_OVERLAY after target strip: these ELF inputs
   # must remain byte-identical, unlike the packaged Mali provider above.
   cmp "/work/foundation/overlay/opt/muos/frontend/$name" "$target/opt/muos/frontend/$name"
  done
  rm -f "$audit/expected-frontend.elf"
  printf "8 approved ELF inputs match finalized image byte for byte (overlay after strip)\n" > "$audit/validated-component-comparison.txt"
  timeout 30 env -i PATH=/usr/bin:/bin qemu-aarch64 -cpu cortex-a35 -L "$target" \
    -E LD_BIND_NOW=1 "$target/opt/muos/frontend/muos-sdl-map" --info > "$audit/mapper-info-qemu.txt"
  for name in system/assign.sh device/audio.sh device/bright.sh var/display.sh var/governor.sh; do
   test -x "$target/opt/muos/script/$name"
   head -1 "$target/opt/muos/script/$name" | grep -qx "#!/bin/sh"
  done
 fi
 if [ -f "$target/usr/libexec/muos-ui-supervisor" ]; then
  cmp /work/foundation/overlay/usr/libexec/muos-ui-supervisor "$target/usr/libexec/muos-ui-supervisor"
  "${prefix}readelf" -h -l -d -V "$target/usr/libexec/muos-ui-supervisor" > "$audit/ui-supervisor.elf.txt"
  if timeout 10 env -i PATH=/usr/bin:/bin qemu-aarch64 -cpu cortex-a35 -L "$target" \
    -E LD_BIND_NOW=1 "$target/usr/libexec/muos-ui-supervisor" --status; then exit 1; else test "$?" = 3; fi
 fi
 if [ -d "$target/lib/modules/4.4.189-muos-r35s-p4" ]; then
  # These modes only inspect metadata/resolve paths, including under QEMU.
  timeout 30 env -i PATH=/usr/bin:/bin qemu-aarch64 -cpu cortex-a35 -L "$target" \
   -0 modinfo "$target/usr/bin/kmod" -b "$target" -k 4.4.189-muos-r35s-p4 -F vermagic 8821cu > "$audit/modinfo-qemu.txt"
  grep -qx "4.4.189-muos-r35s-p4 SMP mod_unload aarch64 *" "$audit/modinfo-qemu.txt"
  for pair in "wifi:usb:v0BDApC820d0200dcEFdsc02dp01icFFiscFFipFFin02" "bluetooth:usb:v0BDApC820d0200dcEFdsc02dp01icE0isc01ip01in00"; do
   name=${pair%%:*}
   alias=${pair#*:}
   timeout 30 env -i PATH=/usr/bin:/bin qemu-aarch64 -cpu cortex-a35 -L "$target" \
    -0 modprobe "$target/usr/bin/kmod" -d "$target" -S 4.4.189-muos-r35s-p4 \
    -C "$target/etc/modprobe.d" -b --show-depends "$alias" > "$audit/$name-modprobe-qemu.txt" 2>&1
  done
  grep -q 8821cu.ko "$audit/wifi-modprobe-qemu.txt"
  grep -q btusb.ko "$audit/bluetooth-modprobe-qemu.txt"
  grep -q btrtl.ko "$audit/bluetooth-modprobe-qemu.txt"
  ! grep -q rtk_btusb.ko "$audit/bluetooth-modprobe-qemu.txt"
 fi
 "${prefix}readelf" -d "$target/usr/lib/libmali-bifrost-g31-rxp0-gbm.so" > "$audit/mali-dynamic.txt"
 # Reproduce the provider recipe transformation independently from the ZIP source.
 cp /work/foundation/provider-source/lib/aarch64-linux-gnu/libmali-bifrost-g31-rxp0-gbm.so "$audit/expected-r13.so"
 "$sdk/bin/patchelf" --set-soname libmali.so.1 "$audit/expected-r13.so"
 cmp "$audit/expected-r13.so" "$sdk/aarch64-buildroot-linux-gnu/sysroot/usr/lib/libmali-bifrost-g31-rxp0-gbm.so"
 # Buildroot finalization may strip target libraries, independently of the SDK.
 "${prefix}strip" --remove-section=.comment --remove-section=.note "$audit/expected-r13.so"
 cmp "$audit/expected-r13.so" "$target/usr/lib/libmali-bifrost-g31-rxp0-gbm.so"
 rm "$audit/expected-r13.so"
 e2fsck -fn "$out/images/rootfs.ext4" > "$audit/e2fsck.txt" 2>&1
 "$sdk/bin/fakeroot" -i "$stage/metadata.fakeroot" tar -C "$target" \
   --exclude=./dev --exclude=./proc --exclude=./sys --exclude=./tmp --exclude=./run -czf "$stage/core-staging.tar.gz" .
 ' > "$f/audit/run.log" 2>&1
python3 - "$repo" "$stage" <<'PY'
from pathlib import Path
import hashlib,json,sys
import importlib.util
repo,stage=map(Path,sys.argv[1:]);work=repo/'build/phase4';f=work/'foundation'
def sha(p):
 with p.open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
target=stage/'rootfs'
modules=json.loads((f/'overlay-manifest.json').read_text()).get('bsp_modules')
if modules:
 sys.dont_write_bytecode=True
 spec=importlib.util.spec_from_file_location('module_audit',repo/'port/scripts/verify-phase4-modules.py')
 module_audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(module_audit)
 inventory=module_audit.verify(target)
 assert inventory['aarch64_et_rel_count']==modules['aarch64_et_rel_count']
 for name,h in modules['overlay_sha256'].items():assert sha(target/name)==h,name
 assert sorted(str(p.relative_to(target/'lib/firmware')) for p in (target/'lib/firmware').rglob('*') if p.is_file())==sorted(modules['lock']['firmware_package']['files'])
 (f/'audit/image-modules.json').write_text(json.dumps(inventory,indent=2)+'\n')
for name,h in json.loads((f/'overlay-manifest.json').read_text())['overlay_sha256'].items():
 # Buildroot strips the new ELF files during finalization. Verify scripts/data
 # byte for byte and verify ELF/link contracts separately above.
 p=target/name
 if (f/'overlay'/name).read_bytes()[:4]!=b'\x7fELF':assert sha(p)==h,name
init=json.loads((f/'overlay-manifest.json').read_text()).get('init_services')
if init:
 assert (target/'etc/init.d/S99muos-ui').is_file()
 assert (target/'etc/init.d/S96muos-input-ready').is_file()
 enabled=json.loads((f/'overlay-manifest.json').read_text())['frontend_autostart']
 assert f'enabled={int(enabled)}\n' in (target/'etc/default/muos-ui').read_text()
else:
 assert not any('S99' in p.name for p in (target/'etc/init.d').iterdir())
runtime=json.loads((f/'overlay-manifest.json').read_text()).get('validated_runtime_components')
if runtime:
 assert len(json.loads((target/'opt/muos/share/info/manifest/core.json').read_text()))>10
 hotkeys=json.loads((target/'opt/muos/share/hotkey/r35s-bringup.json').read_text())
 assert set(hotkeys)=={'devices','VOL_DOWN','VOL_UP','BRIGHT_DOWN','BRIGHT_UP'}
 assert sorted(p.name for p in (target/'opt/muos/share/hotkey').glob('*.json'))==['r35s-bringup.json']
 assert (target/'opt/muos/config/settings/general/volume').read_text().strip()=='35'
 # Product assets keep their originals; the audible help swap was a RAM control.
 original=work/'menu/assets/opt/muos/share/theme/MustardOS/sound'
 for name in ['info_open.wav','info_close.wav']:
  assert sha(target/'opt/muos/share/theme/MustardOS/sound'/name)==sha(original/name)
manifest={'scope':'private coherent R13 SDK/target image, core UI and single-card storage adapter',
 'rootfs':json.loads((f/'audit/rootfs.json').read_text()),
 'container_image_id':(work/'rootfs-container.iid').read_text().strip(),
 'provider':json.loads((f/'provider-manifest.json').read_text()),
 'overlay':json.loads((f/'overlay-manifest.json').read_text()),
 'sdk_provider_sha256':sha(work/'graphics-config/output/host/aarch64-buildroot-linux-gnu/sysroot/usr/lib/libmali-bifrost-g31-rxp0-gbm.so'),
 'image_provider_sha256':sha(target/'usr/lib/libmali-bifrost-g31-rxp0-gbm.so'),
 'staging_sha256':sha(stage/'core-staging.tar.gz'),
 'qemu_link_load_passed':True,'native_storage_tested':False,
 'full_frontend_native_tested':False,'frontend_autostart':json.loads((f/'overlay-manifest.json').read_text())['frontend_autostart'],
 'firmware_boot_tested':False,'redistribution_approved':False,
 'port_inputs':{str(p.relative_to(repo)):sha(p) for p in sorted((repo/'port').rglob('*')) if p.is_file() and '__pycache__' not in str(p)}}
(stage/'staging-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(f/'latest-staging').write_text(str(stage)+'\n')
(f/'audit.exit').write_text('0\n')
print('Private foundation host audit passed; finalized image extracted without runtime substitution:',stage)
PY
