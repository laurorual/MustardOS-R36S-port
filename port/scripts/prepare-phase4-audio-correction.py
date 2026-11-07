#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C05 logger lifecycle correction and ALSA/PipeWire failure diagnostics."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
r=Path(__file__).resolve().parents[2];w=r/'build/phase4';base=w/'linux-diagnostic/audio-observe.4qp6gxvg'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((base/'manifest.json').read_text());assert sha(base/'rootfs.ext4')==m['rootfs_sha256']
s=Path(tempfile.mkdtemp(prefix='audio-correct.',dir=w/'linux-diagnostic'));a=s/'assets';a.mkdir();shutil.copyfile(base/'rootfs.ext4',s/'rootfs.ext4')
run=(base/'assets/usr_libexec_muos-c01-run').read_text()
anchor="    echo 'MAPPING';"
assert anchor in run
run=run.replace(anchor,'''    echo 'CORE FAILURE GRAPH'
    head -c 196608 /run/muos/core/pw-dump-failure.json 2>/dev/null
    echo; echo 'CORE FAILURE STATUS'; cat /run/muos/core/wpctl-failure.txt 2>/dev/null
    echo 'ALSA CARDS'; cat /proc/asound/cards /proc/asound/pcm 2>/dev/null
    echo 'ALSA NODES'; ls -l /dev/snd
    echo 'ALSA UDEV'; udevadm info --query=property --path=/sys/class/sound/card0
'''+anchor)
anchor='echo \'ROOT WRITERS BEFORE REMOUNT\' >> "$state/report.txt"'
assert anchor in run
stop=(r/'port/device/rk-r35s-p0/audio-diagnostic/stop-logger.sh').read_text()
run=run.replace(anchor,stop+'\nc05_stop_logger >> "$state/report.txt" 2>&1 || status=1\n'+anchor)
(a/'usr_libexec_muos-c01-run').write_text(run)
# Native upstream mulog fixture: relocate only filesystem constants in a
# private build copy. Keep refs and installed binary untouched; GPL applies.
f=s/'logger-fixture';f.mkdir();src=w/'core/source/frontend/module/mulog.c'
assert sha(src)==sha(r/'refs/muos/frontend/module/mulog.c')
paths={'LOG_DIR':'logs','LOG_SCK':'sock','LOG_PID':'pid','LOG_LOCK':'lock','SYS_DEBUG_FILE':'debug','VERBOSE_FILE':'verbose'}
text=src.read_text()
for name,tail in paths.items():
 import re
 text,n=re.subn(r'^#define '+name+r'\s+"[^"]*"',f'#define {name} "/work/{f.relative_to(w)}/{tail}"',text,flags=re.M);assert n==1
text=text.replace('"/run/muos"',f'"/work/{f.relative_to(w)}"')
(f/'mulog.c').write_text(text);(f/'debug').write_text('2\n');(f/'verbose').write_text('0\n');shutil.copyfile(r/'refs/muos/frontend/LICENSE',f/'LICENSE')
container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{w}:/work:rw,z','-e','STAGE_REL='+str(s.relative_to(w)),(w/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c']
test=r'''
s=/work/$STAGE_REL
gcc -std=c11 -D_GNU_SOURCE -O2 -Wall -Wextra -I/work/core/source/frontend "$s/logger-fixture/mulog.c" -o "$s/logger-fixture/mulog"
python3 - "$s" <<'FIXTURE'
from pathlib import Path
import subprocess,sys,time,os,json
s=Path(sys.argv[1]);f=s/'logger-fixture';daemon_log=(s/'logger-daemon.log').open('w');daemon=subprocess.Popen([str(f/'mulog'),'--daemon'],stdout=daemon_log,stderr=subprocess.STDOUT)
try:
 deadline=time.monotonic()+3
 while not (f/'sock').exists() and time.monotonic()<deadline:time.sleep(.02)
 assert (f/'sock').exists()
 subprocess.run([str(f/'mulog'),'info','c05fixture','-1','test','known-message'],check=True)
 deadline=time.monotonic()+3
 while time.monotonic()<deadline:
  logs=list((f/'logs').glob('*.log'))
  if logs and 'known-message' in logs[0].read_text():break
  time.sleep(.02)
 assert logs and 'known-message' in logs[0].read_text()
 assert daemon.poll() is None
 daemon.terminate();assert daemon.wait(timeout=3)==0
 assert not (f/'pid').exists() and not (f/'sock').exists()
 (s/'logger-fixture-result.json').write_text(json.dumps({'native_upstream_source':True,'only_paths_relocated':True,'debug_mode_2_daemon_observed_alive':True,'known_log_flushed':True,'sigterm_exit_zero':True,'pid_and_socket_removed':True,'device_binary_changed':False},indent=2)+'\n')
finally:
 if daemon.poll() is None:daemon.kill();daemon.wait()
 daemon_log.close()
FIXTURE
'''
with (s/'logger-fixture.log').open('w') as out:subprocess.run(container+[test],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=30)
old=base/'extracted/usr/libexec/muos-c01-run';entry={'path':'usr/libexec/muos-c01-run','asset':'usr_libexec_muos-c01-run','sha256':sha(a/'usr_libexec_muos-c01-run'),'old_sha256':sha(old),'mode':0o755}
(s/'debugfs.commands').write_text('rm /usr/libexec/muos-c01-run\nwrite assets/usr_libexec_muos-c01-run /usr/libexec/muos-c01-run\nset_inode_field /usr/libexec/muos-c01-run mode 0100755\n')
audit=r'''
cd /work/$STAGE_REL
debugfs -w -f debugfs.commands rootfs.ext4 > debugfs.log 2>&1
e2fsck -fn rootfs.ext4 > fsck.log 2>&1
mkdir extracted
/work/graphics-config/output/host/bin/fakeroot debugfs -R "rdump / $PWD/extracted" rootfs.ext4 > extract.log 2>&1
root=$PWD/extracted
qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh -n "$root/usr/libexec/muos-c01-run"
'''
with (s/'audit.log').open('w') as out:subprocess.run(container+[audit],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=100)
assert sha(s/'extracted'/entry['path'])==entry['sha256'] and not (s/'extracted/var/lib/muos-seedrng').exists()
required={**m['unchanged_required'],'opt/muos/frontend/mulog':sha(base/'extracted/opt/muos/frontend/mulog')}
plan={'experiment':m['experiment'],'diagnostic_revision_update':2,'authorized_secondary_c05_revision':True,'installer_sha256':sha(r/'port/scripts/install-phase4-service-diagnostic.py'),'entries':[entry],'unchanged_required':required}
(s/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
record={**plan,'base_manifest_sha256':sha(base/'manifest.json'),'rootfs_sha256':sha(s/'rootfs.ext4'),'host_audit_passed':True,'seed_material_included':False,'native_audio_tested':False,'scope':'C05 stop native mulog after service logs; capture pre-stop PipeWire graph and ALSA identities; no guessed sink change','port_inputs':{n:sha(r/n) for n in ['port/scripts/prepare-phase4-audio-correction.py','port/device/rk-r35s-p0/audio-diagnostic/stop-logger.sh','port/scripts/install-phase4-service-diagnostic.py']},'mulog_original_source_sha256':sha(src)}
(s/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');(w/'linux-diagnostic/latest-audio-correction').write_text(str(s)+'\n');print('C05 logger correction audited:',s)
