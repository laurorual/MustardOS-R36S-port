#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C22 real Buildroot Kconfig isolation, without changing the shared SDK."""
from pathlib import Path
import hashlib,json,subprocess,tempfile

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'runtime-session'
stage=Path(tempfile.mkdtemp(prefix='package-kconfig.',dir=area));baseline=work/'network-tools/baseline.config'
assert (work/'graphics-config/output/.config').read_bytes()==baseline.read_bytes()
rel=lambda p:'/work/'+str(p.relative_to(work));out=stage/'output'
script=f'''set -eu
make -C /work/buildroot O={rel(out)} BR2_EXTERNAL=/port/buildroot BR2_DEFCONFIG=/work/network-tools/baseline.config defconfig
! grep -qx 'BR2_PACKAGE_MUOS_R35S_SESSION=y' {rel(out)}/.config
echo PASS_default_off
/work/buildroot/utils/config --file {rel(out)}/.config --enable BR2_PACKAGE_MUOS_CORE --enable BR2_PACKAGE_MUOS_R35S_PROFILE --enable BR2_PACKAGE_MUOS_R35S_SESSION --disable BR2_PACKAGE_MUOS_R35S_BOOT
make -C /work/buildroot O={rel(out)} BR2_EXTERNAL=/port/buildroot olddefconfig
grep -qx 'BR2_PACKAGE_MUOS_R35S_SESSION=y' {rel(out)}/.config
! grep -qx 'BR2_PACKAGE_MUOS_R35S_BOOT=y' {rel(out)}/.config
cp {rel(out)}/.config {rel(stage)}/opt-in.config
echo PASS_session_without_boot
/work/buildroot/utils/config --file {rel(out)}/.config --disable BR2_PACKAGE_UTIL_LINUX_MOUNT --enable BR2_PACKAGE_MUOS_R35S_SESSION
make -C /work/buildroot O={rel(out)} BR2_EXTERNAL=/port/buildroot olddefconfig
! grep -qx 'BR2_PACKAGE_UTIL_LINUX_MOUNT=y' {rel(out)}/.config
! grep -qx 'BR2_PACKAGE_MUOS_R35S_SESSION=y' {rel(out)}/.config
echo PASS_missing_mount_disables_session
/work/buildroot/utils/config --file {rel(out)}/.config --enable BR2_PACKAGE_UTIL_LINUX_MOUNT --disable BR2_PACKAGE_UTIL_LINUX_BINARIES --enable BR2_PACKAGE_MUOS_R35S_SESSION
make -C /work/buildroot O={rel(out)} BR2_EXTERNAL=/port/buildroot olddefconfig
! grep -qx 'BR2_PACKAGE_UTIL_LINUX_BINARIES=y' {rel(out)}/.config
! grep -qx 'BR2_PACKAGE_MUOS_R35S_SESSION=y' {rel(out)}/.config
echo PASS_missing_basic_utilities_disables_session
'''
args=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-c',script]
r=subprocess.run(args,capture_output=True,text=True,timeout=60)
(stage/'kconfig.sh').write_text(script);(stage/'stdout').write_text(r.stdout);(stage/'stderr').write_text(r.stderr)
assert r.returncode==0,(stage,r.stdout[-3000:],r.stderr)
assert (work/'graphics-config/output/.config').read_bytes()==baseline.read_bytes()
cases=[s for s in r.stdout.splitlines() if s.startswith('PASS_')];assert len(cases)==4
report={'passed':True,'cases':cases,'SDK_baseline_unchanged':True,'full_image_built':False,'sources':{str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),repo/'port/buildroot/package/muos-r35s-session/Config.in']}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-package-kconfig').write_text(str(stage)+'\n')
print('C22 Kconfig4 cases passed:',stage)
