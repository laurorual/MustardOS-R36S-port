#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Prepare C01 payload and a host clone, without accessing device media."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
base=work/'linux-diagnostic/ext4.0fns3h93';meta=json.loads((base/'manifest.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(base/'rootfs.ext4')==meta['rootfs']['sha256']
stage=Path(tempfile.mkdtemp(prefix='services.',dir=work/'linux-diagnostic'));assets=stage/'assets';assets.mkdir()
shutil.copyfile(base/'rootfs.ext4',stage/'rootfs.ext4')
sources={
 'usr/libexec/muos-c01-chain':repo/'port/device/rk-r35s-p0/service-diagnostic/chain.sh',
 'usr/libexec/muos-c01-run':repo/'port/device/rk-r35s-p0/service-diagnostic/run',
 'sbin/muos-ext4-diag':repo/'port/device/rk-r35s-p0/service-diagnostic/bootstrap'}
for target,source in sources.items():shutil.copyfile(source,assets/target.replace('/','_'))
inittab=(base/'extracted/etc/inittab').read_text()
inittab=inittab.replace('::sysinit:/bin/mount -t proc proc /proc\n','')
inittab=inittab.replace('::sysinit:/etc/init.d/rcS','::sysinit:/usr/libexec/muos-c01-run')
inittab=inittab.replace('::shutdown:/etc/init.d/rcK','::shutdown:/usr/libexec/muos-c01-run stop')
inittab='\n'.join(line for line in inittab.splitlines() if not line.startswith('ttyFIQ0::respawn:'))+'\n'
(assets/'etc_inittab').write_text(inittab)
(assets/'etc_default_muos-core').write_text('audio=0\ninput=1\n')
(assets/'etc_muos-services-diagnostic').write_text('MUOS-R35S-INIT-P4-C01\n')
image=(work/'rootfs-container.iid').read_text().strip()
container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev',
 '-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z','-e','STAGE_REL='+str(stage.relative_to(work)),image,'sh','-eu','-c']
compile=r'''
stage=/work/$STAGE_REL
cc=/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc
"$cc" -std=c11 -O2 -Wall -Wextra -march=armv8-a -mtune=cortex-a35 -fPIE -pie -Wl,-z,relro,-z,now /port/utils/muos-run-bounded.c -o "$stage/assets/usr_libexec_muos-run-bounded"
gcc -std=c11 -O2 -Wall -Wextra /port/utils/muos-run-bounded.c -o "$stage/bounded-host"
readelf -h -l -d "$stage/assets/usr_libexec_muos-run-bounded" > "$stage/bounded-elf.txt"
"$stage/bounded-host" 1 /bin/true
if "$stage/bounded-host" 1 sh -c 'exit 7'; then exit 1; else test "$?" = 7; fi
if "$stage/bounded-host" 1 sh -c 'trap "" TERM; sleep 10'; then exit 1; else test "$?" = 124; fi
'''
with (stage/'compile.log').open('w') as f:subprocess.run(container+[compile],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=30)
# Bootstrap last is the activation point. Old B01 init ignores the new inittab
# and extra marker; the new bootstrap requires all C01 prerequisites.
targets=['usr/libexec/muos-c01-chain','usr/libexec/muos-c01-run','usr/libexec/muos-run-bounded',
         'etc/default/muos-core','etc/inittab','etc/muos-services-diagnostic','sbin/muos-ext4-diag']
entries=[];commands=[]
for target in targets:
    source=assets/target.replace('/','_');old=base/'extracted'/target
    mode=0o755 if target.startswith(('usr/libexec/','sbin/')) else 0o644
    entries.append({'path':target,'asset':source.name,'sha256':sha(source),'mode':mode,
                    'old_sha256':sha(old) if old.is_file() else None})
    if old.exists():commands.append('rm /'+target)
    commands += [f'write assets/{source.name} /{target}',f'set_inode_field /{target} mode 0{mode|0o100000:o}']
(stage/'debugfs.commands').write_text('\n'.join(commands)+'\n')
audit=r'''
cd /work/$STAGE_REL
debugfs -w -f debugfs.commands rootfs.ext4 > debugfs.log 2>&1
e2fsck -fn rootfs.ext4 > fsck.log 2>&1
mkdir extracted
/work/graphics-config/output/host/bin/fakeroot debugfs -R "rdump / $PWD/extracted" rootfs.ext4 > extract.log 2>&1
root=$PWD/extracted
for script in sbin/muos-ext4-diag usr/libexec/muos-c01-run usr/libexec/muos-c01-chain; do
 qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh -n "$root/$script"
done
qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/usr/libexec/muos-run-bounded" 1 /bin/true
if qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh "$root/sbin/muos-ext4-diag" > pid-guard.txt 2>&1; then exit 1; else test "$?" = 64; fi
if qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh "$root/usr/libexec/muos-c01-run" > runner-guard.txt 2>&1; then exit 1; else test "$?" = 64; fi
'''
with (stage/'audit.log').open('w') as f:subprocess.run(container+[audit],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=90)
for e in entries:assert sha(stage/'extracted'/e['path'])==e['sha256']
assert (stage/'extracted/etc/default/muos-ui').read_text().startswith('enabled=0\nhotkeys=0\n')
assert (stage/'extracted/sbin/init').readlink().as_posix()=='../bin/busybox'
# Exercise actual service executables with ordering, failed startup and failed
# stop. No simulated kernel success is claimed by these host fixtures.
fixtures=stage/'chain-fixtures';fixtures.mkdir();services=fixtures/'services';services.mkdir()
names=['S10udev','S30dbus-daemon','S90muos-storage','S95muos-core','S96muos-input-ready','S99muos-ui']
for name in names:
    p=services/name;p.write_text('#!/bin/sh\necho "${0##*/}:$1" >> "$C01_LOG"\n[ "${FAIL:-}" != "${0##*/}:$1" ]\n');p.chmod(0o755)
shell='''set -eu
. "$1"
c01_state=$2
c01_exec() { "$@"; }
c01_udev_ready() { [ "${UDEV_FAIL:-0}" = 0 ]; }
status=0
c01_start_chain "$3" || status=1
c01_stop_chain "$3" || status=1
c01_stop_chain "$3"
exit "$status"
'''
cases={}
for name,failure,udev,ok in [('success','',0,True),('failed-start','S95muos-core:start',0,False),('failed-coldplug','',1,False),('failed-stop','S96muos-input-ready:stop',0,False)]:
    log=fixtures/(name+'.log');env={'PATH':'/usr/bin:/bin','C01_LOG':str(log),'FAIL':failure,'UDEV_FAIL':str(udev)}
    r=subprocess.run(['sh','-c',shell,'test',str(sources['usr/libexec/muos-c01-chain']),str(fixtures/name),str(services)],env=env,capture_output=True,text=True)
    assert (r.returncode==0)==ok,(name,r.stderr)
    events=log.read_text().splitlines()
    attempted=names[:4] if name=='failed-start' else names[:1] if name=='failed-coldplug' else names
    assert events[:len(attempted)]==[x+':start' for x in attempted]
    assert events[-len(attempted):]==[x+':stop' for x in reversed(attempted)]
    assert len(events)==2*len(attempted)+(3 if len(attempted)==6 else 0),events
    cases[name]={'exit':r.returncode,'events':events}
record={'experiment':'MUOS-R35S-INIT-P4-C01','base_media':'MUOS-R35S-EXT4-P4-B01',
 'scope':'BusyBox PID1 diagnostic with selected native services; not complete product rcS',
 'entries':entries,'kernel_release':'4.4.189-muos-r35s-p4','root_partuuid':'4d554432-02',
 'rootfs_sha256':sha(stage/'rootfs.ext4'),'rootfs_base_sha256':meta['rootfs']['sha256'],
 'host_audit_passed':True,'chain_cases':cases,'bounded_executor_cases':['success','child exit 7','SIGTERM ignored -> process group SIGKILL/124'],
 'native_boot_tested':False,'audio_enabled':False,'frontend_enabled':False,
 'port_inputs':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/utils/muos-run-bounded.c',*sources.values()]}}
(stage/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
(work/'linux-diagnostic/latest-services').write_text(str(stage)+'\n')
print('C01 host clone/payload audited:',stage)
