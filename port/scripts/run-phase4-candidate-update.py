#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C24 backup/apply/verify over pinned SSH; never flashes an image or touches p3."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,io,ipaddress,json,os,re,subprocess,tarfile,tempfile,time
from phase4_candidate import sha,sums

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/rootfs-candidate'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('operation',choices=['backup','apply','verify','rollback']);p.add_argument('--host',required=True,type=ipaddress.IPv4Address);p.add_argument('--stage',type=Path);a=p.parse_args()
stage=a.stage.resolve() if a.stage else Path((area/'latest-update').read_text().strip());assert stage.is_relative_to(area);plan=json.loads((stage/'plan.json').read_text());meta=json.loads((stage/'manifest.json').read_text())
assert sha(stage/'plan.json')==meta['plan_sha256'] and sha(stage/'deployment.tar')==meta['deployment_sha256']
if a.operation!='rollback':
 for name,digest in meta['sources'].items():assert sha(repo/name)==digest,name
ssh=['ssh','-p','2222','-i',str(repo/'build/phase4/private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(repo/'build/phase4/private/c07-known_hosts'),'-oBatchMode=yes','-oConnectTimeout=8','root@'+str(a.host)]
def remote(label,code,timeout=35):
 (stage/(label+'.sh')).write_text(code)
 r=subprocess.run(ssh+['sh -s'],input=code,capture_output=True,text=True,timeout=timeout)
 for suffix,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/(label+'.'+suffix)).write_text(value)
 assert r.returncode==0,(label,r.stdout,r.stderr,stage)
 return r.stdout
common='''set -eu
[ "$(id -u)" = 0 ];[ "$(readlink /proc/1/exe)" = /bin/busybox ]
[ "$(readlink /proc/self/ns/mnt)" = "$(readlink /proc/1/ns/mnt)" ]
[ "$(uname -r)" = 4.4.189-muos-r35s-p4 ]
[ "$(tr -d '\\000' < /sys/firmware/devicetree/base/model)" = 'R36S-V12 2023-08-18 Panel 0' ]
[ "$(cat /proc/sys/kernel/tainted)" = 0 ];[ "$(stat -c '%u:%g:%a' /)" = 0:0:755 ]
findmnt -rn -o OPTIONS / | tr ',' '\\n' | grep -qx ro
. /usr/libexec/muos-diag-card-guard
[ "$(diag_card /sys)" = /dev/mmcblk0p1 ]
[ "$(findmnt -rn -o MAJ:MIN,FSTYPE,PARTUUID /)" = "$(cat /sys/class/block/mmcblk0p2/dev) ext4 4d554432-02" ]
! findmnt -rn -M /boot >/dev/null;! findmnt -rn -S /dev/mmcblk0p3 >/dev/null
[ -f /run/muos/entropy/stopped ];[ ! -e /run/muos/entropy/ready ]
[ ! -e /var/lib/muos-diagnostic/c12.once ];[ ! -d /sys/module/btusb ]
for n in muxfrontend muhotkey muinput pipewire wireplumber dbus-daemon mulog;do ! pidof "$n" >/dev/null;done
/usr/libexec/muos-c07-network status
'''
before=common+f'''[ "$(cat /var/lib/muos-diagnostic/boot-seq)" = {plan['boot_sequence']} ]
sha256sum -c /usr/libexec/muos-session/prerequisites.sha256 >/dev/null
'''
def descriptor():
 d=json.loads((stage/'backup-descriptor.json').read_text());path=Path(d['path']);assert path.is_relative_to(repo/'build/phase4/private') and sha(path)==d['sha256'];return d
if a.operation=='backup':
 assert not (stage/'backup-descriptor.json').exists()
 names=[r['path'] for r in plan['files'] if r['before']['type']=='F'];assert names
 command=before+'cd /\ntar -cf - '+' '.join(names)+'\n'
 (stage/'backup-request.sh').write_text(command)
 r=subprocess.run(ssh+['sh -s'],input=command.encode(),capture_output=True,timeout=40)
 assert r.returncode==0,r.stderr.decode()
 expected={r['path']:r['before'] for r in plan['files'] if r['before']['type']=='F'};found={}
 with tarfile.open(fileobj=io.BytesIO(r.stdout)) as archive:
  for member in archive.getmembers():
   assert member.isfile() and member.name in expected and member.name not in found
   data=archive.extractfile(member).read();b=expected[member.name]
   assert hashlib.sha256(data).hexdigest()==b['sha256'] and member.mode==b['mode'] and member.uid==member.gid==0,member.name
   found[member.name]=True
 assert set(found)==set(expected)
 private=Path(tempfile.mkdtemp(prefix='c24-backup.',dir=repo/'build/phase4/private'));private.chmod(0o700);path=private/'original-files.tar'
 with path.open('wb') as stream:os.fchmod(stream.fileno(),0o600);stream.write(r.stdout);stream.flush();os.fsync(stream.fileno())
 fd=os.open(private,os.O_RDONLY|os.O_DIRECTORY);os.fsync(fd);os.close(fd)
 (stage/'backup-descriptor.json').write_text(json.dumps({'path':str(path),'sha256':sha(path),'selected_existing_files':len(found),'private_state_bytes_copied':False},indent=2)+'\n')
 print('C24 independent backup verified and synced:',len(found),'selected public originals; no device writes')
else:
 descriptor()
 if a.operation=='rollback':
  d=descriptor()
  directory=remote('recovery-allocate',common+'umask 077\nmktemp -d /run/muos-c24.XXXXXX\n').strip();assert re.fullmatch(r'/run/muos-c24\.[A-Za-z0-9]{6}',directory)
  (stage/'recovery-directory').write_text(directory+'\n')
  for name,data in [('deployment.tar',(stage/'deployment.tar').read_bytes()),('rollback.tar',Path(d['path']).read_bytes())]:
   r=subprocess.run(ssh+['cat > '+directory+'/'+name],input=data,capture_output=True,timeout=30);assert r.returncode==0
  remote('recovery-unpack',f'''set -eu
printf '%s  %s\\n' {meta['deployment_sha256']} {directory}/deployment.tar | sha256sum -c -
printf '%s  %s\\n' {d['sha256']} {directory}/rollback.tar | sha256sum -c -
tar -xf {directory}/deployment.tar -C {directory}
cd {directory};sha256sum -c SHA256SUMS >/dev/null
mkdir -m 700 payload/backup
tar -xf rollback.tar -C payload/backup
(cd payload/backup && sha256sum -c ../before.sha256 >/dev/null)
''')
  remote('recovery',f'sh {directory}/native.sh {directory} rollback\n',timeout=90)
  remote('recovery-health',common+'sha256sum -c /usr/libexec/muos-session/prerequisites.sha256 >/dev/null\necho C24_RECOVERED_OLD_FOUNDATION_CURRENT_PRIVATE_STATE_PRESERVED\n')
  print('C24 recovery completed; old public files restored; current counter/private state retained')
  raise SystemExit(0)
 if a.operation=='apply':
  checks=Path((area/'latest-update-checks').read_text().strip());cm=json.loads((checks/'analysis.json').read_text());assert cm['passed'] and cm['plan_sha256']==sha(stage/'plan.json')
  for name,digest in cm['sources'].items():assert sha(repo/name)==digest,name
  if plan['experiment']=='C24_R1_COUNTER_UMASK':
   counter=Path((area/'latest-counter-checks').read_text().strip());cr=json.loads((counter/'analysis.json').read_text());assert cr['passed']
   assert cr['source_sha256']['port/device/rk-r35s-p0/network-diagnostic/run.sh']==sha(stage/'payload/new/usr/libexec/muos-c07-run')
  assert not (stage/'remote-directory').exists(),'Never repeat a dispatched transaction'
  directory=remote('allocate',before+'umask 077\nmktemp -d /run/muos-c24.XXXXXX\n').strip();assert re.fullmatch(r'/run/muos-c24\.[A-Za-z0-9]{6}',directory)
  (stage/'remote-directory').write_text(directory+'\n')
  r=subprocess.run(ssh+['cat > '+directory+'/deployment.tar'],input=(stage/'deployment.tar').read_bytes(),capture_output=True,timeout=30);assert r.returncode==0,r.stderr
  remote('unpack',f'''set -eu
printf '%s  %s\\n' {meta['deployment_sha256']} {directory}/deployment.tar | sha256sum -c -
tar -xf {directory}/deployment.tar -C {directory}
cd {directory};sha256sum -c SHA256SUMS >/dev/null
''')
  remote('native-inspect',f'sh {directory}/native.sh {directory} inspect\n')
  remote('native-backup',f'sh {directory}/native.sh {directory} backup\n')
  infrastructure='''for name in udevd wpa_supplicant udhcpc dropbear;do
for pid in $(pidof "$name");do
[ "$(awk '/^PPid:/ {print $2}' /proc/$pid/status)" = 1 ] || continue
printf '%s %s %s\\n' "$name" "$pid" "$(awk '{print $22}' /proc/$pid/stat)"
done;done
'''
  remote('infrastructure-before',common+infrastructure)
  remote('dispatch',f'''set -eu
[ ! -e {directory}/apply.once ];[ ! -e {directory}/apply.done ]
nohup setsid sh {directory}/native.sh {directory} apply > {directory}/apply.log 2>&1 < /dev/null &
echo C24_DISPATCHED
''')
  for number in range(90):
   r=subprocess.run(ssh+[f'test -f {directory}/apply.done'],capture_output=True,timeout=15)
   if r.returncode==0:break
   time.sleep(1)
  else:raise AssertionError('C24 still pending; do not repeat; inspect remote transaction')
  result=remote('apply-result',f'cat {directory}/apply.result; cat {directory}/apply.log\n')
  assert result.splitlines()[0]=='0',('Apply failed; inspect rollback log; no reboot',stage)
  after=remote('infrastructure-after',common+infrastructure)
  assert after==(stage/'infrastructure-before.stdout').read_text(),'Network process identities changed; inspect before reboot'
 directory=(stage/'remote-directory').read_text().strip();assert re.fullmatch(r'/run/muos-c24\.[A-Za-z0-9]{6}',directory)
 health=common+'''[ "$(cat /etc/default/muos-session | sed -n 's/^enabled=//p')" = 0 ]
. /usr/libexec/muos-candidate-boot-checks
candidate_boot_check
(cd /usr/libexec/muos-session && sha256sum -c payload.sha256) >/dev/null
printf 'BOOT=';cat /var/lib/muos-diagnostic/boot-seq
printf 'BRIGHTNESS=';cat /sys/class/backlight/backlight/brightness
printf 'FOUNDATION_HASHES=';wc -l < /usr/libexec/muos-session/prerequisites.sha256
echo CANDIDATE_INSTALLED_ROOT_RO_NETWORK_OK
'''
 remote('health-after',health)
 foundation_count=len(sums(Path(plan['candidate_stage'])/'target/usr/libexec/muos-session/prerequisites.sha256'))
 (stage/'install-analysis.json').write_text(json.dumps({'passed':True,'boot_sequence':plan['boot_sequence'],'public_files_written':len(plan['files']),'root_ro':True,'private_state_preserved':True,'candidate_gate_and_foundation_hashes_passed':True,'foundation_hash_count':foundation_count,'C12_token_armed':False,'image_flashed':False,'reboot_requested':False},indent=2)+'\n')
 print('C24 directed installation verified; root RO, private state retained; no token or reboot',stage)
