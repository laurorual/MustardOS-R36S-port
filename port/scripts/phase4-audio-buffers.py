#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C26 bounded C22 audio experiment; RAM only, pinned SSH, no reboot/token."""
from pathlib import Path
import argparse, io, ipaddress, json, re, subprocess, tarfile, tempfile
from phase4_candidate import sha,sums

repo=Path(__file__).resolve().parents[2]; work=repo/'build/phase4'
area=work/'audio-buffers'; area.mkdir(exist_ok=True)
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('operation',choices=['start','snapshot','monitor','rate-cycle','stop','collect'])
p.add_argument('--host',type=ipaddress.IPv4Address,required=True)
p.add_argument('--stage',type=Path); p.add_argument('--label',default='baseline')
p.add_argument('--quantum',type=int,choices=[0,1024],default=0)
p.add_argument('--gain',type=int,choices=[157,195],default=157)
p.add_argument('--lease',type=int,choices=[300,600],default=300)
p.add_argument('--irq-scheduling',action='store_true',help='C30: one RAM WirePlumber sink override, no installed file changed')
p.add_argument('--alsa-rw',action='store_true',help='C33: RAM-only disable-mmap on the installed IRQ policy')
a=p.parse_args(); assert re.fullmatch('[a-z][a-z0-9-]{0,39}',a.label)
assert a.gain==157 or a.quantum==1024,'Gain trial requires the observed clean quantum'
assert not a.irq_scheduling or (a.operation=='start' and a.quantum==0 and a.gain==157),'IRQ trial starts from the native quantum/gain'
assert not a.alsa_rw or (a.operation=='start' and a.quantum==0 and a.gain==157 and not a.irq_scheduling),'RW trial starts from the native quantum/gain/IRQ'
if a.operation=='start':
 assert a.stage is None
 s=Path(tempfile.mkdtemp(prefix='session.',dir=area)); (area/'latest').write_text(str(s)+'\n')
 (s/'runner-source.py').write_bytes(Path(__file__).read_bytes())
else:
 s=a.stage.resolve() if a.stage else Path((area/'latest').read_text().strip())
 assert s.is_relative_to(area)
