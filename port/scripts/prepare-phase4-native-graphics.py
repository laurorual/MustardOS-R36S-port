#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C03: small graphics overlay on the seedless C02 host blueprint, not live SD."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,tempfile

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
base=work/'linux-diagnostic/entropy.rg3vmy8n';meta=json.loads((base/'manifest.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(base/'rootfs.ext4')==meta['rootfs_sha256'] and meta['host_audit_passed']
assert not (base/'extracted/var/lib/muos-seedrng').exists()
stage=Path(tempfile.mkdtemp(prefix='native-graphics.',dir=work/'linux-diagnostic'));assets=stage/'assets';assets.mkdir()
shutil.copyfile(base/'rootfs.ext4',stage/'rootfs.ext4')
bootstrap=(base/'assets/sbin_muos-ext4-diag').read_text()
guard='[ "$(cat /etc/muos-services-diagnostic)" = MUOS-R35S-INIT-P4-C02 ] || fail \'C02 marker missing\''
assert guard in bootstrap
bootstrap=bootstrap.replace(guard,guard+'\n[ "$(cat /etc/muos-graphics-diagnostic 2>/dev/null)" = MUOS-R35S-GRAPHICS-P4-C03 ] || fail \'C03 marker missing\'')
run=(base/'assets/usr_libexec_muos-c01-run').read_text().replace('C02','C03').replace('MUOS-R35S-INIT-P4-C03','MUOS-R35S-GRAPHICS-P4-C03').replace('/etc/muos-services-diagnostic','/etc/muos-graphics-diagnostic').replace('/run/muos/c02','/run/muos/c03').replace('DIAG04','DIAG05')
run=run.replace('C03: RNG_READY / INPUT OK / SEED SAVED','C03: EGL / SDL / INPUT OK')
run=run.replace('No frontend, audio or network started.','Graphics ended. No frontend, audio or network.')
# Keep the C02 service marker for S05; add a C03-specific activation guard.
function='''c03_graphics() {
    [ -c /dev/dri/card0 ] && [ -c /dev/mali0 ] || return 1
    echo 'DRM_BEFORE'
    /usr/libexec/muos-run-bounded 5 /usr/libexec/muos-drm-mode-probe > "$state/drm-before.txt" 2>&1 || return 1
    cat "$state/drm-before.txt"
    grep -q 'size=640x480' "$state/drm-before.txt" || return 1
    echo 'EGL_BEGIN'
    /usr/libexec/muos-run-bounded 10 /usr/libexec/muos-egl-context || return 1
    echo 'SDL_BEGIN'
    sdl_status=0
    /usr/libexec/muos-run-bounded 45 env SDL_VIDEODRIVER=KMSDRM SDL_VIDEO_EGL_DRIVER=libEGL.so SDL_VIDEO_GL_DRIVER=libGLESv2.so LD_BIND_NOW=1 /usr/libexec/muos-sdl-video-probe 30 || sdl_status=$?
    echo "SDL_COMMAND_STATUS=$sdl_status"
    echo 'DRM_AFTER'
    /usr/libexec/muos-run-bounded 5 /usr/libexec/muos-drm-mode-probe > "$state/drm-after.txt" 2>&1 || return 1
    cat "$state/drm-after.txt"
    cmp -s "$state/drm-before.txt" "$state/drm-after.txt" || return 1
    echo 'DRM_MODE_RESTORED=1'
    [ "$sdl_status" = 0 ] || return 1
    echo 'C03_GRAPHICS_STATUS=0'
}
'''
anchor="{\n    echo 'MUOS-R35S-GRAPHICS-P4-C03';"
assert anchor in run
run=run.replace(anchor,function+'''if [ "$status" = 0 ]; then
    c03_graphics > "$state/graphics.log" 2>&1 || status=1
fi
'''+anchor)
anchor="    echo 'MAPPING'; cat"
assert anchor in run
run=run.replace(anchor,"    echo 'GRAPHICS'; cat \"$state/graphics.log\" 2>/dev/null\n"+anchor)
payload={'sbin/muos-ext4-diag':bootstrap,'usr/libexec/muos-c01-run':run,'etc/muos-graphics-diagnostic':'MUOS-R35S-GRAPHICS-P4-C03\n'}
for name,data in payload.items():(assets/name.replace('/','_')).write_text(data)
container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z','-e','STAGE_REL='+str(stage.relative_to(work)),(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c']
compile=r'''
stage=/work/$STAGE_REL
sdk=/work/graphics-config/output/host
export PKG_CONFIG_LIBDIR=$sdk/aarch64-buildroot-linux-gnu/sysroot/usr/lib/pkgconfig:$sdk/aarch64-buildroot-linux-gnu/sysroot/usr/share/pkgconfig
export PKG_CONFIG_SYSROOT_DIR=$sdk/aarch64-buildroot-linux-gnu/sysroot
cc=$sdk/bin/aarch64-buildroot-linux-gnu-gcc
flags="-std=c11 -D_GNU_SOURCE -O2 -Wall -Wextra -Werror -march=armv8-a -mtune=cortex-a35 -fPIE -pie -Wl,-z,relro,-z,now"
"$cc" $flags /port/probes/phase4-egl-context.c $("$sdk/bin/pkg-config" --cflags --libs egl glesv2 gbm) -o "$stage/assets/usr_libexec_muos-egl-context"
"$cc" $flags /port/diagnostics/sdl-video-probe.c $("$sdk/bin/pkg-config" --cflags --libs sdl2) -o "$stage/assets/usr_libexec_muos-sdl-video-probe"
"$cc" $flags /port/diagnostics/drm-mode-probe.c $("$sdk/bin/pkg-config" --cflags --libs libdrm) -o "$stage/assets/usr_libexec_muos-drm-mode-probe"
'''
with (stage/'compile.log').open('w') as f:subprocess.run(container+[compile],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=40)
names=['sbin/muos-ext4-diag','usr/libexec/muos-egl-context','usr/libexec/muos-sdl-video-probe','usr/libexec/muos-drm-mode-probe','usr/libexec/muos-c01-run','etc/muos-graphics-diagnostic']
entries=[];commands=[]
for name in names:
    p=assets/name.replace('/','_');old=base/'extracted'/name;mode=0o644 if name.startswith('etc/') else 0o755
    entries.append({'path':name,'asset':p.name,'sha256':sha(p),'old_sha256':sha(old) if old.is_file() else None,'mode':mode})
    if old.exists():commands.append('rm /'+name)
    commands += [f'write assets/{p.name} /{name}',f'set_inode_field /{name} mode 0{mode|0o100000:o}']
(stage/'debugfs.commands').write_text('\n'.join(commands)+'\n')
audit=r'''
cd /work/$STAGE_REL
sdk=/work/graphics-config/output/host
debugfs -w -f debugfs.commands rootfs.ext4 > debugfs.log 2>&1
e2fsck -fn rootfs.ext4 > fsck.log 2>&1
mkdir extracted
"$sdk/bin/fakeroot" debugfs -R "rdump / $PWD/extracted" rootfs.ext4 > extract.log 2>&1
root=$PWD/extracted
for name in muos-egl-context muos-sdl-video-probe muos-drm-mode-probe; do
 readelf -h -l -d -V "$root/usr/libexec/$name" > "$name-elf.txt"
 qemu-aarch64 -cpu cortex-a35 -L "$root" -E LD_BIND_NOW=1 "$root/lib/ld-linux-aarch64.so.1" --list "$root/usr/libexec/$name" > "$name-loader.txt" 2>&1
done
qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/usr/libexec/muos-sdl-video-probe" --info > sdl-info.txt
for script in sbin/muos-ext4-diag usr/libexec/muos-c01-run; do
 qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh -n "$root/$script"
done
qemu-aarch64 -cpu cortex-a35 -L "$root" -E LD_BIND_NOW=1 /work/graphics-config/audit/graphics-contract > link-contract.txt 2>&1
'''
with (stage/'audit.log').open('w') as f:subprocess.run(container+[audit],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=100)
for e in entries:assert sha(stage/'extracted'/e['path'])==e['sha256']
assert not (stage/'extracted/var/lib/muos-seedrng').exists()
assert 'GRAPHICS_LINK_LOAD_CONTRACT=OK' in (stage/'link-contract.txt').read_text()
assert 'available_video_driver=KMSDRM' in (stage/'sdl-info.txt').read_text()
# Execute the actual orchestration with fixture executables: successful EGL,
# failing EGL (SDL must not run), failing SDL (mode check must still run).
fixtures={}
for case in ['success','egl-failure','sdl-failure','mode-mismatch']:
    f=stage/('fixture-'+case);f.mkdir();binpath=f/'probe';binpath.write_text('''#!/bin/sh
name=$1; shift
echo "$name" >> "$FIXTURE/calls"
case "$name" in
 *drm-mode-probe) echo 'crtc=1 size=640x480'; if [ "$CASE" = mode-mismatch ] && [ -f "$FIXTURE/mode-called" ]; then echo mismatch; fi; touch "$FIXTURE/mode-called" ;;
 *egl-context) [ "$CASE" != egl-failure ] ;;
 *sdl-video-probe) [ "$CASE" != sdl-failure ] ;;
esac
''');binpath.chmod(0o755)
    bounded=f/'bounded';bounded.write_text('#!/bin/sh\nshift\ncase "$1" in env) shift; while [ "$#" -gt 0 ] && [ "${1#*=}" != "$1" ]; do shift; done ;; esac\nexec "$FIXTURE/probe" "$@"\n');bounded.chmod(0o755)
    fixture=function.replace('[ -c /dev/dri/card0 ] && [ -c /dev/mali0 ] || return 1','true').replace('/usr/libexec/muos-run-bounded',str(bounded))
    test=fixture+'\nstate=$FIXTURE\nc03_graphics\n'
    x=subprocess.run(['sh','-c',test],env={**os.environ,'CASE':case,'FIXTURE':str(f)},text=True,capture_output=True)
    assert (x.returncode==0)==(case=='success'),(case,x.stdout,x.stderr)
    calls=(f/'calls').read_text().splitlines()
    assert len(calls)==(2 if case=='egl-failure' else 4),(case,calls)
    fixtures[case]={'expected_outcome_passed':True,'exit':x.returncode,'calls':calls}
required=['usr/libexec/muos-entropy-functions','etc/init.d/S05muos-entropy','usr/lib/libmali-bifrost-g31-rxp0-gbm.so','usr/lib/libSDL2-2.0.so.0.3000.12']
plan={'experiment':'MUOS-R35S-GRAPHICS-P4-C03','authorized_secondary_c03_install':True,'installer_sha256':sha(repo/'port/scripts/install-phase4-service-diagnostic.py'),'entries':entries,'unchanged_required':{name:sha(base/'extracted'/name) for name in required}}
(stage/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
record={**plan,'scope':'own kernel EGL readback then 30s SDL KMSDRM; no frontend/audio/network','base_manifest_sha256':sha(base/'manifest.json'),'rootfs_sha256':sha(stage/'rootfs.ext4'),'host_audit_passed':True,'orchestration_fixtures':fixtures,'seed_material_included':False,'native_graphics_tested':False,'kernel_dtb_bootloader_partition_changed':False,'proprietary_provider_redistribution_approved':False,'port_inputs':{name:sha(repo/name) for name in ['port/scripts/prepare-phase4-native-graphics.py','port/scripts/install-phase4-service-diagnostic.py','port/probes/phase4-egl-context.c','port/diagnostics/sdl-video-probe.c','port/diagnostics/drm-mode-probe.c']}}
(stage/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');(work/'linux-diagnostic/latest-native-graphics').write_text(str(stage)+'\n')
print('C03 audited; no native GPU runtime approval yet:',stage)
