#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C52 laboratory: build only, format a new regular image under build/."""
from pathlib import Path
import json,re,shutil,subprocess,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'save-store'
checks=Path((area/'latest-checks').read_text().strip());cr=json.loads((checks/'analysis.json').read_text());assert cr['passed']
for n,h in cr['source_sha256'].items():assert sha(repo/n)==h
source=repo/'port/diagnostics/phase4-save-store-ext4.c';parent=repo/'port/diagnostics/phase4-preferences-ext4.c'
def function(text,name):
 m=re.search(r'static [^\n]+\b'+name+r'\([^\n]*\) \{',text);assert m,name
 start=m.start();at=text.index('{',m.start());depth=1;end=at+1
 while depth:
  depth+=(text[end]=='{')-(text[end]=='}');end+=1
 return text[start:end]
guards=['interrupt','root_ro','owned','same_loop','option','ext4_mount','mount_image','unmount_image']
for name in guards:assert function(source.read_text(),name)==function(parent.read_text(),name),name
stage=Path(tempfile.mkdtemp(prefix='ext4.',dir=area));rel='/work/'+str(stage.relative_to(work))
shutil.copyfile(checks/'muos-save-store',stage/'muos-save-store');shutil.copyfile(source,stage/source.name)
transaction=repo/'port/device/rk-r35s-p0/save-store/transaction.sh'
audit=repo/'port/device/rk-r35s-p0/save-store/audit-data.sh'
for p in [transaction,audit]:subprocess.run(['sh','-n',str(p)],check=True);shutil.copyfile(p,stage/p.name)
code=f'''
cd {rel}
/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc -O2 -mcpu=cortex-a35 -std=c11 -Wall -Wextra -Werror -fPIE -pie -Wl,-z,relro,-z,now phase4-save-store-ext4.c -o phase4-save-store-ext4
readelf -h -l -n phase4-save-store-ext4 > elf.txt
test ! -e data.ext4
truncate -s 16777216 data.ext4
mke2fs -q -F -t ext4 -b 4096 -I 256 -m 0 -L MUOSSAVELAB -U 6d756f73-c052-4000-8000-000000000001 -O none,has_journal,ext_attr,resize_inode,dir_index,filetype,extent,sparse_super,large_file,uninit_bg,dir_nlink,extra_isize -E lazy_itable_init=0,lazy_journal_init=0 data.ext4
e2fsck -fn data.ext4 > fsck-before.txt 2>&1
'''
(stage/'build.sh').write_text(code)
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
     '--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z',
     (work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',code]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/('build.'+n)).write_text(v)
assert r.returncode==0,(stage,r.stderr[-2000:])
elf=(stage/'elf.txt').read_text();assert 'AArch64' in elf and 'ABI: 4.4.0' in elf
report={'passed':True,'experiment':'C52_PRIVATE_EXT4_LAB_BUILD','checks_stage':str(checks),'checks_analysis_sha256':sha(checks/'analysis.json'),
        'C19_ownership_guard_functions_unchanged':guards,'native_tested':False,
        'payload_sha256':{n:sha(stage/n) for n in ['muos-save-store','phase4-save-store-ext4','data.ext4','transaction.sh','audit-data.sh']},
        'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),source,parent,transaction,audit]}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-ext4-build').write_text(str(stage)+'\n')
print('C52 ext4 laboratory prepared:',stage)
