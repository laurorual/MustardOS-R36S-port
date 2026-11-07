#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C05 revision: keep failure logs even when root cannot be remounted ro."""
from pathlib import Path
import hashlib,json,mmap,os,shutil,subprocess,tempfile
r=Path(__file__).resolve().parents[2];w=r/'build/phase4';base=w/'linux-diagnostic/native-audio.0r7d8gpx'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
meta=json.loads((base/'manifest.json').read_text());assert sha(base/'rootfs.ext4')==meta['rootfs_sha256']
s=Path(tempfile.mkdtemp(prefix='audio-observe.',dir=w/'linux-diagnostic'));assets=s/'assets';assets.mkdir();shutil.copyfile(base/'rootfs.ext4',s/'rootfs.ext4')
run=(base/'assets/usr_libexec_muos-c01-run').read_text()
old="""mount -o remount,ro / || fail 'Root remount ro failed'
findmnt -rn -o OPTIONS / | tr ',' '\\n' | grep -qx ro || fail 'Root ro check failed'"""
assert old in run
new='''echo 'ROOT WRITERS BEFORE REMOUNT' >> "$state/report.txt"
/usr/libexec/muos-root-writers >> "$state/report.txt" 2>&1
echo 'MOUNTINFO BEFORE REMOUNT' >> "$state/report.txt"; cat /proc/self/mountinfo >> "$state/report.txt"
root_ro=1
mount -o remount,ro / > "$state/remount.txt" 2>&1 || root_ro=0
findmnt -rn -o OPTIONS / | tr ',' '\\n' | grep -qx ro || root_ro=0
[ "$root_ro" = 1 ] || status=1
{
    echo 'ROOT_RO'; echo "$root_ro"
    echo 'REMOUNT RESULT'; cat "$state/remount.txt"
    echo 'FINAL STATUS AFTER REMOUNT'; echo "$status"
} >> "$state/report.txt"'''
run=run.replace(old,new)
anchor='[ "$status" = 0 ] || fail \'Services check failed; DIAG07 saved, root ro\''
assert anchor in run
run=run.replace(anchor,'[ "$root_ro" = 1 ] || fail \'Root still rw; DIAG07 saved, FAT unmounted\'\n'+anchor)
(assets/'usr_libexec_muos-c01-run').write_text(run)
container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{w}:/work:rw,z','-v',f'{r}/port:/port:ro,z','-e','STAGE_REL='+str(s.relative_to(w)),(w/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c']
compile=r'''
s=/work/$STAGE_REL
cc=/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc
"$cc" -std=c11 -O2 -Wall -Wextra -Werror -march=armv8-a -mtune=cortex-a35 -fPIE -pie -Wl,-z,relro,-z,now /port/diagnostics/root-writers.c -o "$s/assets/usr_libexec_muos-root-writers"
gcc -std=c11 -O2 -Wall -Wextra -Werror /port/diagnostics/root-writers.c -o "$s/root-writers-host"
'''
with (s/'compile.log').open('w') as f:subprocess.run(container+[compile],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=40)
# Only inspect this fixture process and this known file/device; never dump
# host-wide processes, command lines or file contents.
with (s/'writer-fixture').open('w+b') as f:
 f.truncate(4096);mapped=mmap.mmap(f.fileno(),4096,access=mmap.ACCESS_WRITE)
 x=subprocess.run([str(s/'root-writers-host'),'--pid',str(os.getpid()),'--device-path',str(s)],capture_output=True,text=True,check=True)
 assert any('FD_WRITER ' in line and str(s/'writer-fixture') in line for line in x.stdout.splitlines())
 assert any('MAP_WRITER ' in line and str(s/'writer-fixture') in line for line in x.stdout.splitlines())
 mapped.close()
(s/'writer-fixture-result.json').write_text(json.dumps({'regular_writable_fd_detected':True,'shared_writable_mapping_detected':True,'file_contents_read':False,'host_process_dump_saved':False},indent=2)+'\n')
names=['usr/libexec/muos-root-writers','usr/libexec/muos-c01-run'];entries=[];commands=[]
for name in names:
 p=assets/name.replace('/','_');oldp=base/'extracted'/name
 entries.append({'path':name,'asset':p.name,'sha256':sha(p),'old_sha256':sha(oldp) if oldp.is_file() else None,'mode':0o755})
 if oldp.exists():commands.append('rm /'+name)
 commands += [f'write assets/{p.name} /{name}',f'set_inode_field /{name} mode 0100755']
(s/'debugfs.commands').write_text('\n'.join(commands)+'\n')
audit=r'''
cd /work/$STAGE_REL
debugfs -w -f debugfs.commands rootfs.ext4 > debugfs.log 2>&1
e2fsck -fn rootfs.ext4 > fsck.log 2>&1
mkdir extracted
/work/graphics-config/output/host/bin/fakeroot debugfs -R "rdump / $PWD/extracted" rootfs.ext4 > extract.log 2>&1
root=$PWD/extracted
qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh -n "$root/usr/libexec/muos-c01-run"
qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/lib/ld-linux-aarch64.so.1" --list "$root/usr/libexec/muos-root-writers" > writer-loader.txt
readelf -h -l -d "$root/usr/libexec/muos-root-writers" > writer-elf.txt
'''
with (s/'audit.log').open('w') as f:subprocess.run(container+[audit],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=100)
for e in entries:assert sha(s/'extracted'/e['path'])==e['sha256']
assert not (s/'extracted/var/lib/muos-seedrng').exists()
plan={'experiment':meta['experiment'],'diagnostic_revision_update':1,'authorized_secondary_c05_revision':True,'installer_sha256':sha(r/'port/scripts/install-phase4-service-diagnostic.py'),'entries':entries,'unchanged_required':meta['unchanged_required']}
(s/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
record={**plan,'base_manifest_sha256':sha(base/'manifest.json'),'rootfs_sha256':sha(s/'rootfs.ext4'),'host_audit_passed':True,'seed_material_included':False,'native_boot_tested':False,'scope':'C05 root writer/mount trace and preserved FAT logs on failed root-ro, still rejects status','port_inputs':{n:sha(r/n) for n in ['port/scripts/prepare-phase4-audio-observability.py','port/diagnostics/root-writers.c','port/scripts/install-phase4-service-diagnostic.py']}}
(s/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');(w/'linux-diagnostic/latest-audio-observability').write_text(str(s)+'\n');print('C05 failure-log revision audited:',s)
