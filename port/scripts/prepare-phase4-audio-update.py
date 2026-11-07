#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C26 directed profile/S95 update; no token, no new ELF or rootfs flash."""
from pathlib import Path
import argparse, ipaddress, json, shutil, subprocess, tempfile
from phase4_candidate import sha,sums
repo=Path(__file__).resolve().parents[2]; work=repo/'build/phase4'; area=work/'rootfs-candidate'
p=argparse.ArgumentParser();p.add_argument('--host',required=True,type=ipaddress.IPv4Address);a=p.parse_args()
old=Path((area/'latest-update').read_text().strip());op=json.loads((old/'plan.json').read_text());assert op['experiment']=='C26_AUDIO_BUFFERS'
base=Path(op['candidate_stage']); checks=Path((work/'runtime-profile/latest-checks').read_text().strip());report=json.loads((checks/'report.json').read_text());assert report['passed']
qc=Path((work/'audio-buffers/latest-quantum-checks').read_text().strip());q=json.loads((qc/'analysis.json').read_text());assert q['passed']
for name,digest in q['source_sha256'].items():assert sha(repo/name)==digest
candidate=Path(tempfile.mkdtemp(prefix='c26-source.',dir=area));root=candidate/'target';shutil.copytree(base/'target',root,symlinks=True)
profile=root/'usr/share/muos-r35s-profile';shutil.copytree(checks/'recipe-target/usr/share/muos-r35s-profile',profile,dirs_exist_ok=True)
r=subprocess.run(['python3','-B',str(repo/'port/scripts/apply-phase4-runtime-profile.py'),'--target',str(root)],capture_output=True,text=True);assert r.returncode==0,(r.stdout,r.stderr)
shutil.copyfile(repo/'port/device/rk-r35s-p0/S95muos-core',root/'etc/init.d/S95muos-core');(root/'etc/init.d/S95muos-core').chmod(0o755)
source=root/'usr/libexec/muos-session/profile-source.sha256';source.write_text(''.join(sha(f)+'  '+str(f.relative_to(profile))+'\n' for f in sorted(profile.rglob('*')) if f.is_file()))
payload=root/'usr/libexec/muos-session/payload.sha256';records=sums(payload);payload.write_text(''.join(sha(root/'usr/libexec/muos-session'/n)+'  '+n+'\n' for n in records))
foundation=root/'usr/libexec/muos-session/prerequisites.sha256';records=sums(foundation);assert len(records)==96
foundation.write_text(''.join(sha(root/n.lstrip('/'))+'  '+n+'\n' for n in records))
changed=[]
for f in sorted(root.rglob('*')):
 if not f.is_file() or f.is_symlink():continue
 n=str(f.relative_to(root));before=base/'target'/n
 if not before.exists() or sha(before)!=sha(f):changed.append(n)
assert len(changed)==8,changed
changed.remove('usr/libexec/muos-session/prerequisites.sha256');changed.append('usr/libexec/muos-session/prerequisites.sha256')
stage=Path(tempfile.mkdtemp(prefix='c26-update.',dir=area))
code='''set -eu
c25_store=/var/lib/muos-diagnostic; c25_state=/run/muos/c25
. /usr/libexec/muos-c25/policy.sh; . /usr/libexec/muos-c25/card-guard.sh; . /usr/libexec/muos-c25/native.sh
c25_ready
[ ! -e /var/lib/muos-diagnostic/c25.once ]; [ ! -e /var/lib/muos-diagnostic/c12.once ]
printf 'BOOT %s\\n' "$(cat /var/lib/muos-diagnostic/boot-seq)"
'''
for name in changed:code+=f'''[ ! -L /{name} ]; if [ -f /{name} ]; then [ "$(stat -c '%u:%g:%h' /{name})" = 0:0:1 ]
printf 'F %s %s {name}\\n' "$(stat -c %a /{name})" "$(sha256sum /{name} | cut -d' ' -f1)"
else printf 'A 0 - {name}\\n'; fi
'''
ssh=['ssh','-p','2222','-i',str(work/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(work/'private/c07-known_hosts'),'-oBatchMode=yes','root@'+str(a.host),'sh -s']
r=subprocess.run(ssh,input=code,capture_output=True,text=True,timeout=40)
for suf,val in [('sh',code),('stdout',r.stdout),('stderr',r.stderr)]: (stage/('survey.'+suf)).write_text(val)
assert r.returncode==0,(stage,r.stdout,r.stderr)
lines=r.stdout.splitlines();boot=int(lines.pop(0).split()[1]);rows=[]
for line in lines:
 kind,mode,digest,name=line.split()
 if kind=='F':assert digest==sha(base/'target'/name),name
 else:assert kind=='A' and not (base/'target'/name).exists(),name
 rows.append({'path':name,'before':{'type':kind,'mode':int(mode,8),'sha256':digest},'after':{'type':'file','mode':(root/name).stat().st_mode&0o777,'sha256':sha(root/name)}})
sources=[Path(__file__),repo/'port/device/rk-r35s-p0/S95muos-core',repo/'port/device/rk-r35s-p0/runtime-profile.json',repo/'port/device/rk-r35s-p0/speaker-calibration.json',repo/'port/scripts/prepare-phase4-runtime-profile.py',repo/'port/scripts/check-phase4-runtime-profile.py',repo/'port/scripts/apply-phase4-runtime-profile.py',repo/'port/scripts/check-phase4-audio-quantum.py']
pins={str(f.relative_to(repo)):sha(f) for f in sources}
(candidate/'analysis.json').write_text(json.dumps({'passed':True,'revision':'C27','profile_recipe_checks_sha256':sha(checks/'report.json'),'quantum_checks_sha256':sha(qc/'analysis.json'),'base_analysis_sha256':sha(base/'analysis.json'),'foundation_hashes':96,'new_ELF':False,'image_built':False,'sources':pins},indent=2)+'\n')
plan={'schema':1,'experiment':'C27_VOLUME_CALIBRATION','candidate_stage':str(candidate),'candidate_analysis_sha256':sha(candidate/'analysis.json'),'boot_sequence':boot,'files':rows,'new_directories':[],'already_current_skipped':[],'factory_counter_excluded':True,'private_state_or_p3_in_payload':False,'reboot_requested':False,'previous_update_stage':str(old),'source_sha256':pins}
(stage/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');(stage/'foundation-before-source.sha256').write_bytes((base/'target/usr/libexec/muos-session/prerequisites.sha256').read_bytes());(area/'latest-update').write_text(str(stage)+'\n')
print('C27 calibrated eight-file plan, boot',boot,stage)
