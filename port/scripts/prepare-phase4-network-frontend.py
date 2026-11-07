#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C08 RAM-only package and lifecycle fixtures, using verified C06/C07 assets."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,tarfile,tempfile

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
updates=[work/'linux-diagnostic'/name for name in ['latest-network-recovery','latest-network-reprobe','latest-network-deadline']]
base=next((Path(p.read_text().strip()) for p in updates if p.exists()),work/'linux-diagnostic/network-deadline.6qfz33xd')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
meta=json.loads((base/'manifest.json').read_text())
stage=Path(tempfile.mkdtemp(prefix='network-frontend.',dir=work/'linux-diagnostic'))
package=stage/'package';package.mkdir()
source=repo/'port/device/rk-r35s-p0/network-frontend-diagnostic'
for name in ['run.sh','chain.sh']:shutil.copyfile(source/name,package/name)
required={**meta['unchanged_required'],**{e['path']:e['sha256'] for e in meta['entries']}}
for name in ['etc/init.d/S30dbus-daemon','etc/init.d/S90muos-storage','etc/init.d/S95muos-core','etc/init.d/S96muos-input-ready','etc/init.d/S99muos-ui','usr/libexec/muos-c06-session','usr/libexec/muos-run-bounded']:
    required[name]=sha(base/'extracted'/name)
(package/'prerequisites.sha256').write_text(''.join(value+'  /'+name+'\n' for name,value in sorted(required.items())))
assert 'c06_control_effects=0\n' in (base/'extracted/usr/libexec/muos-c06-session').read_text()
assert 'c06_nav_adjusted=1\n' in (base/'extracted/usr/libexec/muos-c06-session').read_text()

# The actual C08 chain executes fixture services, including partial failures.
fixtures=stage/'fixtures';fixtures.mkdir();services=fixtures/'services';services.mkdir()
names=['S30dbus-daemon','S90muos-storage','S95muos-core','S96muos-input-ready']
for name in names:
    p=services/name;p.write_text('#!/bin/sh\necho "${0##*/}:$1" >> "$EVENTS"\n[ "${FAIL:-}" != "${0##*/}:$1" ]\n');p.chmod(0o755)
test='''. "$CHAIN"
state=$CASE_STATE
c08_service_dir=$SERVICES
c08_exec() { "$@"; }
c06_before_core() { echo before-core >> "$EVENTS"; [ "$FAIL" != before-core ]; }
c08_start_chain
start=$?
c08_stop_chain
stop=$?
if [ "$stop" = 0 ]; then c08_stop_chain || exit 99; fi
printf '%s %s\\n' "$start" "$stop"
'''
cases={}
for label,failure in [('success',''),('dbus-start','S30dbus-daemon:start'),('storage-start','S90muos-storage:start'),
                      ('core-pre-hook','before-core'),('core-start','S95muos-core:start'),('input-start','S96muos-input-ready:start'),
                      ('input-status','S96muos-input-ready:status'),('core-stop','S95muos-core:stop')]:
    state=fixtures/label;state.mkdir();events=state/'events'
    env={**os.environ,'CHAIN':str(source/'chain.sh'),'CASE_STATE':str(state),'SERVICES':str(services),'EVENTS':str(events),'FAIL':failure}
    r=subprocess.run(['sh','-c',test],env=env,text=True,capture_output=True)
    assert r.returncode==0,(label,r.stderr)
    start,stop=map(int,r.stdout.split())
    assert (start,stop)==((0,0) if label=='success' else (0,1) if label=='core-stop' else (1,0)),(label,r.stdout)
    log=events.read_text().splitlines()
    attempted=names[:1] if label=='dbus-start' else names[:2] if label=='storage-start' else names[:3] if label in ['core-pre-hook','core-start'] else names
    assert log[-len(attempted):]==[name+':stop' for name in reversed(attempted)],(label,log)
    assert not any(name in '\n'.join(log) for name in ['S05','S10','c07','seedrng','network'])
    assert (state/'attempted').exists()==(label=='core-stop')
    cases[label]={'passed':True,'start':start,'stop':stop,'events':log,'shared_services_untouched':True}
(stage/'chain-fixtures.json').write_text(json.dumps(cases,indent=2)+'\n')
proc=fixtures/'proc';proc.mkdir()
for pid,parent,exe in [('209','1','/sbin/udevd'),('5203','209','/sbin/udevd'),('5204','209','/sbin/udevd'),('888','1','/sbin/udevd'),('77','1','/bin/busybox')]:
    p=proc/pid;p.mkdir();(p/'status').write_text('PPid:\t'+parent+'\n');(p/'exe').symlink_to(exe)
identities={}
for label,pids,expected in [('main',['209'],'209'),('worker-first',['5203','209'],'209'),('two-workers',['5203','5204','209'],'209'),
                            ('worker-only',['5203'],None),('two-daemons',['209','888'],None),('wrong-exe',['77'],None),('invalid',['x'],None)]:
    r=subprocess.run(['sh','-c','. "$1"; shift; c08_main_udev "$@"','test',str(source/'chain.sh'),str(proc),*pids],text=True,capture_output=True)
    assert (r.returncode==0)==(expected is not None),(label,r.stderr)
    if expected:assert r.stdout.strip()==expected
    identities[label]={'passed':True,'selected':r.stdout.strip(),'exit':r.returncode}
(stage/'udev-fixtures.json').write_text(json.dumps(identities,indent=2)+'\n')

container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev',
 '-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z','-e','STAGE_REL='+str(stage.relative_to(work)),
 (work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c']
code=r'''
cd /work/$STAGE_REL
cc=/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc
"$cc" -std=c11 -Wall -Wextra -Werror -O2 -g0 -mcpu=cortex-a35 -fPIE -pie -Wl,-z,relro,-z,now /port/utils/muos-mount-namespace.c -o package/mount-namespace
readelf -h -l -d package/mount-namespace > namespace-elf.txt
root=/work/linux-diagnostic/network-deadline.6qfz33xd/extracted
qemu-aarch64 -cpu cortex-a35 -L "$root" -E LD_BIND_NOW=1 "$root/lib/ld-linux-aarch64.so.1" --inhibit-cache --library-path "$root/lib:$root/usr/lib" --list "$PWD/package/mount-namespace" > namespace-loader.txt
for name in run.sh chain.sh; do
 qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh -n "package/$name"
done
'''
with (stage/'audit.log').open('w') as out:subprocess.run(container+[code],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=60)
for p in package.iterdir():p.chmod(0o755 if p.name in ['run.sh','mount-namespace'] else 0o644)
(package/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(package.iterdir()) if p.is_file()))
with tarfile.open(stage/'deployment.tar','w') as archive:
    for p in package.iterdir():archive.add(p,arcname=p.name)
manifest={'experiment':'MUOS-R35S-NETWORK-FRONTEND-P4-C08','host_audit_passed':True,
 'scope':'RAM package; no boot change; private mount namespace; reuse C06 UI/audio while preserving C07 network/udev/RNG',
 'chain_cases':cases,'udev_identity_cases':identities,'package_sha256':{p.name:sha(p) for p in package.iterdir()},'deployment_sha256':sha(stage/'deployment.tar'),
 'base_manifest_sha256':sha(base/'manifest.json'),'seed_credentials_private_keys_included':False,'native_tested':False,
 'sources':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),source/'run.sh',source/'chain.sh',repo/'port/utils/muos-mount-namespace.c']}}
(stage/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(work/'linux-diagnostic/latest-network-frontend').write_text(str(stage)+'\n')
print('C08 RAM package/chain fixtures/ABI/shell passed:',stage)
