#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Real calibration controller on tmpfs, hardware/identity adapters replaced."""
from pathlib import Path
import json,subprocess,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'volume-calibration';area.mkdir(exist_ok=True)
s=Path(tempfile.mkdtemp(prefix='checks.',dir=area));source=repo/'port/device/rk-r35s-p0/volume-calibration/step.sh'
script=r"""
from pathlib import Path
import os,shutil,subprocess,time,signal
parent=Path('/run/muos-volcal.ABCDEF');parent.mkdir(mode=0o700)
pkg=Path('/usr/libexec/muos-c25');pkg.mkdir(parents=True)
(pkg/'policy.sh').write_text('')
(pkg/'card-guard.sh').write_text('')
(pkg/'native.sh').write_text('c25_media() { return 0; }; c25_root_mode() { return 0; }\n')
pkg=Path('/usr/libexec/muos-session');pkg.mkdir()
(pkg/'control-functions.sh').write_text('session_current() { generation=run-0001;cycle=/tmp/cycle;return 0; }; session_identity() { test -f /tmp/alive; }\n')
Path('/tmp/cycle').mkdir();Path('/tmp/cycle/run.conf').write_text('lease_seconds=600\n');Path('/tmp/cycle/ready').touch()
binary=Path('/tmp/bin');binary.mkdir()
(binary/'pidof').write_text('#!/bin/sh\necho 1\n')
(binary/'amixer').write_text('''#!/bin/sh
case "$3" in cget) printf '  : values=';cat /tmp/codec ;; cset) echo "$5" >/tmp/codec;echo "$5" >>/tmp/codec-changes ;;
esac
''')
(binary/'wpctl').write_text('''#!/bin/sh
case "$1" in
inspect) echo 'id 35, type PipeWire:Interface:Node';echo ' node.name = "alsa_output.platform-rk817-sound.playback.0.0"';echo ' object.serial = "39"' ;;
get-volume) printf 'Volume: ';cat /tmp/volume ;;
set-volume) echo "$3" >/tmp/volume;echo "$3" >>/tmp/changes ;;
esac
''')
for f in binary.iterdir():f.chmod(0o755)
text=Path('/port/device/rk-r35s-p0/volume-calibration/step.sh').read_text().replace('export PATH=/usr/sbin:/usr/bin:/sbin:/bin','export PATH=/tmp/bin:/usr/sbin:/usr/bin:/sbin:/bin').replace('+180)', '+1)')
Path('/tmp/step.sh').write_text(text)
def reset():
 for f in parent.iterdir():
  if f.is_dir():shutil.rmtree(f)
  else:f.unlink()
 parent.chmod(0o700);(parent/'deadline').write_text(str(int(float(Path('/proc/uptime').read_text().split()[0]))+600)+'\n')
 Path('/tmp/volume').write_text('0.55\n');Path('/tmp/codec').write_text('195,195\n');Path('/tmp/codec-changes').unlink(missing_ok=True);Path('/tmp/alive').touch();Path('/tmp/changes').unlink(missing_ok=True)
def run(level):return subprocess.run(['sh','/tmp/step.sh',str(parent),'run-0001',str(level)],capture_output=True,text=True,timeout=5)
def done(name):print('PASS_'+name,flush=True)
reset();r=run(100);assert r.returncode==0,(r.stdout,r.stderr);assert Path('/tmp/changes').read_text()=='1.00\n0.55\n';done('deadline_restores_maximum_to55')
reset();p=subprocess.Popen(['sh','/tmp/step.sh',str(parent),'run-0001','65'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
for n in range(100):
 if (parent/'level-65/ready').exists():break
 time.sleep(.005)
assert (parent/'level-65/ready').exists();p.send_signal(signal.SIGTERM);out,err=p.communicate(timeout=4)
assert p.returncode==0 and Path('/tmp/volume').read_text()=='0.55\n',(out,err);done('operator_finish_restores55')
reset();r=run(101);assert r.returncode==64 and not Path('/tmp/changes').exists();done('overrange_refused_before_change')
reset();parent.chmod(0o755);r=run(65);assert r.returncode==64 and not Path('/tmp/changes').exists();done('wrong_directory_mode_refused')
reset();(parent/'deadline').write_text('0\n');r=run(65);assert r.returncode==64 and not Path('/tmp/changes').exists();done('insufficient_lease_refused')
reset();Path('/tmp/volume').write_text('0.75\n');r=run(65);assert r.returncode==64 and not Path('/tmp/changes').exists();done('foreign_initial_volume_refused')
reset();Path('/tmp/alive').unlink();r=run(65);assert r.returncode==64 and not Path('/tmp/changes').exists();done('foreign_session_refused')
reset();r=run(0);assert r.returncode==0 and Path('/tmp/changes').read_text()=='0.00\n0.55\n';done('zero_step_restores55')
reset();p=subprocess.Popen(['sh','/tmp/step.sh',str(parent),'run-0001','65'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
for n in range(100):
 if (parent/'level-65/ready').exists():break
 time.sleep(.005)
assert (parent/'level-65/ready').exists();Path('/tmp/volume').write_text('0.75\n');out,err=p.communicate(timeout=4)
assert p.returncode==1 and Path('/tmp/volume').read_text()=='0.55\n' and 'volume-changed' in (parent/'level-65/report.txt').read_text();done('external_volume_drift_aborts_and_restores')
reset();r=subprocess.run(['sh','/tmp/step.sh',str(parent),'run-0001','100','205'],capture_output=True,text=True,timeout=5)
assert r.returncode==0,(r.stdout,r.stderr)
assert Path('/tmp/codec-changes').read_text()=='205,205\n195,195\n' and Path('/tmp/volume').read_text()=='0.55\n';done('codec205_watchdog_restores_both_controls')
reset();r=subprocess.run(['sh','/tmp/step.sh',str(parent),'run-0001','65','205'],capture_output=True,text=True,timeout=5)
assert r.returncode==64 and not Path('/tmp/changes').exists();done('codec_trial_wrong_level_refused')
reset();(parent/'deadline').write_text(str(int(float(Path('/proc/uptime').read_text().split()[0]))+209)+'\n');r=run(65)
assert r.returncode==64 and not Path('/tmp/changes').exists();done('late_preparation_cannot_overlap_worker_lease')
reset();Path('/tmp/codec').write_text('215,215\n');r=subprocess.run(['sh','/tmp/step.sh',str(parent),'run-0001','0','215','215'],capture_output=True,text=True,timeout=5)
assert r.returncode==0 and Path('/tmp/volume').read_text()=='0.55\n' and Path('/tmp/codec').read_text()=='215,215\n' and not Path('/tmp/codec-changes').exists();done('calibrated_native_gain215_preserved')
"""
(s/'fixtures.py').write_text(script)
rel='/work/'+str((s/'fixtures.py').relative_to(work))
r=subprocess.run(['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev','--tmpfs','/run:rw,nosuid,nodev','--tmpfs','/usr/libexec:rw,nosuid,nodev','-v',f'{repo}/port:/port:ro,z','-v',f'{work}:/work:ro,z',(work/'rootfs-container.iid').read_text().strip(),'python3','-B',rel],capture_output=True,text=True,timeout=20)
(s/'stdout').write_text(r.stdout);(s/'stderr').write_text(r.stderr);assert r.returncode==0,(s,r.stdout,r.stderr)
report={'passed':True,'cases':r.stdout.splitlines(),'native_hardware_accessed':False,'source_sha256':{str(f.relative_to(repo)):sha(f) for f in [Path(__file__),source]}}
(s/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-checks').write_text(str(s)+'\n');print('Calibration13 control/restore guards passed',s)
