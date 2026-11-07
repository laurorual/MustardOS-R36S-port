#!/usr/bin/env bash
# Audit/package the host-built headless rootfs. No device access or deployment.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
[[ ! -f "$work/core/active" ]] || {
    echo 'Core profile active; use audit-phase4-core.sh and preserve rootfs-headless.' >&2; exit 1;
}
audit="$work/rootfs-audit"
output="$repo/dist/phase4/rootfs-headless"
[[ $(cat "$work/rootfs-build.exit" 2>/dev/null) == 0 ]] || {
    echo 'Need a completed successful rootfs build first.' >&2; exit 1;
}
[[ $(podman inspect --format '{{.State.Running}}' muos-r35s-phase4-rootfs) == false ]]
cmp "$repo/port/device/rk-r35s-p0/phase4-rootfs.defconfig" "$work/headless.defconfig"
mkdir -p "$audit"
python3 "$repo/port/scripts/verify-phase4-rootfs.py" "$work/rootfs-output" \
    > "$audit/static-verification.json"
podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
    --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev \
    -v "$work:/work:ro,z" -v "$audit:/audit:rw,z" -v "$repo/port:/port:ro,z" \
    "$(cat "$work/rootfs-container.iid")" sh -eu -c '
    prefix=/work/rootfs-output/host/bin/aarch64-buildroot-linux-gnu-
    target=/work/rootfs-output/target
    "${prefix}gcc" --version > /audit/userspace-compiler.txt
    "${prefix}gcc" -Wall -Wextra -Werror -O2 -mcpu=cortex-a35 -pthread \
        /port/probes/phase4-rootfs-abi.c -o /audit/abi-probe
    "${prefix}readelf" -h -l -d -n -V /audit/abi-probe > /audit/abi-probe.elf.txt
    "${prefix}readelf" -n "$target/lib/libc.so.6" > /audit/libc-notes.txt
    qemu-aarch64 --version > /audit/qemu-version.txt
    timeout 20 qemu-aarch64 -cpu cortex-a35 -L "$target" "$target/lib/ld-linux-aarch64.so.1" \
        --inhibit-cache --library-path "$target/lib:$target/usr/lib" \
        /audit/abi-probe > /audit/abi-qemu.txt
    grep -Fqx "libc_path=$target/lib/libc.so.6" /audit/abi-qemu.txt
    timeout 20 qemu-aarch64 -cpu cortex-a35 -L "$target" "$target/bin/busybox" true
    timeout 20 qemu-aarch64 -cpu cortex-a35 -L "$target" "$target/bin/bash" --version > /audit/bash-qemu.txt
    timeout 20 qemu-aarch64 -cpu cortex-a35 -L "$target" "$target/usr/bin/pipewire" --version > /audit/pipewire-qemu.txt
    timeout 20 qemu-aarch64 -cpu cortex-a35 -L "$target" "$target/usr/bin/wireplumber" --version > /audit/wireplumber-qemu.txt
    e2fsck -fn /work/rootfs-output/images/rootfs.ext4 > /audit/e2fsck.txt 2>&1
    dumpe2fs -h /work/rootfs-output/images/rootfs.ext4 > /audit/ext4-superblock.txt 2>&1
    debugfs -R "stat /sbin/init" /work/rootfs-output/images/rootfs.ext4 > /audit/image-init.txt 2>&1
    ' > "$audit/container-audit.log" 2>&1
mkdir -p "$output"
mkdir -p "$output/abi-runtime"
cp -L "$work/rootfs-output/target/lib/libc.so.6" "$output/abi-runtime/libc.so.6"
cp -L "$work/rootfs-output/target/lib/ld-linux-aarch64.so.1" "$output/abi-runtime/ld-linux-aarch64.so.1"
cp "$work"/rootfs-output/build/glibc-*/COPYING.LIB "$output/abi-runtime/COPYING.LIB"
cp --reflink=auto --sparse=always "$work/rootfs-output/images/rootfs.ext4" "$output/rootfs.ext4"
cp "$work/rootfs-output/.config" "$output/buildroot.config"
cp "$work/rootfs-resolved.defconfig" "$output/resolved.defconfig"
cp "$repo/port/device/rk-r35s-p0/phase4-sources.json" "$output/sources.json"
cp "$work/rootfs-packages.txt" "$output/container-packages.txt"
cp "$audit"/{static-verification.json,abi-probe,abi-probe.elf.txt,abi-qemu.txt,libc-notes.txt,userspace-compiler.txt,qemu-version.txt,ext4-superblock.txt,e2fsck.txt,image-init.txt} "$output/"
printf '%s\n' 'HEADLESS ROOTFS BUILD PROBE. NOT A FLASHABLE FIRMWARE.' \
    'No bootloader/kernel/DTB, GPU provider, muOS payload or muOS init integration.' \
    'QEMU user-mode checks do not validate boot or RK3326 hardware.' \
    'Do not write this filesystem to the current device.' > "$output/NOT-FOR-DEVICE-BOOT.txt"
epoch=$(git -C "$work/buildroot" show -s --format=%ct HEAD)
tar --sort=name --mtime="@$epoch" --owner=0 --group=0 --numeric-owner -C "$repo" \
    -czf "$output/port-source.tar.gz" \
    port/device/rk-r35s-p0/phase4-rootfs.defconfig \
    port/device/rk-r35s-p0/phase4-sources.json \
    port/packaging/phase4-rootfs.Containerfile \
    port/scripts/configure-phase4-rootfs.sh port/scripts/build-phase4-rootfs.sh \
    port/scripts/verify-phase4-rootfs.py port/scripts/audit-phase4-rootfs.sh \
    port/scripts/run-phase4-abi-probe.sh \
    port/scripts/collect-phase4-legal-info.sh \
    port/device/rk-r35s-p0/phase4-linux-headers.hash \
    port/probes/phase4-rootfs-abi.c
python3 - "$work" "$output" <<'PY'
from pathlib import Path
import hashlib, json, subprocess, sys, tarfile
work, output = map(Path, sys.argv[1:])
with tarfile.open(output / 'port-source.tar.gz') as archive:
    hashes = {item.name: hashlib.sha256(archive.extractfile(item).read()).hexdigest()
              for item in archive if item.isfile()}
archives = {}
for path in sorted((work / 'rootfs-downloads').glob('*/*')):
    if path.is_file() and (path.name.endswith(('.tar.gz', '.tar.xz', '.tar.bz2', '.tgz', '.zip'))):
        with path.open('rb') as source:
            archives[str(path.relative_to(work / 'rootfs-downloads'))] = hashlib.file_digest(source, 'sha256').hexdigest()
manifest = {'scope': 'headless standalone userspace probe, not flashable firmware',
            'buildroot_revision': subprocess.check_output(['git', '-C', str(work / 'buildroot'), 'rev-parse', 'HEAD'], text=True).strip(),
            'container_image_id': (work / 'rootfs-container.iid').read_text().strip(),
            'rootfs_built': True, 'qemu_user_smoke_passed': True,
            'native_probe_passed': False, 'boot_tested': False, 'muos_sysinit_integrated': False,
            'static_verification': json.loads((output / 'static-verification.json').read_text()),
            'port_source_sha256': hashes, 'download_archive_sha256': archives}
(output / 'build-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
PY
(cd "$output" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
printf 'Audited host-only artifact: %s\n' "$output"
