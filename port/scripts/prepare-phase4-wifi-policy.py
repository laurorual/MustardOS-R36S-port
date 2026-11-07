#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Verify the real Wi-Fi-only recipe and isolated Kconfig without rebuilding an image."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'network-warm'
stage=Path(tempfile.mkdtemp(prefix='wifi-policy-build.',dir=area));source=stage/'source'
shutil.copytree(repo/'port/device/rk-r35s-p0/wifi-only',source)
baseline=work/'network-tools/baseline.config'
assert (work/'graphics-config/output/.config').read_bytes()==baseline.read_bytes()
rel=lambda p:'/work/'+str(p.relative_to(work))
target=stage/'target';harness=stage/'recipe.mk'
harness.write_text(f'TARGET_DIR := {rel(target)}\nINSTALL := install\nBR2_EXTERNAL_MUOS_R35S_PATH := /port/buildroot\ngeneric-package =\ninclude /port/buildroot/package/muos-r35s-wifi-only/muos-r35s-wifi-only.mk\n{rel(source/".installed")}:\n\t$(MUOS_R35S_WIFI_ONLY_INSTALL_TARGET_CMDS)\n\ttouch $@\n')
args=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id',
      '--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z',
      (work/'rootfs-container.iid').read_text().strip()]
r=subprocess.run(args+['make','-f',rel(harness)],text=True,capture_output=True,timeout=25)
(stage/'recipe.stdout').write_text(r.stdout);(stage/'recipe.stderr').write_text(r.stderr);assert r.returncode==0,r.stderr
files=sorted(p for p in target.rglob('*') if p.is_file())
assert [str(p.relative_to(target)) for p in files]==['etc/modprobe.d/90-muos-r35s-wifi-only.conf','usr/share/licenses/muos-r35s-wifi-only/LICENSE']
assert (target/'etc/modprobe.d/90-muos-r35s-wifi-only.conf').read_bytes()==(source/'90-muos-r35s-wifi-only.conf').read_bytes()
assert (source/'LICENSE').read_bytes()==(repo/'port/LICENSE').read_bytes()
assert all(p.stat().st_mode&0o777==0o644 for p in files)
out=stage/'kconfig'
code=f'''set -eu
make -C /work/buildroot O={rel(out)} BR2_EXTERNAL=/port/buildroot BR2_DEFCONFIG=/work/network-tools/baseline.config defconfig
if grep -q '^BR2_PACKAGE_MUOS_R35S_WIFI_ONLY=y$' {rel(out)}/.config;then exit 1;fi
/work/buildroot/utils/config --file {rel(out)}/.config --enable BR2_PACKAGE_MUOS_R35S_WIFI_ONLY
make -C /work/buildroot O={rel(out)} BR2_EXTERNAL=/port/buildroot olddefconfig
grep -qx 'BR2_PACKAGE_MUOS_R35S_WIFI_ONLY=y' {rel(out)}/.config
'''
r=subprocess.run(args+['sh','-c',code],text=True,capture_output=True,timeout=45)
(stage/'kconfig.stdout').write_text(r.stdout);(stage/'kconfig.stderr').write_text(r.stderr);assert r.returncode==0,r.stderr
assert (work/'graphics-config/output/.config').read_bytes()==baseline.read_bytes()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs=[Path(__file__),repo/'port/buildroot/Config.in',repo/'port/device/rk-r35s-p0/phase4-wifi-only.fragment',
        *sorted((repo/'port/buildroot/package/muos-r35s-wifi-only').iterdir()),
        *sorted((repo/'port/device/rk-r35s-p0/wifi-only').iterdir())]
meta={'host_passed':True,'actual_install_macro_passed':True,'only_two_files_no_init_or_libraries':True,
      'Kconfig_default_off_and_opt_in_passed':True,'SDK_config_unchanged':True,'full_image_built':False,
      'payload':{str(p.relative_to(target)):{'sha256':sha(p),'mode':'644'} for p in files},
      'sources':{str(p.relative_to(repo)):sha(p) for p in inputs}}
(stage/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n');(area/'latest-wifi-policy-build').write_text(str(stage)+'\n')
print('Wi-Fi-only recipe, two-file payload and isolated Kconfig passed;',stage)
