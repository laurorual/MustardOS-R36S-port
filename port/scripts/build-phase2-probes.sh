#!/usr/bin/env bash
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase2"
output="$repo/dist/phase2"
revision=5e8635b3b485eec9ad2ace141c415fd2df47d8f1
mkdir -p "$work/source" "$work/diagnostics" "$output"
podman build --pull=never --iidfile "$work/toolchain.iid" \
    -t localhost/muos-r35s-phase2-toolchain:20261023 \
    -f "$repo/port/packaging/phase2-toolchain.Containerfile" "$repo/port/packaging" \
    > "$work/toolchain-build.log" 2>&1
git -C "$repo/refs/muos/frontend" archive "$revision" module/musplash.c LICENSE > "$work/upstream-source.tar"
tar -xf "$work/upstream-source.tar" -C "$work/source"
git -C "$repo" apply --directory=build/phase2/source "$repo/port/patches/0001-musplash-fb-read-write-fallback.patch"
cp "$repo/port/diagnostics/"*.c "$work/diagnostics/"
epoch=$(git -C "$repo/refs/muos/frontend" show -s --format=%ct "$revision")
podman run --rm --network=none --read-only --cap-drop=all \
    --security-opt=no-new-privileges --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev \
    -v "$work:/work:rw,Z" -w /work -e SOURCE_DATE_EPOCH="$epoch" \
    "$(cat "$work/toolchain.iid")" sh -eu -c '
    flags="-std=c11 -D_GNU_SOURCE -O2 -march=armv8-a -fPIE -fstack-protector-strong -D_FORTIFY_SOURCE=3 -Wall -Wextra -Wpedantic -ffile-prefix-map=/work=."
    link="-pie -Wl,-z,relro,-z,now"
    aarch64-linux-gnu-gcc $flags source/module/musplash.c -o musplash $(pkg-config --cflags --libs libpng) $link
    aarch64-linux-gnu-gcc $flags diagnostics/sdl-video-probe.c -o sdl-video-probe $(pkg-config --cflags --libs sdl2) $link
    aarch64-linux-gnu-gcc $flags diagnostics/drm-mode-probe.c -o drm-mode-probe $(pkg-config --cflags --libs libdrm) $link
    cp /usr/local/share/phase2-packages.txt packages.txt
    aarch64-linux-gnu-gcc --version > compiler.txt
    for name in musplash sdl-video-probe drm-mode-probe; do
        aarch64-linux-gnu-readelf -h -l -d -n --version-info "$name" > "$name.elf.txt"
        aarch64-linux-gnu-readelf --dyn-syms --wide "$name" > "$name.symbols.txt"
    done
    ' > "$work/compile.log" 2>&1
for name in musplash sdl-video-probe drm-mode-probe; do
    cp "$work/$name" "$work/$name.elf.txt" "$work/$name.symbols.txt" "$output/"
done
python3 "$repo/port/scripts/make-phase2-pattern.py" "$output/panel-test.png"
cp "$work/packages.txt" "$work/compiler.txt" "$work/upstream-source.tar" "$output/"
cp "$work/source/LICENSE" "$output/LICENSE.upstream"
cp "$repo/port/patches/0001-musplash-fb-read-write-fallback.patch" "$output/"
cp "$repo/port/scripts/phase2-device-session.py" "$output/"
cp "$repo/port/scripts/phase2-input-namespace.py" "$output/"
{
    printf 'upstream_revision=%s\nsource_date_epoch=%s\n' "$revision" "$epoch"
    printf 'toolchain_image_id=%s\n' "$(cat "$work/toolchain.iid")"
    printf 'target_isa=armv8-a\n'
    sha256sum "$repo/port/packaging/phase2-toolchain.Containerfile" "${BASH_SOURCE[0]}" "$repo/port/diagnostics/"*.c
} > "$output/build-manifest.txt"
(
    cd "$output"
    sha256sum musplash sdl-video-probe drm-mode-probe panel-test.png \
        phase2-device-session.py phase2-input-namespace.py *.elf.txt *.symbols.txt packages.txt compiler.txt \
        upstream-source.tar LICENSE.upstream build-manifest.txt *.patch > SHA256SUMS
)
printf 'Artifacts and ELF audits: %s\n' "$output"
