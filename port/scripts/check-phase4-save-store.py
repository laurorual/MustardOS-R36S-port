#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build the bounded save store and exercise synthetic transactions/failures."""
from pathlib import Path
import json,re,shutil,subprocess,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'save-store';area.mkdir(exist_ok=True)
stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area));stage.chmod(0o755);rel='/work/'+str(stage.relative_to(work))
sources=[repo/'port/utils/muos-save-store.c',repo/'port/diagnostics/phase4-save-store-check.py',Path(__file__)]
for p in sources[:2]:shutil.copyfile(p,stage/p.name)
code=f'''
sdk=/work/graphics-config/output/host
cc="$sdk/bin/aarch64-buildroot-linux-gnu-gcc"
flags='-O2 -mcpu=cortex-a35 -std=c11 -Wall -Wextra -Werror -fstack-protector-strong -fPIE -pie -Wl,-z,relro,-z,now'
"$cc" $flags {rel}/muos-save-store.c -lz -o {rel}/muos-save-store
"$cc" $flags -DSAVE_STORE_TEST {rel}/muos-save-store.c -lz -o {rel}/muos-save-store-test
'''
(stage/'build.sh').write_text(code)
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
     '--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z',
     (work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',code]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
assert r.returncode==0,(stage,r.stderr[-2500:])
fixture='export C52_ROOT=/sysroot C52_BINARY=/payload/muos-save-store C52_TEST_BINARY=/payload/muos-save-store-test\npython3 /payload/phase4-save-store-check.py\n'
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
     '--userns=keep-id','--user=0','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{stage}:/payload:ro,z',
     '-v',f'{work}/rootfs-candidate/composition.w59vz7vo/target:/sysroot:ro,z',
     (work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',fixture]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/('check.'+n)).write_text(v)
assert r.returncode==0,(stage,r.stderr[-2500:])
cases=re.findall(r'^C52_FIXTURE_PASS (.*)$',r.stdout,re.M)
assert len(cases)>=30 and f'C52_FIXTURES_PASSED count={len(cases)}' in r.stdout
assert (work/'graphics-config/output/.config').read_bytes()==(work/'network-tools/baseline.config').read_bytes()
report={'passed':True,'experiment':'C52_SAVE_STORE','case_count':len(cases),'cases':cases,
        'binary_sha256':sha(stage/'muos-save-store'),'test_binary_sha256':sha(stage/'muos-save-store-test'),
        'private_content_used':False,'native_or_real_ext4_tested':False,'SDK_config_unchanged':True,
        'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-checks').write_text(str(stage)+'\n')
print('C52 save store QEMU transactions passed:',len(cases),stage)
