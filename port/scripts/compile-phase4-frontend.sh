#!/usr/bin/env bash
# Full core UI, no diagnostic dispatch wrappers, still private/no boot approval.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
[[ $(cat "$work/foundation/provider.exit") == 0 ]]
[[ $(podman inspect --format '{{.State.Running}}' muos-r35s-phase4-graphics) == false ]]
python3 - "$repo" "$work" <<'PY'
from pathlib import Path
import hashlib,io,json,shutil,subprocess,sys,tarfile
repo,work=map(Path,sys.argv[1:]);f=work/'foundation'
source=f/'frontend-source'
if not source.exists():
 archive=(work/'menu/frontend-source.tar').read_bytes()
 assert hashlib.sha256(archive).hexdigest()==json.loads((work/'menu/source-manifest.json').read_text())['frontend_archive_sha256']
 source.mkdir()
 with tarfile.open(fileobj=io.BytesIO(archive)) as stream:stream.extractall(source,filter='data')
 subprocess.run(['git','-C',str(source),'apply',str(repo/'port/patches/0003-frontend-r35s-panel0-board.patch')],check=True)
 shutil.copytree(work/'menu/deps',f/'deps',ignore=shutil.ignore_patterns('objects','libmojibake.a'))
patch=repo/'port/patches/0006-frontend-r35s-normalized-volume.patch'
if subprocess.run(['git','-C',str(source),'apply','--reverse','--check',str(patch)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
 subprocess.run(['git','-C',str(source),'apply',str(patch)],check=True)
shutil.copy2(repo/'port/packaging/phase4-frontend.mk',source/'phase4-frontend.mk')
if (f/'frontend-bin').exists():
 shutil.rmtree(f/'frontend-bin')  # Relink after changes to object grouping.
(f/'frontend-compile.exit').unlink(missing_ok=True)
PY
podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges --userns=keep-id \
 --memory=12g --pids-limit=2048 --tmpfs /tmp:rw,nosuid,nodev,size=2g -v "$work:/work:rw,z" \
 -w /work/foundation/frontend-source "$(cat "$work/rootfs-container.iid")" sh -eu -c '
 sdk=/work/graphics-config/output/host
 export PATH="$sdk/bin:$PATH"
 export PKG_CONFIG_LIBDIR="$sdk/aarch64-buildroot-linux-gnu/sysroot/usr/lib/pkgconfig:$sdk/aarch64-buildroot-linux-gnu/sysroot/usr/share/pkgconfig"
 export PKG_CONFIG_SYSROOT_DIR="$sdk/aarch64-buildroot-linux-gnu/sysroot"
 cc=$sdk/bin/aarch64-buildroot-linux-gnu-gcc
 mkdir -p ../deps/pic
 for src in ../deps/mojibake-0.3.6/src/*.c; do
  "$cc" -std=c11 -O2 -mcpu=cortex-a35 -fPIC -I../deps/mojibake-0.3.6/src -c "$src" -o "../deps/pic/$(basename "$src" .c).o"
 done
 "$sdk/bin/aarch64-buildroot-linux-gnu-ar" rcs ../deps/libmojibake-pic.a ../deps/pic/*.o
 make -f phase4-frontend.mk -j8 CC="$cc" PKG_CONFIG="$sdk/bin/pkg-config" CFLAGS="-O2 -mcpu=cortex-a35"
 ' > "$work/foundation/frontend-compile.log" 2>&1
printf '0\n' > "$work/foundation/frontend-compile.exit"
echo 'Core frontend linked without menu harness wrappers; runtime still requires validation'
