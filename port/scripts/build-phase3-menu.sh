#!/usr/bin/env bash
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase3"
output="$repo/dist/phase3"
revision=5e8635b3b485eec9ad2ace141c415fd2df47d8f1
mkdir -p "$work/source" "$work/deps" "$output"
podman build --pull=never --iidfile "$work/toolchain.iid" \
    -t localhost/muos-r35s-phase3-toolchain:20261023 \
    -f "$repo/port/packaging/phase3-toolchain.Containerfile" "$repo/port/packaging" \
    > "$work/toolchain-build.log" 2>&1
git -C "$repo/refs/muos/frontend" archive "$revision" > "$work/frontend-source.tar"
tar -xf "$work/frontend-source.tar" -C "$work/source"
git -C "$repo" apply --directory=build/phase3/source "$repo/port/patches/0003-frontend-r35s-panel0-board.patch"
cp "$repo/port/diagnostics/phase3-menu.c" "$repo/port/packaging/phase3-menu.mk" "$work/source/"
python3 - "$work/deps" <<'PY'
import hashlib, sys, tarfile, urllib.request
from pathlib import Path
root = Path(sys.argv[1])
path = root / 'mojibake-0.3.6.tar.gz'
if not path.exists():
    with urllib.request.urlopen('https://codeload.github.com/zaerl/mojibake/tar.gz/refs/tags/v0.3.6',timeout=60) as response:
        path.write_bytes(response.read())
assert hashlib.sha256(path.read_bytes()).hexdigest() == '156bb5c0c1f1265c5d75f4ef53ff4aab09c368e358b05f4f780ba6ec2575fed3'
with tarfile.open(path) as source:
    source.extractall(root, filter='data')
PY
mkdir -p "$work/deps/include/mojibake"
cp "$work/deps/mojibake-0.3.6/src/"*.h "$work/deps/include/mojibake/"
epoch=$(git -C "$repo/refs/muos/frontend" show -s --format=%ct "$revision")
podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
    --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev -v "$work:/work:rw,Z" \
    -w /work/source -e SOURCE_DATE_EPOCH="$epoch" "$(cat "$work/toolchain.iid")" sh -eu -c '
    mkdir -p ../deps/objects
    for source in ../deps/mojibake-0.3.6/src/*.c; do
        object="../deps/objects/$(basename "$source" .c).o"
        aarch64-linux-gnu-gcc -std=c11 -O2 -march=armv8-a -fPIE -ffile-prefix-map=/work=. -I../deps/mojibake-0.3.6/src -c "$source" -o "$object"
    done
    aarch64-linux-gnu-ar rcs ../deps/libmojibake.a ../deps/objects/*.o
    make -f phase3-menu.mk -j6
    aarch64-linux-gnu-gcc -std=c11 -D_GNU_SOURCE -O2 -march=armv8-a -fPIE -D_FORTIFY_SOURCE=3 -fstack-protector-strong -I. module/muvarctl.c common/config/var_store.c -pie -Wl,-z,relro,-z,now -o ../muvarctl
    for binary in ../phase3-menu ../muvarctl; do
        aarch64-linux-gnu-readelf -h -l -d -n --version-info "$binary" > "$binary.elf.txt"
        aarch64-linux-gnu-readelf --dyn-syms --wide "$binary" > "$binary.symbols.txt"
    done
    cp /usr/local/share/phase3-packages.txt ../packages.txt
    aarch64-linux-gnu-gcc --version > ../compiler.txt
    ' > "$work/compile.log" 2>&1
python3 "$repo/port/scripts/prepare-phase3-assets.py" > "$work/assets-prepare.log" 2>&1
mkdir -p "$work/staging/opt/muos/frontend"
cp "$work/phase3-menu" "$work/muvarctl" "$work/staging/opt/muos/frontend/"
# Reuse the exact input artifact already validated natively in Phase 2.
expected=7cf6f81e83d6033ce929b8741fae3d494916b8ac5e4875e92d2c9b63964ff96a
actual=$(sha256sum "$repo/dist/phase2-input/muinput")
[[ ${actual%% *} == "$expected" ]]
cp "$repo/dist/phase2-input/muinput" "$work/staging/opt/muos/frontend/muinput"
cp "$work/phase3-menu" "$work/muvarctl" "$work/"*.elf.txt "$work/"*.symbols.txt "$work/packages.txt" "$work/compiler.txt" "$work/asset-manifest.json" "$output/"
cp "$work/frontend-source.tar" "$work/deps/mojibake-0.3.6.tar.gz" "$work/deps/mojibake-0.3.6/LICENSE" "$output/"
cp "$repo/port/patches/0003-frontend-r35s-panel0-board.patch" "$output/"
cp "$repo/port/scripts/phase3-device-session.py" "$repo/port/scripts/phase3-namespace.py" "$repo/port/scripts/phase2-device-session.py" "$output/"
tar --sort=name --mtime="@$epoch" --owner=0 --group=0 --numeric-owner -C "$work/staging" -czf "$output/staging.tar.gz" opt
tar --sort=name --mtime="@$epoch" --owner=0 --group=0 --numeric-owner -C "$repo" -czf "$output/port-source.tar.gz" \
    port/diagnostics/phase3-menu.c port/packaging/phase3-menu.mk port/packaging/phase3-toolchain.Containerfile \
    port/scripts/build-phase3-menu.sh port/scripts/prepare-phase3-assets.py port/scripts/phase3-device-session.py \
    port/scripts/phase3-namespace.py port/scripts/phase2-device-session.py port/device/rk-r35s-p0/staging-config.json
printf 'upstream_revision=%s\ntoolchain_image_id=%s\nsource_date_epoch=%s\n' "$revision" "$(cat "$work/toolchain.iid")" "$epoch" > "$output/build-manifest.txt"
printf 'runtime_status=see docs/analysis/phase3-native-menu.md; compilation does not establish runtime approval\n' >> "$output/build-manifest.txt"
sha256sum "$repo/port/diagnostics/phase3-menu.c" "$repo/port/packaging/phase3-menu.mk" \
    "$repo/port/packaging/phase3-toolchain.Containerfile" "$repo/port/scripts/build-phase3-menu.sh" \
    "$repo/port/scripts/prepare-phase3-assets.py" "$repo/port/scripts/phase3-device-session.py" \
    "$repo/port/scripts/phase3-namespace.py" "$repo/port/device/rk-r35s-p0/staging-config.json" >> "$output/build-manifest.txt"
(
    cd "$output"
    sha256sum phase3-menu muvarctl *.elf.txt *.symbols.txt packages.txt compiler.txt asset-manifest.json \
        frontend-source.tar mojibake-0.3.6.tar.gz LICENSE *.patch staging.tar.gz port-source.tar.gz \
        phase3-device-session.py phase3-namespace.py phase2-device-session.py build-manifest.txt > SHA256SUMS
    if [[ -f last-tested/phase3-menu ]]; then
        sha256sum last-tested/phase3-menu last-tested/phase3-menu.c >> SHA256SUMS
    fi
)
printf 'Phase 3 menu artifacts: %s\n' "$output"
