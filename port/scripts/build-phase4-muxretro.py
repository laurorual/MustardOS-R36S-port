#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C41 private muxretro build from the approved frontend snapshot and SDK."""
from pathlib import Path
import json
import shutil
import subprocess
import tarfile
import tempfile
from phase4_candidate import sha

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'muxretro'
baseline=work/'network-tools/baseline.config';config=work/'graphics-config/output/.config'
assert config.read_bytes()==baseline.read_bytes()
origin=json.loads((work/'menu/source-manifest.json').read_text())
archive=work/'menu/frontend-source.tar';assert sha(archive)==origin['frontend_archive_sha256']
rc_commit='2ad0b8672f68a48148620164510b963039e49eb1'
rc_archive=area/'cache'/('rcheevos-'+rc_commit+'.tar.gz')
assert sha(rc_archive)=='b8e3e834d15c327085154315c49dea85b081ad48592ba1740f323ac953e1bfec'
candidate=Path((work/'rootfs-candidate/latest-composition').read_text().strip())
assert candidate.resolve().is_relative_to(work/'rootfs-candidate')
cr=json.loads((candidate/'analysis.json').read_text());assert cr['passed']
libraries=candidate/'target/opt/muos/frontend/lib'
old_libraries={p.name:sha(p) for p in libraries.glob('*.so')}
stage=Path(tempfile.mkdtemp(prefix='build.',dir=area));(area/'latest-attempt').write_text(str(stage)+'\n')
source=stage/'source';source.mkdir()
with tarfile.open(archive) as stream:stream.extractall(source,filter='data')
patches=[repo/'port/patches'/name for name in ['0003-frontend-r35s-panel0-board.patch','0006-frontend-r35s-normalized-volume.patch','0007-muxretro-no-content.patch','0008-muxretro-buildroot-headers.patch']]
for patch in patches:
    subprocess.run(['git','-C',str(source),'apply','--check',str(patch)],check=True)
    subprocess.run(['git','-C',str(source),'apply',str(patch)],check=True)
with tarfile.open(rc_archive) as stream:stream.extractall(stage,filter='data')
rc=stage/('rcheevos-'+rc_commit)
assert 'MIT License' in (rc/'LICENSE').read_text()
include=stage/'include';include.mkdir()
for header in (rc/'include').glob('*.h'):shutil.copyfile(header,include/header.name)
shutil.copyfile(rc/'src/rc_libretro.h',include/'rc_libretro.h')
# Upstream's external prefix nests these headers; Buildroot installs them flat.
compat=include/'libarchive';compat.mkdir()
for name in ['archive.h','archive_entry.h']:(compat/name).write_text('#include <'+name+'>\n')
rel=lambda p:'/work/'+str(p.relative_to(work))
code=f'''sdk=/work/graphics-config/output/host
export PATH="$sdk/bin:$PATH"
export PKG_CONFIG_LIBDIR="$sdk/aarch64-buildroot-linux-gnu/sysroot/usr/lib/pkgconfig:$sdk/aarch64-buildroot-linux-gnu/sysroot/usr/share/pkgconfig"
export PKG_CONFIG_SYSROOT_DIR="$sdk/aarch64-buildroot-linux-gnu/sysroot"
cc=$sdk/bin/aarch64-buildroot-linux-gnu-gcc
rc={rel(rc)}
out={rel(stage)}
mkdir "$out/rc-objects"
for file in "$rc"/src/*.c "$rc"/src/rcheevos/*.c "$rc"/src/rapi/*.c "$rc"/src/rhash/*.c; do
 case "$file" in */rc_client_external.c|*/rc_client_raintegration.c) continue ;; esac
 name=$(basename "$(dirname "$file")")_$(basename "$file" .c)
 "$cc" -O2 -mcpu=cortex-a35 -fPIC -DRC_CLIENT_SUPPORTS_HASH -I"$rc/include" -I"$rc/src" -I"$rc/src/rcheevos" -I{rel(source)}/retro/core -c "$file" -o "$out/rc-objects/$name.o"
done
"$sdk/bin/aarch64-buildroot-linux-gnu-ar" rcs "$out/librcheevos.a" "$out"/rc-objects/*.o
pkgs="sdl2 SDL2_image SDL2_mixer SDL2_ttf harfbuzz freetype2 libpng libcurl libarchive openssl"
cflags="-O2 -mcpu=cortex-a35 -std=c11 -D_GNU_SOURCE -DTEST_IMAGE=1 -DRC_CLIENT_SUPPORTS_HASH -DMINIZ_NO_ZLIB_COMPATIBLE_NAMES -fPIE -fstack-protector-strong -MMD -MP -Wall -Werror=implicit-function-declaration -Werror=incompatible-pointer-types -Werror=return-type -Wno-unused-function -I{rel(include)} $($sdk/bin/pkg-config --cflags $pkgs)"
libs="-L{rel(libraries)} -lui -lmuxcom -lmuxmod -lplutosvg $out/librcheevos.a $($sdk/bin/pkg-config --libs $pkgs) -lEGL -lGLESv2 -lz -ldl -lm -lpthread -latomic"
make -C {rel(source)}/retro -j4 DEVICE=GENERIC ARCH_FLAGS=-mcpu=cortex-a35 CC="$cc" CFLAGS="$cflags" LDLIBS="$libs" LDFLAGS="-pie -Wl,-z,relro,-z,now -Wl,--enable-new-dtags,-rpath,/opt/muos/frontend/lib -Wl,--export-dynamic-symbol=eglGetProcAddress -Wl,-rpath-link,{rel(candidate/'target/lib')} -Wl,-rpath-link,{rel(candidate/'target/usr/lib')} -Wl,-rpath-link,{rel(libraries)}"
"$sdk/bin/aarch64-buildroot-linux-gnu-readelf" -h -l -d {rel(source)}/bin/muxretro
'''
(stage/'build.sh').write_text(code)
container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all',
           '--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev',
           '-v',f'{work}:/work:rw,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c']
result=subprocess.run(container+[code],capture_output=True,text=True,timeout=240)
for ext,value in [('stdout',result.stdout),('stderr',result.stderr),('exit',str(result.returncode)+'\n')]:
    (stage/('build.'+ext)).write_text(value)
assert config.read_bytes()==baseline.read_bytes()
assert {p.name:sha(p) for p in libraries.glob('*.so')}==old_libraries
assert result.returncode==0,(stage,result.stderr[-4000:])
binary=source/'bin/muxretro'
record={'passed':True,'experiment':'C41_MUXRETRO_PRIVATE_BUILD','frontend_revision':origin['frontend_revision'],
        'frontend_archive_sha256':sha(archive),'rcheevos_commit':rc_commit,'rcheevos_archive_sha256':sha(rc_archive),
        'binary_sha256':sha(binary),'SDK_baseline_preserved':True,'approved_frontend_libraries_preserved':old_libraries,
        'candidate_analysis_sha256':sha(candidate/'analysis.json'),'candidate_stage':str(candidate),
        'no_content_patch_applied':True,'device_written':False,'native_runtime_qualified':False,
        'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),*patches]}}
(stage/'analysis.json').write_text(json.dumps(record,indent=2)+'\n')
(area/'latest').write_text(str(stage)+'\n')
print('C41 private muxretro linked; runtime not qualified:',stage)
