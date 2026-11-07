#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C112 resident four ELF assets plus original loader; no ROM in package."""
import json,os,re,subprocess,tempfile
from phase4_resident_assets import *
from phase4_backup_core import write_new,sync_dir

def main():
 os.umask(0o077);AREA.mkdir(mode=0o700,exist_ok=True)
 stage=Path(tempfile.mkdtemp(prefix='package.',dir=AREA));root=stage/'target'/PREFIX;root.mkdir(parents=True)
 for p in [stage/'target',stage/'target/usr',stage/'target/usr/libexec',root]:p.chmod(0o755)
 files=asset_files()
 for key,dest in ASSETS.items():
  data=files[key].read_bytes();require(data[:6]==b'\x7fELF\x02\x01' and int.from_bytes(data[18:20],'little')==183,'Qualified AArch64 ELF')
  write_new(root/dest,data)
 rel=lambda p:'/work/'+str(p.relative_to(WORK))
 code=f"/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc -O2 -mcpu=cortex-a35 -std=c11 -Wall -Wextra -Werror -fstack-protector-strong -fPIE -pie -Wl,-z,relro,-z,now /port/utils/muos-sync-path.c -o {rel(root/'sync-path')}\n"
 cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id',
 '--tmpfs','/tmp:rw,nosuid,nodev','-v',str(WORK)+':/work:rw,z','-v',str(REPO/'port')+':/port:ro,z',
 (WORK/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',code]
 result=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
 for n,v in [('build.sh',code),('build.stdout',result.stdout),('build.stderr',result.stderr),('build.exit',str(result.returncode)+'\n')]:write_new(stage/n,v.encode())
 require(result.returncode==0,'C112 sync-path compile failed')
 require((WORK/'graphics-config/output/.config').read_bytes()==(WORK/'network-tools/baseline.config').read_bytes(),'SDK unchanged')
 write_new(root/'functions.sh' ,(NATIVE/'functions.sh').read_bytes())
 write_new(root/'assets.tsv',''.join(sha(root/n)+' '+n+'\n' for n in ASSETS.values()).encode())
 guard=common();hashes={n:h for h,n in re.findall(r"printf '[^']+' ([0-9a-f]{64}) /([A-Za-z0-9_./+-]+) \| sha256sum -c - >/dev/null",guard)}
 dependency_names={**{parent.prep.PREFIX+'/'+n:644 for n in parent.prep.NAMES},
   'usr/libexec/muos-session/mount-namespace':755,'usr/libexec/muos-session/card-guard.sh':755,
   'usr/libexec/muos-session/data-functions.sh':755}
 survey=AREA/'session-payload.sha256'
 require(sha(survey)==hashes['usr/libexec/muos-session/payload.sha256'],'Qualified session manifest')
 session_files={n.lstrip('./'):h for h,n in (line.split() for line in survey.read_text().splitlines())}
 for n in dependency_names:
  if n not in hashes:
   leaf=n.removeprefix('usr/libexec/muos-session/');require(leaf in session_files,'Qualified session helper '+leaf);hashes[n]=session_files[leaf]
 require(all(n in hashes for n in dependency_names),'Qualified installed helpers')
 write_new(root/'dependencies.tsv',''.join(f'{hashes[n]} {mode} {n}\n' for n,mode in dependency_names.items()).encode())
 contract={'schema':112,'activation':'manual only','public_assets_resident':4,'host_runtime_uploads':0,
   'ROM_source':'MUOS/port-roms-v1/gb/private.gb on guarded p3','ROM_in_package':False,
   'runtime_data_mount':'private ro,noload,nosuid,nodev,noexec then unmount before C111 stage',
   'load_only':True,'autostart':False,'root_payload_modified':False,
   'licenses':{'helpers':'MIT','menu-libmuxmod.so':'GPL-3.0; existing C46 qualified patch','provider-probe':'existing qualified diagnostic; original source retained'}}
 write_new(root/'contract.json',(json.dumps(contract,indent=2)+'\n').encode())
 write_new(root/'LICENSE',(base.proof('manual-caller-installed')/'payload/LICENSE').read_bytes())
 write_new(root/'LICENSE.frontend',(REPO/'refs/muos/frontend/LICENSE').read_bytes())
 contents=NAMES[:-2];require(contents==['functions.sh','assets.tsv','dependencies.tsv','contract.json','LICENSE','LICENSE.frontend','runner','state-metadata','menu-libmuxmod.so','provider-probe','sync-path'],'Finite manifest')
 write_new(root/'payload.sha256',''.join(sha(root/n)+' '+n+'\n' for n in contents).encode())
 text=(NATIVE/'load.in.sh').read_text()
 for k,v in [('@MANIFEST_SHA@',sha(root/'payload.sha256')),('@FUNCTIONS_SHA@',sha(root/'functions.sh'))]:
  require(text.count(k)==1,'Finite loader token');text=text.replace(k,v)
 write_new(root/'load.sh',text.encode())
 for p in root.iterdir():
  p.chmod(0o644)
  if p.suffix=='.sh':subprocess.run(['sh','-n',str(p)],check=True)
 old=base.proof('manual-caller-installed')/'adapter'
 tx=(old/'transaction.sh').read_text().replace('c105','c112').replace('C105','C112')
 tx=tx.replace('usr/libexec/muos-caller',PREFIX).replace('= 17 ]','= 13 ]')
 tx=re.sub(r'c112_names\(\) \{.*?\n\}',lambda _:"c112_names() {\n    printf '%s\\n' "+' '.join(PREFIX+'/'+n for n in NAMES)+'\n}',tx,count=1,flags=re.S)
 native=(old/'native.sh').read_text().replace('c105','c112').replace('C105','C112')
 for n,t in [('transaction.sh',tx),('native.sh',native)]:write_new(stage/n,t.encode());subprocess.run(['sh','-n',str(stage/n)],check=True)
 _,prior=qualified()
 report={'passed':True,'schema':112,'files':13,'directories':1,'bytes':sum(p.stat().st_size for p in root.iterdir()),
  'package_files':{n:sha(root/n) for n in NAMES},'adapter_sha256':{n:sha(stage/n) for n in ['transaction.sh','native.sh']},
  'source_sha256':{str(p.relative_to(REPO)):sha(p) for p in sources()},
  'parent_proofs_sha256':{'prepared-capsule-session':sha(parent.proof('prepared-capsule-session')/'SHA256SUMS')},
  'ROM_seed_or_private_identity_included':False,'new_sync_ELF_built':True,'full_image_built':False,
  'asset_sources':{ASSETS[n]:{'path':str(p.relative_to(REPO)),'sha256':sha(p)} for n,p in files.items()}}
 write_new(stage/'analysis.json',(json.dumps(report,indent=2)+'\n').encode());sync_dir(stage)
 (AREA/'latest-package').write_text(str(stage)+'\n');sync_dir(AREA)
 print('C112 resident package:',report['bytes'],'bytes;',stage)
if __name__=='__main__':main()
