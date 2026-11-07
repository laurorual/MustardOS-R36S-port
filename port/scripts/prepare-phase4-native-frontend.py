#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C04 diagnostic: reuse the installed S99/supervisor/frontend without rebuilding."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
base=work/'linux-diagnostic/native-graphics.6qz6i3e7';meta=json.loads((base/'manifest.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(base/'rootfs.ext4')==meta['rootfs_sha256']
assert not (base/'extracted/var/lib/muos-seedrng').exists()
stage=Path(tempfile.mkdtemp(prefix='native-frontend.',dir=work/'linux-diagnostic'));assets=stage/'assets';assets.mkdir()
shutil.copyfile(base/'rootfs.ext4',stage/'rootfs.ext4')
bootstrap=(base/'assets/sbin_muos-ext4-diag').read_text().replace('/etc/muos-graphics-diagnostic','/etc/muos-frontend-diagnostic').replace('MUOS-R35S-GRAPHICS-P4-C03','MUOS-R35S-FRONTEND-P4-C04').replace("'C03 marker missing'","'C04 marker missing'")
run=(base/'assets/usr_libexec_muos-c01-run').read_text().replace('C03','C04').replace('MUOS-R35S-GRAPHICS-P4-C04','MUOS-R35S-FRONTEND-P4-C04').replace('/etc/muos-graphics-diagnostic','/etc/muos-frontend-diagnostic').replace('/run/muos/c03','/run/muos/c04').replace('DIAG05','DIAG06')
a=run.index('c03_graphics() {');z=run.index("{\n    echo 'MUOS-R35S-FRONTEND-P4-C04'",a)
run=run[:a]+(repo/'port/device/rk-r35s-p0/frontend-diagnostic/session.sh').read_text()+'''\nif [ "$status" = 0 ]; then
    c04_frontend > "$state/frontend.log" 2>&1 || status=1
fi
'''+run[z:]
run=run.replace("echo 'GRAPHICS'; cat \"$state/graphics.log\"", "echo 'FRONTEND'; cat \"$state/frontend.log\"")
run=run.replace('C04: EGL / SDL / INPUT OK','C04: FRONTEND / INPUT OK').replace('Graphics ended. No frontend, audio or network.','Frontend stopped. No audio or network.')
payload={'sbin/muos-ext4-diag':bootstrap,'usr/libexec/muos-c01-run':run,'etc/muos-frontend-diagnostic':'MUOS-R35S-FRONTEND-P4-C04\n'}
entries=[];commands=[]
for name,text in payload.items():
    p=assets/name.replace('/','_');p.write_text(text);old=base/'extracted'/name;mode=0o644 if name.startswith('etc/') else 0o755
    entries.append({'path':name,'asset':p.name,'sha256':sha(p),'old_sha256':sha(old) if old.is_file() else None,'mode':mode})
    if old.exists():commands.append('rm /'+name)
    commands += [f'write assets/{p.name} /{name}',f'set_inode_field /{name} mode 0{mode|0o100000:o}']
(stage/'debugfs.commands').write_text('\n'.join(commands)+'\n')
container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z','-e','STAGE_REL='+str(stage.relative_to(work)),(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c']
audit=r'''
cd /work/$STAGE_REL
debugfs -w -f debugfs.commands rootfs.ext4 > debugfs.log 2>&1
e2fsck -fn rootfs.ext4 > fsck.log 2>&1
mkdir extracted
/work/graphics-config/output/host/bin/fakeroot debugfs -R "rdump / $PWD/extracted" rootfs.ext4 > extract.log 2>&1
root=$PWD/extracted
for script in sbin/muos-ext4-diag usr/libexec/muos-c01-run; do
 qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh -n "$root/$script"
done
for file in opt/muos/frontend/muxfrontend usr/libexec/muos-ui-supervisor; do
 name=${file##*/}
 readelf -h -l -d "$root/$file" > "$name-elf.txt"
 qemu-aarch64 -cpu cortex-a35 -L "$root" -E LD_BIND_NOW=1 "$root/lib/ld-linux-aarch64.so.1" --list "$root/$file" > "$name-loader.txt" 2>&1
done
'''
with (stage/'audit.log').open('w') as f:subprocess.run(container+[audit],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=100)
for e in entries:assert sha(stage/'extracted'/e['path'])==e['sha256']
assert not (stage/'extracted/var/lib/muos-seedrng').exists()
required=['usr/libexec/muos-entropy-functions','etc/init.d/S05muos-entropy','usr/lib/libmali-bifrost-g31-rxp0-gbm.so','usr/lib/libSDL2-2.0.so.0.3000.12','usr/libexec/muos-ui-supervisor','etc/init.d/S99muos-ui','opt/muos/frontend/muxfrontend','usr/libexec/muos-drm-mode-probe']
for name in required:assert sha(stage/'extracted'/name)==sha(base/'extracted'/name)
plan={'experiment':'MUOS-R35S-FRONTEND-P4-C04','authorized_secondary_c04_install':True,'installer_sha256':sha(repo/'port/scripts/install-phase4-service-diagnostic.py'),'entries':entries,'unchanged_required':{name:sha(base/'extracted'/name) for name in required}}
(stage/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
record={**plan,'scope':'75s supervised frontend on own kernel, audio/hotkeys disabled, temporary UI config bind','base_manifest_sha256':sha(base/'manifest.json'),'rootfs_sha256':sha(stage/'rootfs.ext4'),'host_audit_passed':True,'seed_material_included':False,'binaries_rebuilt':False,'native_frontend_tested':False,'kernel_dtb_bootloader_partition_changed':False,'port_inputs':{name:sha(repo/name) for name in ['port/scripts/prepare-phase4-native-frontend.py','port/device/rk-r35s-p0/frontend-diagnostic/session.sh','port/scripts/install-phase4-service-diagnostic.py']}}
(stage/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');(work/'linux-diagnostic/latest-native-frontend').write_text(str(stage)+'\n');print('C04 audited, native UI pending:',stage)
