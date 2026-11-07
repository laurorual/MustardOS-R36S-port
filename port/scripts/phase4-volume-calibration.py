#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Bounded speaker calibration on an owned600s C22 session, no saved changes."""
from pathlib import Path
import argparse,io,ipaddress,json,re,subprocess,tarfile,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'volume-calibration';area.mkdir(exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('operation',choices=['prepare','step','finish','collect']);p.add_argument('--host',required=True,type=ipaddress.IPv4Address);p.add_argument('--level',type=int,choices=[0,55,65,75,85,100]);p.add_argument('--codec',type=int,choices=[195,205,215,225]);p.add_argument('--rating');a=p.parse_args()
checks=Path((area/'latest-checks').read_text().strip());cm=json.loads((checks/'analysis.json').read_text());assert cm['passed']
if a.operation in ['prepare','step']:
 for n,d in cm['source_sha256'].items():assert sha(repo/n)==d
if a.operation=='prepare':s=Path(tempfile.mkdtemp(prefix='calibration.',dir=area));(area/'latest').write_text(str(s)+'\n')
else:s=Path((area/'latest').read_text().strip())
ssh=['ssh','-p','2222','-i',str(work/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(work/'private/c07-known_hosts'),'-oBatchMode=yes','root@'+str(a.host)]
def remote(label,code,timeout=30):
 (s/(label+'.sh')).write_text(code);r=subprocess.run(ssh+['sh -s'],input=code,capture_output=True,text=True,timeout=timeout)
 for suf,val in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (s/(label+'.'+suf)).write_text(val)
 assert r.returncode==0,(label,r.stdout,r.stderr,s)
 return r.stdout
def record(n,x):(s/(n+'.json')).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
base='''set -eu
export XDG_RUNTIME_DIR=/run PIPEWIRE_RUNTIME_DIR=/run
umask 077
c25_store=/var/lib/muos-diagnostic; c25_state=/run/muos/c25
. /usr/libexec/muos-c25/policy.sh; . /usr/libexec/muos-c25/card-guard.sh; . /usr/libexec/muos-c25/native.sh
c25_media; c25_root_mode ro
'''
if a.operation=='prepare':
 audio=Path((work/'audio-buffers/latest').read_text().strip());m=json.loads((audio/'session.json').read_text());g=json.loads((audio/'generation.json').read_text())['name'];assert m['lease_seconds']==600
 src=repo/'port/device/rk-r35s-p0/volume-calibration/step.sh'
 setup=remote('prepare',base+f'''[ "$(cat /run/muos/session/current)" = {g} ]
[ -f /run/muos/session/{g}/ready ]; [ "$(wpctl get-volume @DEFAULT_AUDIO_SINK@)" = 'Volume: 0.55' ]
parent=$(mktemp -d /run/muos-volcal.XXXXXX)
read paint ignored < /run/muos/session/{g}/first-paint.txt
case "$paint" in *[!0-9.]*|'') exit 64 ;; esac
echo "$((${{paint%%.*}}+570))" > "$parent/deadline"
baseline=$(jq -r .audio.codec_gain /usr/share/muos-r35s-profile/profile.json)
printf '%s %s\\n' "$parent" "$baseline"
''').strip().split();assert len(setup)==2
 d,baseline=setup;baseline=int(baseline);assert baseline in [195,205,215,225] and re.fullmatch('/run/muos-volcal[.][a-zA-Z0-9]{6}',d)
 code=src.read_text();assert code.endswith('\n')
 remote('upload',base+f"cat > {d}/step.sh <<'VOLUME_STEP'\n"+code+'VOLUME_STEP\n'+f"printf '%s  %s\\n' {sha(src)} {d}/step.sh | sha256sum -c -\nsh -n {d}/step.sh\n")
 record('manifest',{'audio_stage':str(audio),'generation':g,'directory':d,'source_sha256':sha(src),'codec_target':a.codec or baseline,'restore_codec':baseline,'boot_sequence':m['boot_sequence'],'saved_pair_unchanged':[55,70]});print('CALIBRATION_PREPARED',s);raise SystemExit(0)
m=json.loads((s/'manifest.json').read_text());d=m['directory'];g=m['generation'];assert re.fullmatch('/run/muos-volcal[.][a-zA-Z0-9]{6}',d) and re.fullmatch('run-[0-9]{4}',g)
if a.operation=='step':
 assert m['source_sha256']==sha(repo/'port/device/rk-r35s-p0/volume-calibration/step.sh'),'Never mix controller revisions in an active stage'
 assert a.level is not None and not (s/f'level-{a.level}-intent.json').exists()
 record(f'level-{a.level}-intent',{'dispatched':True,'level':a.level})
 remote(f'level-{a.level}-dispatch',base+f'''nohup setsid sh {d}/step.sh {d} {g} {a.level} {m.get('codec_target',195)} {m.get('restore_codec',195)} > {d}/level-{a.level}.log 2>&1 < /dev/null &
echo STEP_DISPATCHED
''')
 remote(f'level-{a.level}-ready',base+f'''n=0
while [ ! -f {d}/level-{a.level}/ready ]; do
 [ ! -f {d}/level-{a.level}/done ]; [ "$n" -lt 50 ];sleep .1;n=$((n+1))
done
cat {d}/level-{a.level}/volume.txt;cat {d}/level-{a.level}/window.txt
''');print('CALIBRATION_READY',a.level,flush=True)
elif a.operation=='finish':
 assert a.level is not None
 reply=remote(f'level-{a.level}-finish',base+f'''state={d}/level-{a.level}
if [ -f "$state/ready" ]; then echo STEP_ACTIVE=1; else echo STEP_ACTIVE=0; fi
echo RECEIPT_VOLUME; wpctl get-volume @DEFAULT_AUDIO_SINK@ || :
echo RECEIPT_UPTIME;cat /proc/uptime
cat "$state/window.txt"
tail -5 "$state/readback.log"
if [ ! -f "$state/done" ]; then
 read p start < "$state/manager"
 [ "$(awk '{{print $22}}' /proc/$p/stat)" = "$start" ]
 tr '\\000' '\\n' < /proc/$p/cmdline | grep -Fxq {d}/step.sh
 kill -TERM "$p"
fi
n=0;while [ ! -f "$state/done" ];do [ "$n" -lt 60 ];sleep .1;n=$((n+1));done
[ "$(cat "$state/result")" = 0 ];[ "$(wpctl get-volume @DEFAULT_AUDIO_SINK@)" = 'Volume: 0.55' ]
cat "$state/report.txt"
''')
 held='STEP_ACTIVE=1\nRECEIPT_VOLUME\nVolume: '+f'{a.level/100:.2f}'+'\n' in reply
 record(f'level-{a.level}-observation',{'level':a.level,'user_rating':a.rating,'target_held_at_receipt':held,'restored55':True});print('CALIBRATION_RESTORED55',a.level,'timing_confirmed',held)
else:
 remote('final',base+'''c25_ready
echo CALIBRATION_SESSION_STOPPED_ROOT_RO_NO_AUDIO
''')
 observations=[json.loads(f.read_text()) for f in sorted(s.glob('level-*-observation.json'))]
 levels=sorted(v['level'] for v in observations); names=['step.sh','deadline']
 for level in levels:
  assert level in [0,55,65,75,85,100]
  names += [f'level-{level}/'+n for n in ['report.txt','volume.txt','window.txt','readback.log','result','manager']]
  if m.get('codec_target',195)!=m.get('restore_codec',195):names += [f'level-{level}/codec-active.txt',f'level-{level}/codec-restored.txt']
 code=base+'c25_ready\n'+f'cd {d}\ntar -cf - '+' '.join(names)+'\n'
 (s/'collection.sh').write_text(code)
 r=subprocess.run(ssh+['sh -s'],input=code.encode(),capture_output=True,timeout=30);assert r.returncode==0,r.stderr
 target=s/'collected';target.mkdir(exist_ok=True)
 with tarfile.open(fileobj=io.BytesIO(r.stdout)) as archive:
  seen=set()
  for member in archive.getmembers():
   assert member.isfile() and member.name in names and member.name not in seen and member.size<65536
   f=target/member.name;f.parent.mkdir(parents=True,exist_ok=True);data=archive.extractfile(member).read()
   if f.exists():assert f.read_bytes()==data
   else:f.write_bytes(data)
   seen.add(member.name)
 assert seen==set(names) and sha(target/'step.sh')==m['source_sha256']
 record('analysis',{'passed':True,'saved_pair':[55,70],'points':levels,'all_five_points_observed':set(levels)=={0,65,75,85,100} and all(v.get('target_held_at_receipt') for v in observations),'hardware_gain_permanently_changed_by_controller':False,'hardware_gain_tested':m.get('codec_target',195),'absolute_SPL_measured':False})
 print('CALIBRATION_COLLECTED',s)
