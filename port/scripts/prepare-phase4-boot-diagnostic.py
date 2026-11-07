#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Stage the C12 one-shot candidate and exact targeted install plan on the host."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tarfile,tempfile
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'boot-order'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
coordinator=Path((area/'latest-coordinator').read_text().strip())
base=json.loads((coordinator/'manifest.json').read_text());assert base['host_passed']
for name,digest in base['source_sha256'].items():assert sha(repo/name)==digest,('stale coordinator',name)
checked=Path((area/'latest-diagnostic-checks').read_text().strip());checks=json.loads((checked/'report.json').read_text());assert checks['passed']
for name,digest in checks['sources'].items():assert sha(repo/name)==digest,('stale tests',name)
stage=Path(tempfile.mkdtemp(prefix='boot-test.',dir=area));payload=stage/'payload';tree=payload/'tree'
tree.mkdir(parents=True)
shutil.copytree(coordinator/'package/boot',tree/'usr/libexec/muos-boot')
shutil.copytree(coordinator/'package/session',tree/'usr/libexec/muos-session')
(tree/'etc/default').mkdir(parents=True)
(tree/'etc/default/muos-boot').write_text('enabled=1\nallow_power=0\nrecover_network=1\nsession_package=/usr/libexec/muos-session\nsession_config=/etc/default/muos-session\n')
(tree/'etc/default/muos-session').write_text('enabled=1\nlease_seconds=90\nprofile_dir=/usr/libexec/muos-session/profile\nprerequisites=/usr/libexec/muos-session/prerequisites.sha256\n')
original=coordinator/'root-layout/etc/inittab.c07';old=original.read_text()
assert old.count('::sysinit:/usr/libexec/muos-c07-run\n')==1
assert old.count('::shutdown:/usr/libexec/muos-c07-run stop\n')==1
selected=old.replace('::sysinit:/usr/libexec/muos-c07-run\n','::sysinit:/usr/libexec/muos-boot/select.sh start\n').replace('::shutdown:/usr/libexec/muos-c07-run stop\n','::shutdown:/usr/libexec/muos-boot/select.sh stop\n')
assert selected.replace('/usr/libexec/muos-boot/select.sh start','/usr/libexec/muos-c07-run').replace('/usr/libexec/muos-boot/select.sh stop','/usr/libexec/muos-c07-run stop')==old
(payload/'inittab.c07').write_text(old);(payload/'inittab.selected').write_text(selected)
(payload/'inittab-before.sha256').write_text(sha(original)+'\n')
# Keep all C11 prerequisite checks. Only the reviewed inittab dispatcher changes.
prereq=tree/'usr/libexec/muos-session/prerequisites.sha256'
lines=prereq.read_text().splitlines();assert sum(line.endswith('  /etc/inittab') for line in lines)==1
prereq.write_text('\n'.join(sha(payload/'inittab.selected')+'  /etc/inittab' if line.endswith('  /etc/inittab') else line for line in lines)+'\n')
session=tree/'usr/libexec/muos-session'
(session/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(session))+'\n' for p in sorted(session.rglob('*')) if p.is_file() and p!=session/'SHA256SUMS'))
share=tree/'usr/share/muos-r35s-boot';share.mkdir(parents=True)
shutil.copyfile(payload/'inittab.c07',share/'inittab.c07');shutil.copyfile(payload/'inittab.selected',share/'inittab.selected')
shutil.copyfile(repo/'port/LICENSE',share/'LICENSE')
shutil.copyfile(repo/'port/device/rk-r35s-p0/boot/contract.json',share/'contract.json')
shutil.copyfile(coordinator/'package/session/prerequisites.sha256',payload/'prerequisites.sha256')
files=sorted(p for p in tree.rglob('*') if p.is_file());modes={}
for p in files:
 assert not p.is_symlink()
 name=str(p.relative_to(tree));mode=0o600 if name.startswith('etc/default/') else 0o755 if p.stat().st_mode&0o111 else 0o644
 p.chmod(mode);modes[name]=format(mode,'o')
(payload/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(tree))+'\n' for p in files))
(payload/'MODES').write_text(''.join(modes[str(p.relative_to(tree))]+' '+str(p.relative_to(tree))+'\n' for p in files))
for n in ['install.sh','install-functions.sh']:shutil.copyfile(repo/'port/device/rk-r35s-p0/boot-diagnostic'/n,stage/n)
container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z',(work/'rootfs-container.iid').read_text().strip()]
root=work/'linux-diagnostic/network-recovery.zz7sq2ve/extracted';rel=lambda p:'/work/'+str(p.relative_to(work))
code='set -eu\n'
for p in [*sorted((tree/'usr/libexec/muos-boot').glob('*.sh')),stage/'install.sh',stage/'install-functions.sh']:
 code+=f'qemu-aarch64 -cpu cortex-a35 -L {rel(root)} {rel(root/"bin/busybox")} sh -n {rel(p)}\n'
r=subprocess.run(container+['sh','-c',code],capture_output=True,text=True,timeout=40);(stage/'shell.stdout').write_text(r.stdout);(stage/'shell.stderr').write_text(r.stderr);assert r.returncode==0,r.stderr
with tarfile.open(stage/'deployment.tar','w') as archive:
 for p in [payload,stage/'install.sh',stage/'install-functions.sh']:archive.add(p,arcname=p.name)
sources=[Path(__file__),repo/'port/scripts/check-phase4-boot-diagnostic.py',*sorted((repo/'port/device/rk-r35s-p0/boot-diagnostic').iterdir())]
meta={'experiment':'MUOS-R35S-BOOT-ONCE-P4-C12','host_passed':True,'hardware_tested':False,'coordinator_stage':str(coordinator),'coordinator_manifest_sha256':sha(coordinator/'manifest.json'),'checks':checks,'active_selection_diff_only_two_dispatchers':True,'C07_fallback_next_boot':True,'session_lease_seconds':90,'allow_power':False,'recover_network':True,'persistent_user_settings':False,'kernel_DTB_bootloader_partition_changes':False,'installed_files':{str(p.relative_to(tree)):{'sha256':sha(p),'mode':modes[str(p.relative_to(tree))]} for p in files},'inittab_before_sha256':sha(original),'inittab_selected_sha256':sha(payload/'inittab.selected'),'deployment_sha256':sha(stage/'deployment.tar'),'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}}
(stage/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n');(area/'latest-boot-test').write_text(str(stage)+'\n');print('C12 one-shot selector/install/rollback host candidate prepared:',stage)
