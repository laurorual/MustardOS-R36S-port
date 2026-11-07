#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Exercise the temporary IRQ wrapper with mount/service adapters, no device."""
from pathlib import Path
import json, subprocess, tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2]; work=repo/'build/phase4'
stage=Path(tempfile.mkdtemp(prefix='irq-checks.',dir=work/'audio-clock-audit'))
fixture=r'''
from pathlib import Path
import hashlib,os,shutil,subprocess
root=Path('/tmp/irq'); root.mkdir(); os.umask(0o077)
src=Path('/port/device/rk-r35s-p0/audio-buffers/irq-session.sh').read_text()
baseline=Path('/port/device/rk-r35s-p0/core-wireplumber.conf').read_text().replace('      api.alsa.disable-tsched = true\n','')
def case(name,namespace=True,mode=0o600,symlink=False,hardlink=False,wronghash=False,irq=True,busy=False,start=True,foundation=False,bad_foundation=False):
 if root.exists(): shutil.rmtree(root)
 root.mkdir(); directory=root/'muos-c26.ABCDEF'; directory.mkdir(mode=0o700)
 target=root/'device.conf'; target.write_text(baseline)
 conf=baseline.replace('      api.alsa.period-size = 1024','      api.alsa.disable-tsched = true\n      api.alsa.period-size = 1024') if irq else baseline
 (directory/'wireplumber.conf').write_text(conf); (directory/'wireplumber.conf').chmod(mode)
 (directory/'session.conf').write_text('fixture\n')
 h='0'*64 if wronghash else hashlib.sha256(target.read_bytes()).hexdigest()
 (directory/'original-wp.sha256').write_text(h+'  '+str(target)+'\n')
 old_foundation=root/'foundation';old_foundation.write_text('original foundation\n')
 if foundation:
  (directory/'trial-foundation.sha256').write_text('trial foundation\n')
  h='0'*64 if bad_foundation else hashlib.sha256(old_foundation.read_bytes()).hexdigest()
  (directory/'original-foundation.sha256').write_text(h+'  '+str(old_foundation)+'\n')
 if symlink:
  p=directory/'wireplumber.conf'; p.rename(directory/'other'); p.symlink_to(directory/'other')
 if hardlink: os.link(directory/'wireplumber.conf',directory/'other')
 code=src.replace('/run/muos-c26.',str(root/'muos-c26.')).replace('/opt/muos/device/control/wireplumber.conf',str(target))
 code=code.replace('/usr/libexec/muos-session/prerequisites.sha256',str(old_foundation))
 service=root/'service'; service.write_text('#!/bin/sh\necho START >> '+str(root/'events')+'\n'+('exit 0\n' if start else 'exit 7\n'));service.chmod(0o700)
 code=code.replace('/usr/libexec/muos-session/service.sh',str(service))
 adapters=f"""
readlink() {{ case "$1" in /proc/self/ns/mnt) echo 'mnt:[{'2' if namespace else '1'}]' ;; /proc/1/ns/mnt) echo 'mnt:[1]' ;; *) command readlink "$@" ;; esac; }}
findmnt() {{ {'return 0' if busy else 'return 1'}; }}
mount() {{ echo MOUNT >> {root}/events; cp "$3" "$3.saved"; cp "$2" "$3"; }}
umount() {{ echo UMOUNT >> {root}/events; cp "$1.saved" "$1"; rm "$1.saved"; }}
"""
 # Inject adapters after PATH so the real script still exercises its guards.
 code=code.replace('umask 077\n','umask 077\n'+adapters,1)
 wrapper=root/'wrapper'; wrapper.write_text(code)
 result=subprocess.run(['sh',str(wrapper),str(directory)],capture_output=True,text=True,timeout=5)
 expected=namespace and mode==0o600 and not symlink and not hardlink and not wronghash and irq and not busy and not bad_foundation
 assert (result.returncode==0)==(expected and start),(name,result.stdout,result.stderr)
 events=(root/'events').read_text() if (root/'events').exists() else ''
 sequence='MOUNT\nMOUNT\nSTART\nUMOUNT\nUMOUNT\n' if foundation else 'MOUNT\nSTART\nUMOUNT\n'
 assert events==(sequence if expected else ''),(name,events)
 assert target.read_text()==baseline,name
 assert old_foundation.read_text()=='original foundation\n',name
 print('PASS_'+name)
case('isolated_start_unmounts_parent_bind')
case('global_namespace_refused',namespace=False)
case('nonprivate_mode_refused',mode=0o644)
case('symlink_config_refused',symlink=True)
case('hardlink_config_refused',hardlink=True)
case('changed_native_source_refused',wronghash=True)
case('missing_IRQ_setting_refused',irq=False)
case('foreign_bind_refused',busy=True)
case('failed_start_unmounts_parent_bind',start=False)
case('trial_foundation_private_bind_restored',foundation=True)
case('trial_foundation_changed_origin_refused',foundation=True,bad_foundation=True)
case('failed_start_restores_both_private_binds',foundation=True,start=False)
'''
(stage/'fixtures.py').write_text(fixture)
relative='/work/'+str((stage/'fixtures.py').relative_to(work))
command=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{repo}/port:/port:ro,z','-v',f'{work}:/work:ro,z',(work/'rootfs-container.iid').read_text().strip(),'python3','-B',relative]
r=subprocess.run(command,capture_output=True,text=True,timeout=30)
for name,value in [('stdout',r.stdout),('stderr',r.stderr)]: (stage/name).write_text(value)
assert r.returncode==0,(stage,r.stdout,r.stderr)
cases=[line for line in r.stdout.splitlines() if line.startswith('PASS_')]; assert len(cases)==12
sources=[Path(__file__),repo/'port/scripts/phase4-audio-buffers.py',repo/'port/device/rk-r35s-p0/audio-buffers/irq-session.sh',repo/'port/device/rk-r35s-p0/core-wireplumber.conf']
(stage/'analysis.json').write_text(json.dumps({'passed':True,'cases':cases,'hardware_accessed':False,'mount_and_service_adapters_mocked':True,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}},indent=2)+'\n')
(work/'audio-clock-audit/latest-irq-checks').write_text(str(stage)+'\n')
print('IRQ scheduling guard checks passed:',len(cases),stage)