ssh=['ssh','-p','2222','-i',str(work/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(work/'private/c07-known_hosts'),'-oBatchMode=yes','-oConnectTimeout=8','root@'+str(a.host)]
def remote(label,code,timeout=40,required=True,public_stdout=True):
 (s/(label+'.sh')).write_text(code)
 r=subprocess.run(ssh+['sh -s'],input=code,capture_output=True,text=True,timeout=timeout)
 for suffix,value in [('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (s/(label+'.'+suffix)).write_text(value)
 if public_stdout: (s/(label+'.stdout')).write_text(r.stdout)
 if required: assert r.returncode==0,(label,r.stdout[-3000:],r.stderr,s)
 return r
def record(name,obj): (s/(name+'.json')).write_text(json.dumps(obj,indent=2)+'\n')
common='''set -eu
export PATH=/opt/muos/frontend:/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
export XDG_RUNTIME_DIR=/run PIPEWIRE_RUNTIME_DIR=/run
umask 077
c25_store=/var/lib/muos-diagnostic; c25_state=/run/muos/c25
. /usr/libexec/muos-c25/policy.sh
. /usr/libexec/muos-c25/card-guard.sh
. /usr/libexec/muos-c25/native.sh
c25_media; c25_root_mode ro
[ ! -e "$c25_store/c25.once" ]; [ ! -L "$c25_store/c25.once" ]
[ -f /run/muos/entropy/stopped ]; [ ! -e /run/muos/entropy/ready ]
/usr/libexec/muos-c07-network status
'''
infrastructure='''for n in udevd wpa_supplicant udhcpc dropbear; do
for p in $(pidof "$n"); do
[ "$(awk '/^PPid:/ {print $2}' /proc/$p/status)" = 1 ] || continue
printf '%s %s %s\\n' "$n" "$p" "$(awk '{print $22}' /proc/$p/stat)"
done; done
'''
if a.operation=='start':
 boot=int(remote('preflight',common+'''c25_ready
(cd /usr/libexec/muos-session && sha256sum -c payload.sha256) >/dev/null
cat /var/lib/muos-diagnostic/boot-seq
''').stdout.strip())
 directory=remote('allocate',common+'c25_ready\nmktemp -d /run/muos-c26.XXXXXX\n').stdout.strip()
 assert re.fullmatch('/run/muos-c26[.][a-zA-Z0-9]{6}',directory)
 record('session',{'boot_sequence':boot,'directory':directory,'pair':[55,70],'lease_seconds':a.lease,'manual_quantum_override':a.quantum or None,'manual_codec_gain_override':a.gain if a.gain!=157 else None,'source_sha256':sha(Path(__file__)),'persistent_code_changed_by_runner':False})
 remote('infrastructure-before',common+infrastructure)
 remote('prepare',common+f'''cat > {directory}/session.conf <<'CONF'
enabled=1
preferences_enabled=1
lease_seconds={a.lease}
profile_dir=/usr/share/muos-r35s-profile
prerequisites=/usr/libexec/muos-session/prerequisites.sha256
CONF
chmod 600 {directory}/session.conf
''')
 start_command=f'MUOS_SESSION_CONFIG={directory}/session.conf /usr/libexec/muos-session/service.sh start\n'
 if a.irq_scheduling or a.alsa_rw:
  original=repo/'port/device/rk-r35s-p0/core-wireplumber.conf'
  text=original.read_text(); needle='      api.alsa.period-size = 1024\n'; assert text.count(needle)==1
  if a.alsa_rw:
   assert text.count('      api.alsa.disable-tsched = true\n')==1 and 'api.alsa.disable-mmap' not in text
   setting='      api.alsa.disable-mmap = true\n'
  else:
   assert 'api.alsa.disable-tsched' not in text,'IRQ policy already selected in source; use normal startup after installation'
   setting='      api.alsa.disable-tsched = true\n'
  trial=text.replace(needle,setting+needle)
  wrapper=repo/'port/device/rk-r35s-p0/audio-buffers/irq-session.sh'
  (s/'irq-wireplumber.conf').write_text(trial); (s/'irq-session.sh').write_bytes(wrapper.read_bytes())
  record('irq-configuration',{'temporary_only':True,'original_sha256':sha(original),'trial_sha256':sha(s/'irq-wireplumber.conf'),'source_sha256':sha(wrapper),'delta':setting.strip()+' on the RK817 playback node','native_profile_gain':215,'native_quantum':1024})
  remote('irq-prepare',common+f"printf '%s  %s\\n' {sha(original)} /opt/muos/device/control/wireplumber.conf | sha256sum -c -\n"+f"cat > {directory}/wireplumber.conf <<'C30_WP_CONFIG'\n"+trial+'C30_WP_CONFIG\n'+f"cat > {directory}/irq-session.sh <<'C30_IRQ_WRAPPER'\n"+wrapper.read_text()+'C30_IRQ_WRAPPER\n'+f"printf '%s  %s\\n' {sha(original)} /opt/muos/device/control/wireplumber.conf > {directory}/original-wp.sha256\n"+f"printf '%s  %s\\n' {sha(wrapper)} {directory}/irq-session.sh {sha(s/'irq-wireplumber.conf')} {directory}/wireplumber.conf | sha256sum -c -\n/bin/sh -n {directory}/irq-session.sh\n")
  if a.alsa_rw:
   current=Path((work/'rootfs-candidate/latest-update').read_text().strip())
   plan=json.loads((current/'plan.json').read_text()); assert json.loads((current/'install-analysis.json').read_text())['passed']
   foundation=Path(plan['candidate_stage'])/'target/usr/libexec/muos-session/prerequisites.sha256'
   records=sums(foundation);assert len(records)==97
   assert records['/opt/muos/device/control/wireplumber.conf']==sha(original)
   records['/opt/muos/device/control/wireplumber.conf']=sha(s/'irq-wireplumber.conf')
   altered=''.join(d+'  '+n+'\n' for n,d in records.items());(s/'trial-foundation.sha256').write_text(altered)
   remote('trial-foundation',common+f"printf '%s  %s\\n' {sha(foundation)} /usr/libexec/muos-session/prerequisites.sha256 | sha256sum -c -\nprintf '%s  %s\\n' {sha(foundation)} /usr/libexec/muos-session/prerequisites.sha256 > {directory}/original-foundation.sha256\ncat > {directory}/trial-foundation.sha256 <<'C33_FOUNDATION'\n"+altered+'C33_FOUNDATION\n'+f"printf '%s  %s\\n' {sha(s/'trial-foundation.sha256')} {directory}/trial-foundation.sha256 | sha256sum -c -\n")
  start_command=f'/usr/libexec/muos-session/mount-namespace /bin/sh {directory}/irq-session.sh {directory}\n'
 record('start-intent',{'dispatched':True,'boot_sequence':boot})
 r=remote('start',common+start_command,timeout=135,required=False)
 generation=remote('generation','cat /run/muos/session/current\n').stdout.strip()
 assert re.fullmatch('run-[0-9]{4}',generation)
 record('generation',{'name':generation})
 assert r.returncode==0,('Startup failed; collect stopped generation, never repeat start',s)
 if a.quantum:
  remote('quantum',common+f'''[ "$(cat /run/muos/session/current)" = {generation} ]
[ -f /run/muos/session/{generation}/ready ]
pw-metadata -n settings 0 clock.force-quantum 1024
pw-metadata -n settings 0 clock.force-quantum
echo CHANGE_UPTIME; cat /proc/uptime
''')
 if a.gain!=157:
  remote('codec-gain',common+f'''[ "$(cat /run/muos/session/current)" = {generation} ]
[ -f /run/muos/session/{generation}/ready ]
amixer -c 0 cget name='Playback Volume'
amixer -c 0 cset name='Playback Volume' 195,195
amixer -c 0 cget name='Playback Volume'
''')
 print('C26_READY',boot,generation,s,flush=True)
 raise SystemExit(0)
meta=json.loads((s/'session.json').read_text()); generation=json.loads((s/'generation.json').read_text())['name']
assert re.fullmatch('run-[0-9]{4}',generation)
directory=meta['directory']; assert re.fullmatch('/run/muos-c26[.][a-zA-Z0-9]{6}',directory)
cycle='/run/muos/session/'+generation
identity=common+f'''[ "$(cat /var/lib/muos-diagnostic/boot-seq)" = {meta['boot_sequence']} ]
[ "$(cat /run/muos/session/current)" = {generation} ]
cmp {directory}/session.conf {cycle}/run.conf
'''
active=identity+f'''package=/usr/libexec/muos-session; base=/run/muos/session
. "$package/control-functions.sh"; session_current; session_identity "$cycle"
[ -f {cycle}/ready ]; [ ! -e {cycle}/done ]
[ "$(cat /sys/class/backlight/backlight/brightness)" = 70 ]
'''
if a.operation=='rate-cycle':
 source=repo/'port/device/rk-r35s-p0/audio-buffers/rate-cycle.sh'
 assert not (s/'rate-cycle-intent.json').exists(),'Do not repeat a dispatched rate cycle'
 code=source.read_text();(s/'rate-cycle-native.sh').write_text(code)
 remote('rate-cycle-prepare',active+f"cat > {directory}/rate-cycle.sh <<'C32_RATE_CYCLE'\n"+code+'C32_RATE_CYCLE\n'+f"printf '%s  %s\\n' {sha(source)} {directory}/rate-cycle.sh | sha256sum -c -\n/bin/sh -n {directory}/rate-cycle.sh\n")
 record('rate-cycle-intent',{'source_sha256':sha(source),'rates':[48000,0],'saved_settings_changed':False,'generation':generation})
 r=remote('rate-cycle',active+f'/usr/libexec/muos-session/bin/muos-run-bounded 25 /bin/sh {directory}/rate-cycle.sh {generation}\n',timeout=32,required=False)
 record('rate-cycle-result',{'completed':r.returncode==0,'exit_code':r.returncode,'source_sha256':sha(source),'persistent_change':False})
 assert r.returncode==0,('Inspect rate-cycle transcript and restore; do not repeat',s)
 print('C32_RATE_CYCLE_COLLECTED',s,flush=True)
elif a.operation=='monitor':
 source=repo/'port/device/rk-r35s-p0/audio-buffers/monitor.sh'
 assert not (s/'monitor-intent.json').exists()
 code=source.read_text(); assert code.endswith('\n')
 remote('monitor-install',active+f"cat > {directory}/monitor.sh <<'C26_MONITOR_SCRIPT'\n"+code+'C26_MONITOR_SCRIPT\n'+f"printf '%s  %s\\n' {sha(source)} {directory}/monitor.sh | sha256sum -c -\n/bin/sh -n {directory}/monitor.sh\n")
 record('monitor-intent',{'source_sha256':sha(source),'sink':'alsa_output.platform-rk817-sound.playback.0.0','capture_microphone':False})
 remote('monitor-dispatch',active+f'nohup setsid sh {directory}/monitor.sh {directory} {generation} > {directory}/monitor.log 2>&1 < /dev/null &\necho C26_MONITOR_STARTED\n')
 print('C26_MONITOR_STARTED',s,flush=True)
elif a.operation=='snapshot':
 assert not (s/(a.label+'.json')).exists(),'Snapshot labels are immutable'
 remote(a.label+'-audio',active+f'''echo UPTIME; cat /proc/uptime
echo SOFTWARE_VOLUME; wpctl get-volume @DEFAULT_AUDIO_SINK@
echo CODEC; amixer -c 0 cget name='Playback Volume'; amixer -c 0 cget name='Playback Path'
echo NATIVE_QUANTUM; [ ! -f /run/muos/core/quantum.txt ] || cat /run/muos/core/quantum.txt
echo PCM; cat /proc/asound/card0/pcm0p/sub0/hw_params; cat /proc/asound/card0/pcm0p/sub0/status
echo THREADS
for name in pipewire wireplumber muxfrontend; do
 for pid in $(pidof "$name"); do
  echo "PROCESS=$name PID=$pid"
  for f in /proc/$pid/task/*/stat; do cat "$f"; done
 done
done
echo PIPEWIRE_LOG; tail -c 131072 /run/muos/core/pipewire.log
''')
 r=remote(a.label+'-graph',active+'pw-dump\n',public_stdout=False)
 # The raw dump stays in RAM; persist only audio graph fields, not client/user properties.
 data=json.loads(r.stdout); result=[]; ids=[]
 for obj in data:
  kind=obj.get('type',''); info=obj.get('info',{}); props=info.get('props',{})
  if kind not in ['PipeWire:Interface:Node','PipeWire:Interface:Port','PipeWire:Interface:Link','PipeWire:Interface:Metadata']: continue
  if kind=='PipeWire:Interface:Metadata': continue
  selected={k:v for k,v in props.items() if k.startswith(('audio.','api.alsa.','clock.','node.','port.','format.')) or k in ['media.class','media.name','factory.name','library.name','object.serial']}
  item={'id':obj['id'],'type':kind,'props':selected,'state':info.get('state'),'params':{k:v for k,v in info.get('params',{}).items() if k in ['Format','Buffers','Latency','ProcessLatency']}}
  if kind=='PipeWire:Interface:Link': item.update({k:v for k,v in info.items() if k in ['output-node-id','output-port-id','input-node-id','input-port-id','format']})
  result.append(item)
  if kind in ['PipeWire:Interface:Node','PipeWire:Interface:Port']:
   oid=int(obj['id']); assert 0<=oid<10000; ids.append(oid)
 # Remove unfiltered dump output before anything can be packaged.
 record(a.label+'-graph',result)
 code=active+'pw-metadata -n settings\n'
 for oid in ids:
  code+=f'echo OBJECT={oid}\npw-cli enum-params {oid} Buffers || :\n'
 remote(a.label+'-buffers',code,timeout=45)
 remote(a.label+'-profiler',active+f'''mkdir -m 700 {directory}/{a.label}-profiler
cd {directory}/{a.label}-profiler
rc=0; /usr/libexec/muos-session/bin/muos-run-bounded 3 pw-profiler -o samples.tsv > client.log 2>&1 || rc=$?
echo PROFILER_RC=$rc
cat client.log
[ ! -f samples.tsv ] || {{ echo SAMPLES; head -100 samples.tsv; }}
''',timeout=12)
 out=(s/(a.label+'-audio.stdout')).read_text(); warnings=[v for v in out.splitlines() if 'out of buffers on port' in v]
 record(a.label,{'captured':True,'warning_lines_in_bounded_log':len(warnings),'warning_lines_are_not_xrun_count':True,'graph_ids':ids,'boot_sequence':meta['boot_sequence'],'generation':generation})
 print('C26_SNAPSHOT',a.label,'warning_lines',len(warnings),s,flush=True)
elif a.operation=='stop':
 remote('stop',identity+'/usr/libexec/muos-session/service.sh stop\n',timeout=115)
 print('C26_STOPPED',s,flush=True)
else:
 health=identity+f'''[ -f {cycle}/done ]; [ "$(cat {cycle}/result)" = 0 ]
c25_ready
[ "$(cat /sys/class/backlight/backlight/brightness)" = 80 ]
'''
 remote('health',health+'echo C26_STOPPED_ROOT_RO_CURRENT_FOUNDATION_NO_GLOBAL_DATA_MOUNT\n')
 after=remote('infrastructure-after',health+infrastructure).stdout
 assert after==(s/'infrastructure-before.stdout').read_text()
 names=['result','report.txt','prepare.log','start.log','stop.log','restore.log','checkpoint.log','preferences-loaded.txt','preferences-saved.txt','brightness-before.txt','brightness-after.txt','mixer-before.txt','mixer-after.txt','drm-before.txt','drm-after.txt','volume-before.sha256','volume-after.sha256','wireplumber-before.sha256','wireplumber-after.sha256','ui-identity.txt','software-volume.txt']
 r=subprocess.run(ssh+['sh -s'],input=(health+f'cd {cycle}\ntar -cf - '+' '.join(names)+'\n').encode(),capture_output=True,timeout=40); assert r.returncode==0,r.stderr
 out=s/'collected'; out.mkdir(exist_ok=True)
 with tarfile.open(fileobj=io.BytesIO(r.stdout)) as archive:
  seen=set()
  for member in archive.getmembers():
   assert member.isfile() and member.name in names and member.name not in seen and member.size<524288
   content=archive.extractfile(member).read(); path=out/member.name
   if path.exists(): assert path.read_bytes()==content
   else: path.write_bytes(content)
   seen.add(member.name)
 assert seen==set(names)
 for stem,suffix in [('mixer','.txt'),('drm','.txt'),('volume','.sha256'),('wireplumber','.sha256')]:
  assert (out/(stem+'-before'+suffix)).read_bytes()==(out/(stem+'-after'+suffix)).read_bytes()
 pair='MUOS-PREFS-1\nVOLUME=55\nBRIGHTNESS=70\n'
 assert (out/'preferences-loaded.txt').read_text()==(out/'preferences-saved.txt').read_text()==pair
 record('analysis',{'passed':True,'cleanup_and_preferences_qualified':True,'audio_quality_qualified':False,'root_ro':True,'network_process_identities_preserved':True,'no_reboot_or_token':True,'source_sha256':sha(Path(__file__))})
 print('C26_COLLECTED_CLEAN',s,flush=True)
