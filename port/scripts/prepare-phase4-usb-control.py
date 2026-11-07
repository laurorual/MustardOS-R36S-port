#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build/test the fixed IN-only USB probe with the existing AArch64 SDK."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,tempfile
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'network-warm'
assert (work/'graphics-config/output/.config').read_bytes()==(work/'network-tools/baseline.config').read_bytes()
stage=Path(tempfile.mkdtemp(prefix='control-build.',dir=area))
for n in ['usb-control-probe.c','usb-control-probe-test.c']:shutil.copyfile(repo/'port/diagnostics'/n,stage/n)
root=work/'linux-diagnostic/network-recovery.zz7sq2ve/extracted'
rel=lambda p:'/work/'+str(p.relative_to(work))
container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
           '--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z',
           (work/'rootfs-container.iid').read_text().strip()]
flags='-O2 -g0 -march=armv8-a -mtune=cortex-a35 -std=c11 -Wall -Wextra -Werror -fPIE -pie -Wl,-z,relro,-z,now'
code='set -eu\ncd '+rel(stage)+'\n'
cc='/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc'
code+=f'{cc} {flags} usb-control-probe.c -o usb-control-probe\n{cc} {flags} usb-control-probe-test.c -o usb-control-probe-test\n'
code+='readelf -h -l -d -n --version-info usb-control-probe > elf.txt\n'
code+=f'qemu-aarch64 -cpu cortex-a35 -L {rel(root)} -E LD_BIND_NOW=1 {rel(root/"lib/ld-linux-aarch64.so.1")} --inhibit-cache --library-path {rel(root/"lib")}:{rel(root/"usr/lib")} --list ./usb-control-probe > loader.txt\n'
for i in range(5):
    code+=f'qemu-aarch64 -cpu cortex-a35 -L {rel(root)} ./usb-control-probe-test {i} > fixture-{i}.stdout\n'
code+=f'set +e\nqemu-aarch64 -cpu cortex-a35 -L {rel(root)} ./usb-control-probe baseline > guard.stdout\ng=$?\nqemu-aarch64 -cpu cortex-a35 -L {rel(root)} ./usb-control-probe arbitrary > argument.stdout\na=$?\nset -e\n[ "$g:$a" = 64:2 ]\n'
r=subprocess.run(container+['sh','-c',code],text=True,capture_output=True,timeout=40)
(stage/'build.stdout').write_text(r.stdout);(stage/'build.stderr').write_text(r.stderr)
assert r.returncode==0,r.stderr
elf=(stage/'elf.txt').read_text();assert 'AArch64' in elf and '/lib/ld-linux-aarch64.so.1' in elf
assert 'Shared library: [libc.so.6]' in elf
for i in range(5):
    text=(stage/f'fixture-{i}.stdout').read_text()
    lines=text.splitlines();reads=[s for s in lines if s.startswith('READ=')]
    assert len(reads)==(1 if i==3 else 7)
    for s in reads:assert re.fullmatch(r'READ=[a-z_]+ RC=-?[0-9]+ EXPECTED=[0-9]+ ELAPSED_MS=[0-9]+ MATCH=-?1|READ=[a-z_]+ RC=-?[0-9]+ EXPECTED=[0-9]+ ELAPSED_MS=[0-9]+ MATCH=0',s),s
    if i in [0,1,2,4]:assert f'READ_FAILURES={[0,1,7,0,1][i]}' in text
    assert not any(v in text for v in ['a5a5','SSID','MAC=','PSK'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'host_passed':True,'AArch64_QEMU_cases':7,'synthetic_transfer_cases':5,'board_and_argument_refusals':2,
        'IN_requests_only_fixed_plan':True,'runtime_loader':'/lib/ld-linux-aarch64.so.1','needed':re.findall(r'Shared library: \[(.*?)\]',elf),
        'compiler_flags':flags,'no_target_device_or_USB_used':True,'binary_sha256':sha(stage/'usb-control-probe'),
        'sources':{str(p.relative_to(repo)):sha(p) for p in [repo/'port/diagnostics/usb-control-probe.c',repo/'port/diagnostics/usb-control-probe-test.c',Path(__file__)]}}
(stage/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-control-build').write_text(str(stage)+'\n')
print('C16 fixed USB IN probe:7 AArch64 checks and loader passed;',stage)
