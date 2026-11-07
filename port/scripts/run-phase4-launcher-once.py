#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C25 arm/boot/audit/fallback over pinned SSH, separate from legacy C12."""
from pathlib import Path
import argparse, io, ipaddress, json, re, subprocess, tarfile, tempfile, time
from phase4_candidate import sha
from phase4_launcher_trial import calibrated_contract

repo=Path(__file__).resolve().parents[2]; work=repo/'build/phase4'; area=work/'rootfs-candidate'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('operation',choices=['new-trial','negative','arm','request','running','collect','fallback-request','fallback-collect'])
p.add_argument('--host',required=True,type=ipaddress.IPv4Address); p.add_argument('--trial',type=Path); a=p.parse_args()
s=Path((area/'latest-update').read_text().strip()); installation=s; plan=json.loads((s/'plan.json').read_text())
assert plan['experiment'] in ['C25_LAUNCHER_ONCE','C27_VOLUME_CALIBRATION','C30_ALSA_IRQ','C33_ALSA_RW','C36_PCM_PRIME'] and json.loads((s/'install-analysis.json').read_text())['passed']
integrated=plan['experiment'] in ['C27_VOLUME_CALIBRATION','C30_ALSA_IRQ','C33_ALSA_RW','C36_PCM_PRIME']
contract=calibrated_contract(repo,area,installation,plan) if integrated else None
foundation_count=contract.get('foundation_hashes',96) if integrated else 96
assert not integrated or a.trial or a.operation=='new-trial','Calibrated boot requires its own bound trial'
backup=json.loads((s/'backup-descriptor.json').read_text()); assert sha(Path(backup['path']))==backup['sha256']
for name,digest in plan['source_sha256'].items(): assert sha(repo/name)==digest,name
checks=Path((area/'latest-c25-checks').read_text().strip()); cr=json.loads((checks/'analysis.json').read_text()); assert cr['passed']
for name,digest in cr['source_sha256'].items(): assert sha(repo/name)==digest,name
ssh=['ssh','-p','2222','-i',str(work/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(work/'private/c07-known_hosts'),'-oBatchMode=yes','-oConnectTimeout=5','root@'+str(a.host)]
before=plan['boot_sequence']
if a.trial:
 s=a.trial.resolve(); assert s.is_relative_to(area) and s.name.startswith('c25-physical.')
 tm=json.loads((s/'trial.json').read_text())
 assert tm['installation_stage']==str(installation) and tm['plan_sha256']==sha(installation/'plan.json')
 if integrated: assert tm['calibrated_contract']==contract
 else: assert tm['previous_fallback_sha256']==sha(installation/'c25-fallback.json')
 before=tm['before_boot']; assert isinstance(before,int) and before>=plan['boot_sequence']+(0 if integrated else 2)
boot=before+1; fallback=before+2
def remote(label,code,timeout=30,required=True):
 (s/(label+'.sh')).write_text(code)
 r=subprocess.run(ssh+['sh -s'],input=code,capture_output=True,text=True,timeout=timeout)
 for suffix,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (s/(label+'.'+suffix)).write_text(value)
 if required: assert r.returncode==0,(label,r.stdout,r.stderr,s)
 return r
def record(name,obj): (s/(name+'.json')).write_text(json.dumps(obj,indent=2)+'\n')
common='''set -eu
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
umask 077
c25_store=/var/lib/muos-diagnostic; c25_state=/run/muos/c25
. /usr/libexec/muos-c25/policy.sh
. /usr/libexec/muos-c25/card-guard.sh
. /usr/libexec/muos-c25/native.sh
c25_media; c25_root_mode ro; c25_foundation
[ -f /run/muos/entropy/stopped ]; [ ! -e /run/muos/entropy/ready ]
/usr/libexec/muos-c07-network status
(cd /usr/libexec/muos-session && sha256sum -c payload.sha256 >/dev/null)
(cd /usr/share/muos-r35s-profile && sha256sum -c /usr/libexec/muos-session/profile-source.sha256 >/dev/null)
'''
if integrated:
 for name,digest in contract['native_file_sha256'].items():
  assert re.fullmatch('/[a-zA-Z0-9/_.-]+',name)
  common+=f"printf '%s  %s\\n' {digest} {name} | sha256sum -c - >/dev/null\n"
def sequence(n): return f'[ "$(cat /var/lib/muos-diagnostic/boot-seq)" = {n} ]\n'
def consumed(): return f'''[ ! -e "$c25_store/c25.once" ]; [ ! -L "$c25_store/c25.once" ]
c25_matches "$c25_store/c25.used.BOOT{boot:04d}" ONCE {boot}
'''
infrastructure='''for n in udevd wpa_supplicant udhcpc dropbear; do
for p in $(pidof "$n"); do
[ "$(awk '/^PPid:/ {print $2}' /proc/$p/status)" = 1 ] || continue
printf '%s %s %s\\n' "$n" "$p" "$(awk '{print $22}' /proc/$p/stat)"
done; done
'''
if a.operation=='new-trial':
 assert not a.trial
 if not integrated:
  previous=json.loads((installation/'c25-fallback.json').read_text()); assert previous['passed']
 trial=Path(tempfile.mkdtemp(prefix='c25-physical.',dir=area)); s=trial
 r=remote('c25-repeat-survey',common+'''c25_ready
[ "$(cat /run/muos/c25/selected)" = c07 ]
[ "$(cat /run/muos/c25/select.result)" = 0 ]
case "$(cat /run/muos/c25/fallback)" in
 1) [ -f /run/muos/c25/done ]; [ "$(cat /run/muos/c25/result)" = 0 ] ;;
 0) [ ! -e /run/muos/c25/grant ]; [ ! -e /run/muos/c25/ready ] ;;
 *) exit 64 ;;
esac
[ ! -e /run/muos/c25/session.attempted ]
if [ -e /run/muos/session/current ] || [ -L /run/muos/session/current ]; then
 package=/usr/libexec/muos-session; base=/run/muos/session
 . "$package/control-functions.sh"; session_current
 [ -f "$cycle/done" ]; [ "$(cat "$cycle/result")" = 0 ]
 if session_identity "$cycle"; then exit 64; fi
fi
[ ! -e "$c25_store/c25.once" ]; [ ! -L "$c25_store/c25.once" ]
[ ! -e "$c25_store/c25.once.tmp" ]; [ ! -L "$c25_store/c25.once.tmp" ]
cat /var/lib/muos-diagnostic/boot-seq
''')
 current=int(r.stdout.strip()); assert current>=(plan['boot_sequence'] if integrated else previous['boot_sequence']) and current<9997
 meta={'schema':1,'experiment':contract['experiment'] if integrated else 'C25_PHYSICAL_REPEAT','reason':'Validate C25 boot with the bound installed audio policy, then C07 fallback' if integrated else 'User explicitly requested a repeat because absent during first visual test','installation_stage':str(installation),'plan_sha256':sha(installation/'plan.json'),'before_boot':current,'expected_boot':current+1,'expected_fallback':current+2,'reinstall_required':False,'C12_rearmed':False}
 if integrated: meta['calibrated_contract']=contract
 else: meta['previous_fallback_sha256']=sha(installation/'c25-fallback.json')
 record('trial',meta)
 (area/'latest-c25-physical').write_text(str(trial)+'\n'); print('New C25 physical trial prepared:',trial,'expected boot',current+1)
elif a.operation=='negative':
 assert not a.trial
 remote('c25-negative',common+sequence(before)+'''c25_ready
[ ! -e /run/muos/c25 ]; [ ! -e "$c25_store/c25.once" ]
rc=0; /usr/libexec/muos-c25/select.sh || rc=$?; [ "$rc" = 64 ]
rc=0; /usr/libexec/muos-c25/session.sh start || rc=$?; [ "$rc" = 64 ]
for f in /usr/libexec/muos-c25/*.sh; do /bin/sh -n "$f"; done
[ ! -e /run/muos/c25 ]; [ ! -e "$c25_store/c25.once" ]; c25_ready
echo C25_MANUAL_SELECT_AND_START_REFUSED_64_NO_TOKEN_NO_UI
''')
 record('c25-negative',{'passed':True,'select_and_start_rc':64,'persistent_write':False})
elif a.operation=='arm':
 assert not (s/'c25-arm.json').exists(),'Never repeat a dispatched arm; inspect actual state'
 code=common+sequence(before)+f'''c25_ready
[ ! -e "$c25_store/c25.once" ]; [ ! -L "$c25_store/c25.once" ]
[ ! -e "$c25_store/c25.once.tmp" ]; [ ! -L "$c25_store/c25.once.tmp" ]
[ ! -e "$c25_store/c25.used.BOOT{boot:04d}" ]; [ ! -L "$c25_store/c25.used.BOOT{boot:04d}" ]
if [ -e /run/muos/c25 ] || [ -L /run/muos/c25 ]; then
 [ ! -L /run/muos/c25 ]; [ "$(stat -c '%u:%g:%a' /run/muos/c25)" = 0:0:700 ]
 [ "$(cat /run/muos/c25/selected)" = c07 ]
 [ "$(cat /run/muos/c25/select.result)" = 0 ]
 case "$(cat /run/muos/c25/fallback)" in
  1) [ -f /run/muos/c25/done ]; [ "$(cat /run/muos/c25/result)" = 0 ] ;;
  0) [ ! -e /run/muos/c25/done ]; [ ! -e /run/muos/c25/result ] ;;
  *) exit 64 ;;
 esac
 [ ! -e /run/muos/c25/session.attempted ]; [ ! -e /run/muos/c25/grant ]; [ ! -e /run/muos/c25/ready ]
fi
if [ ! -e /run/muos/session ] && [ ! -L /run/muos/session ]; then mkdir -m 700 /run/muos/session; fi
[ -d /run/muos/session ]; [ ! -L /run/muos/session ]
[ "$(stat -c '%u:%g:%a' /run/muos/session)" = 0:0:700 ]
exec 8>/run/muos/session/lifetime.lock; flock -n 8
trap 'mount -o remount,ro /' EXIT
trap 'exit 143' HUP INT TERM
mount -o remount,rw /
(set -C; c25_record ONCE {boot} > "$c25_store/c25.once.tmp")
chmod 600 "$c25_store/c25.once.tmp"
mv "$c25_store/c25.once.tmp" "$c25_store/c25.once"
sync
mount -o remount,ro /
c25_matches "$c25_store/c25.once" ONCE {boot}
c25_ready
echo C25_ARMED_BOOT_{boot}_ROOT_RO
'''
 record('c25-arm',{'phase':'intent','expected_boot':boot,'C12_rearmed':False})
 remote('c25-arm',code)
 record('c25-arm',{'passed':True,'expected_boot':boot,'lease_seconds':180,'C12_rearmed':False,'root_ro':True,'runner_sha256':sha(Path(__file__))})
elif a.operation in ['request','fallback-request']:
 first=a.operation=='request'; label='c25-reboot' if first else 'c25-fallback-reboot'
 assert not (s/(label+'.json')).exists(),'Never repeat a dispatched reboot'
 if first:
  assert json.loads((s/'c25-arm.json').read_text())['passed']
  extra=f'c25_matches "$c25_store/c25.once" ONCE {boot}\n'
  n=before
 else:
  assert json.loads((s/'c25-collect.json').read_text())['passed']
  extra=consumed()+'''[ -f /run/muos/c25/done ]; [ "$(cat /run/muos/c25/result)" = 0 ]
'''; n=boot
 code=common+sequence(n)+'c25_ready\n'+extra
 remote(label+'-preflight',code+'sync\necho C25_NORMAL_REBOOT_PREFLIGHT_OK\n')
 record(label,{'phase':'intent','before':n,'expected_after':n+1,'normal_PID1':True})
 r=remote(label,code+'echo C25_NORMAL_PID1_REBOOT\n/sbin/reboot\n',required=False)
 assert r.returncode in (0,255),(r.stdout,r.stderr)
 record(label,{'requested':True,'before':n,'expected_after':n+1,'normal_PID1':True,'C12_rearmed':False})
 print('C25 normal reboot requested; expected boot',n+1)
elif a.operation=='running':
 code=common+sequence(boot)+consumed()+'''[ "$(cat /run/muos/c25/selected)" = c25 ]
[ -f /run/muos/c25/ready ]; [ ! -e /run/muos/c25/done ]
c25_matches /run/muos/c25/grant GRANT "$(cat "$c25_store/boot-seq")"
package=/usr/libexec/muos-session; base=/run/muos/session
. "$package/control-functions.sh"; session_current; session_identity "$cycle"
[ "$(cat /run/muos/c25/generation)" = "$generation" ]; [ -f "$cycle/ready" ]
[ "$(readlink /proc/$session_pid/ns/mnt)" != "$(readlink /proc/1/ns/mnt)" ]
awk '$5=="/" {if ($6 !~ /^ro(,|$)/) exit 1; found=1} END{if (!found) exit 1}' /proc/$session_pid/mountinfo
[ "$(cat /proc/$session_pid/root/opt/muos/config/settings/general/volume)" = 55 ]
[ "$(cat /proc/$session_pid/root/opt/muos/config/settings/general/brightness)" = 70 ]
[ "$(cat /proc/$session_pid/root/opt/muos/config/settings/advanced/volume)" = 0 ]
[ "$(cat /sys/class/backlight/backlight/brightness)" = 70 ]
printf 'MUOS-PREFS-1\\nVOLUME=55\\nBRIGHTNESS=70\\n' | cmp -s - "$cycle/preferences-loaded.txt"
grep -qx 'Volume: 0.55' "$cycle/software-volume.txt"
cat /run/muos/c25/START.TXT
echo C25_RUNNING_FIRST_PAINT_PAIR_55_70_BOTH_ROOTS_RO
'''
 if integrated:
  code+='''export PATH=/opt/muos/bin:$PATH
export XDG_RUNTIME_DIR=/run PIPEWIRE_RUNTIME_DIR=/run
amixer -c 0 cget name='Playback Volume' | grep -qx '  : values=215,215'
amixer -c 0 cget name='Playback Path' | grep -qx '  : values=3'
pw-metadata -n settings 0 clock.force-quantum | grep -F "key:'clock.force-quantum' value:'1024'"
wpctl get-volume @DEFAULT_AUDIO_SINK@ | grep -qx 'Volume: 0.55'
if grep -q 'out of buffers on port' /run/muos/core/pipewire.log; then exit 64; fi
echo C28_NATIVE_CODEC215_QUANTUM1024_VOLUME55_NO_BUFFER_WARNINGS
'''
  if contract.get('IRQ_scheduling'):
   code+='''pw-dump | jq -e '.[] | select(.type=="PipeWire:Interface:Node" and .info.props["node.name"]=="alsa_output.platform-rk817-sound.playback.0.0") | .info.props["api.alsa.disable-tsched"] == true'
echo C31_NATIVE_IRQ_SCHEDULING_CONFIRMED
'''
  if contract.get('RW_access'):
   code+='''pw-dump | jq -e '.[] | select(.type=="PipeWire:Interface:Node" and .info.props["node.name"]=="alsa_output.platform-rk817-sound.playback.0.0") | .info.props["api.alsa.disable-mmap"] == true'
grep -qx 'access: RW_INTERLEAVED' /proc/asound/card0/pcm0p/sub0/hw_params
echo C34_NATIVE_RW_CONFIRMED
'''
  if contract.get('direct_PCM_priming'):
   code+='''grep -qx DIRECT_ZERO_PCM_COMPLETED /run/muos/core/pcm-prime.txt
echo C37_NATIVE_DIRECT_ZERO_PRIME_CONFIRMED
'''
 deadline=time.monotonic()+130
 while True:
  r=remote('c25-running',code,required=False)
  if r.returncode==0: break
  assert time.monotonic()<deadline,('C25 launcher not ready; inspect, do not rearm',s,r.stdout,r.stderr)
  time.sleep(2)
 remote('c25-infrastructure-running',common+sequence(boot)+infrastructure)
 record('c25-running',{'passed':True,'boot_sequence':boot,'pair':[55,70],'both_roots_ro':True,'C12_rearmed':False,'lease_seconds':180})
 if integrated: record('c28-audio-running',{'passed':True,'boot_sequence':boot,'codec_gain':215,'quantum':1024,'software_volume':55,'buffer_warnings':0,'manual_audio_override':False})
 print('C25 launcher ready; boot',boot,'pair55/70; lease180s',flush=True)
else:
 is_fallback=a.operation=='fallback-collect'; n=fallback if is_fallback else boot
 label='c25-fallback' if is_fallback else 'c25-collect'
 assert not (s/(label+'.json')).exists(),'Proof already collected; do not overwrite'
 base=common+sequence(n)+consumed()+'''c25_ready
[ -f /run/muos/c25/done ]; [ "$(cat /run/muos/c25/result)" = 0 ]
[ "$(cat /sys/class/backlight/backlight/brightness)" = 80 ]
[ ! -e /run/muos/selection/mode ]
'''
 if is_fallback:
  base+='''[ "$(cat /run/muos/c25/selected)" = c07 ]; [ ! -e /run/muos/c25/grant ]
[ ! -e /run/muos/c25/session.attempted ]; [ ! -e /run/muos/session/current ]
grep -qx REASON=one-shot-fallback /run/muos/c25/FINAL.TXT
'''
 else: base+='''[ "$(cat /run/muos/c25/selected)" = c25 ]
grep -qx REASON=lease-completed /run/muos/c25/FINAL.TXT
'''
 deadline=time.monotonic()+370
 while True:
  r=remote(label+'-health',base+f'echo C25_QUIET_ROOT_RO_FOUNDATION{foundation_count}_TAINT0_NETWORK_OK\n',required=False)
  if r.returncode==0: break
  assert time.monotonic()<deadline,('C25 not clean; do not retry boot/arm',s,r.stdout,r.stderr)
  time.sleep(3)
 out=s/label; out.mkdir(exist_ok=True)
 def archive(name,code,allowed):
  request=out/(name+'-request.sh')
  if request.exists(): assert request.read_text()==code,'Collection request changed during resume'
  else: request.write_text(code)
  r=subprocess.run(ssh+['sh -s'],input=code.encode(),capture_output=True,timeout=30); assert r.returncode==0,r.stderr
  with tarfile.open(fileobj=io.BytesIO(r.stdout)) as t:
   seen=set()
   for m in t.getmembers():
    assert m.isfile() and m.name in allowed and m.name not in seen and m.size<524288,m
    dest=out/name/m.name; dest.parent.mkdir(parents=True,exist_ok=True); content=t.extractfile(m).read()
    if dest.exists(): assert dest.read_bytes()==content,('Existing evidence changed during collection resume',dest)
    else: dest.write_bytes(content)
    seen.add(m.name)
  return seen
 names=['START.TXT','FINAL.TXT','select.result','selected','fallback','result','done','start.log','publish.log','stop.log']
 code=base+'cd /run/muos/c25\nset --; for n in '+' '.join(names)+'; do [ ! -f "$n" ] || set -- "$@" "$n"; done; tar -cf - "$@"\n'
 archive('ram',code,set(names))
 if not is_fallback:
  names=['result','report.txt','preferences-loaded.txt','preferences-active.txt','preferences-saved.txt','brightness-before.txt','brightness-active.txt','brightness-after.txt','mixer-before.txt','mixer-after.txt','drm-before.txt','drm-after.txt','volume-before.sha256','volume-after.sha256','wireplumber-before.sha256','wireplumber-after.sha256','original-restored.txt','writer-restored.txt','first-paint.txt','ui-identity.txt','software-volume.txt']
  code=base+'''package=/usr/libexec/muos-session; base=/run/muos/session
. "$package/control-functions.sh"; session_current; [ -f "$cycle/done" ]; [ "$(cat "$cycle/result")" = 0 ]
cd "$cycle"
tar -cf - '''+' '.join(names)+'\n'
  archive('session',code,set(names))
  pair='MUOS-PREFS-1\nVOLUME=55\nBRIGHTNESS=70\n'
  for name in ['preferences-loaded.txt','preferences-saved.txt']: assert (out/'session'/name).read_text()==pair
  for stem in ['mixer','drm','volume','wireplumber']:
   suffix='.sha256' if stem in ['volume','wireplumber'] else '.txt'
   assert (out/'session'/(stem+'-before'+suffix)).read_bytes()==(out/'session'/(stem+'-after'+suffix)).read_bytes(),stem
  assert (out/'session/brightness-before.txt').read_text().strip()=='80' and (out/'session/brightness-after.txt').read_text().strip()=='80'
  infra=remote('c25-infrastructure-stopped',common+sequence(boot)+infrastructure).stdout
  assert infra==(s/'c25-infrastructure-running.stdout').read_text(),'Infrastructure changed during launcher lease'
 # Durable readback after unmount; no writes during collection.
 reports=['FINAL.TXT'] if is_fallback else ['START.TXT','FINAL.TXT']
 code=base+f'''mount -t vfat -o ro,nosuid,nodev,noexec /dev/mmcblk0p1 /boot
trap 'umount /boot' EXIT
[ "$(cat /boot/DIAG.ID)" = MUOS-R35S-EXT4-P4-B01 ]
cd /boot/DIAG25/BOOT{n:04d}
'''
 for name in reports: code+=f'cmp /run/muos/c25/{name} {name}\n'
 code+='tar -cf - '+' '.join(reports)+'\ncd /\numount /boot\ntrap - EXIT\n'
 assert archive('fat',code,set(reports))==set(reports)
 for name in reports: assert (out/'fat'/name).read_bytes()==(out/'ram'/name).read_bytes()
 health=remote(label+'-final-health',base+'''dmesg | awk '/Kernel panic|BUG:|Oops:|EXT4-fs error|I\\/O error|mmc.*timeout/ {n++} END{printf "KERNEL_STORAGE_SIGNATURES=%d\\n",n}'
echo C25_FAT_UNMOUNTED_FINAL_HEALTH_OK
''').stdout
 assert 'KERNEL_STORAGE_SIGNATURES=0' in health,health
 record(label,{'passed':True,'boot_sequence':n,'selected':'c07' if is_fallback else 'c25','foundation_hashes':foundation_count,'root_ro_0755':True,'pair':[55,70],'clean_session_and_restore':not is_fallback,'next_boot_no_UI':is_fallback,'durable_reports_match_RAM':True,'FAT_and_p3_unmounted':True,'C12_rearmed':False,'runner_sha256':sha(Path(__file__))})
 print('C25 proof collected:',label,'boot',n,flush=True)
