#!/usr/bin/env bash
set -euo pipefail

repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
revision=5e8635b3b485eec9ad2ace141c415fd2df47d8f1
work="$repo/build/phase1"
output="$repo/dist/phase1"
recipe="$repo/port/packaging/phase1-toolchain.Containerfile"

for tool in podman git tar sha256sum; do
    command -v "$tool" >/dev/null || { printf 'Missing tool: %s\n' "$tool" >&2; exit 1; }
done

mkdir -p "$work/source" "$output"
podman build --pull=never --iidfile "$work/toolchain.iid" \
    -t localhost/muos-r35s-phase1-toolchain:20261023 \
    -f "$recipe" "$repo/port/packaging" > "$work/toolchain-build.log" 2>&1
toolchain=$(cat "$work/toolchain.iid")

git -C "$repo/refs/muos/frontend" archive "$revision" input LICENSE > "$work/source.tar"
tar -xf "$work/source.tar" -C "$work/source"
epoch=$(git -C "$repo/refs/muos/frontend" show -s --format=%ct "$revision")

podman run --rm --network=none --read-only --cap-drop=all \
    --security-opt=no-new-privileges --userns=keep-id \
    --tmpfs /tmp:rw,nosuid,nodev \
    -v "$work:/work:rw,Z" -w /work/source/input \
    -e SOURCE_DATE_EPOCH="$epoch" "$toolchain" sh -eu -c '
        flags="-std=c11 -O2 -pipe -flto=auto -ffunction-sections -fdata-sections"
        flags="$flags -fstack-protector-strong -D_FORTIFY_SOURCE=3 -D_GNU_SOURCE -DNDEBUG"
        flags="$flags -Wall -Wextra -Wpedantic -march=armv8-a -fPIE -ffile-prefix-map=/work=."
        make -B -j2 CC=aarch64-linux-gnu-gcc CFLAGS="$flags" \
            LDFLAGS="-flto=auto -Wl,--gc-sections -pie -Wl,-z,relro,-z,now" \
            BUILDDIR=/work/objects
        aarch64-linux-gnu-gcc --version > /work/compiler.txt
        aarch64-linux-gnu-gcc -print-sysroot > /work/sysroot.txt
        cp /usr/local/share/phase1-packages.txt /work/packages.txt
        file /work/objects/bin/muinput > /work/file.txt
        aarch64-linux-gnu-readelf -h -l -d -n --version-info \
            /work/objects/bin/muinput > /work/elf.txt
        aarch64-linux-gnu-readelf --dyn-syms --wide \
            /work/objects/bin/muinput > /work/symbols.txt
        aarch64-linux-gnu-readelf -n /usr/aarch64-linux-gnu/lib/libc.so.6 \
            > /work/sysroot-libc-notes.txt
    ' > "$work/compile.log" 2>&1

cp "$work/objects/bin/muinput" "$output/muinput"
cp "$work/source/LICENSE" "$output/LICENSE.upstream"
cp "$work/source.tar" "$output/upstream-source.tar"
for name in compiler sysroot packages file elf symbols sysroot-libc-notes; do
    cp "$work/$name.txt" "$output/$name.txt"
done
{
    printf 'upstream_revision=%s\n' "$revision"
    printf 'source_date_epoch=%s\n' "$epoch"
    printf 'toolchain_image_id=%s\n' "$toolchain"
    printf 'debian_snapshot=20261023T000000Z\n'
    printf 'isa=armv8-a\n'
    printf 'sysroot=Debian trixie arm64 cross libc development packages\n'
    printf 'runtime_status=not-assessed-by-build-script\n'
    sha256sum "$recipe" "${BASH_SOURCE[0]}"
} > "$output/build-manifest.txt"
(
    cd "$output"
    sha256sum muinput LICENSE.upstream upstream-source.tar \
        compiler.txt sysroot.txt packages.txt file.txt elf.txt symbols.txt \
        sysroot-libc-notes.txt build-manifest.txt > SHA256SUMS
)
printf 'Built: %s/muinput\nAudit: %s/elf.txt\n' "$output" "$output"
printf 'No target program was executed. Device validation is still required.\n'
