#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C30 two-file IRQ-policy plan after a physically approved RAM experiment."""
from pathlib import Path
import argparse, ipaddress, json, shutil, subprocess, tempfile
from phase4_candidate import sha, sums, validate
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'rootfs-candidate'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',type=ipaddress.IPv4Address,required=True);p.add_argument('--trial',type=Path,required=True);a=p.parse_args()
trial=a.trial.resolve();assert trial.is_relative_to(work/'audio-buffers')
observation=json.loads((trial/'physical-observation.json').read_text())
assert observation['sound_clean_and_audible'] is True
assert json.loads((trial/'analysis.json').read_text())['passed']
config=json.loads((trial/'irq-configuration.json').read_text())
assert sha(trial/'irq-wireplumber.conf')==config['trial_sha256']
source=repo/'port/device/rk-r35s-p0/core-wireplumber.conf'
assert source.read_bytes()==(trial/'irq-wireplumber.conf').read_bytes()
old=Path((area/'latest-update').read_text().strip());previous=json.loads((old/'plan.json').read_text())
assert previous['experiment'] in ['C27_VOLUME_CALIBRATION','C30_ALSA_IRQ']
rw=previous['experiment']=='C30_ALSA_IRQ'
assert json.loads((old/'install-analysis.json').read_text())['passed']
base=Path(previous['candidate_stage']);candidate=Path(tempfile.mkdtemp(prefix='c30-source.',dir=area))
root=candidate/'target';shutil.copytree(base/'target',root,symlinks=True)
name='opt/muos/device/control/wireplumber.conf';assert sha(root/name)==config['original_sha256']
shutil.copyfile(source,root/name)
foundation=root/'usr/libexec/muos-session/prerequisites.sha256';records=sums(foundation)
assert len(records)==(97 if rw else 96)
if rw:assert '/'+name in records and 'api.alsa.disable-mmap = true' in source.read_text()
else:assert '/'+name not in records
records['/'+name]=sha(root/name)
foundation.write_text(''.join(sha(root/n.lstrip('/'))+'  '+n+'\n' for n in records))
analysis=validate(root);assert analysis['foundation_files']==97 and analysis['ALSA_irq_scheduling']
changed=[name,'usr/libexec/muos-session/prerequisites.sha256']
stage=Path(tempfile.mkdtemp(prefix='c30-update.',dir=area))
code='''set -eu
c25_store=/var/lib/muos-diagnostic; c25_state=/run/muos/c25
. /usr/libexec/muos-c25/policy.sh
. /usr/libexec/muos-c25/card-guard.sh
. /usr/libexec/muos-c25/native.sh
c25_ready
[ ! -e "$c25_store/c25.once" ]; [ ! -L "$c25_store/c25.once" ]
printf 'BOOT %s\\n' "$(cat "$c25_store/boot-seq")"
'''
for name in changed:
 code+=f'''[ -f /{name} ];[ ! -L /{name} ];[ "$(stat -c '%u:%g:%h' /{name})" = 0:0:1 ]
printf 'F %s %s {name}\\n' "$(stat -c %a /{name})" "$(sha256sum /{name} | cut -d' ' -f1)"
'''
ssh=['ssh','-p','2222','-i',str(work/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(work/'private/c07-known_hosts'),'-oBatchMode=yes','root@'+str(a.host),'sh -s']
r=subprocess.run(ssh,input=code,text=True,capture_output=True,timeout=30)
for ext,value in [('sh',code),('stdout',r.stdout),('stderr',r.stderr)]: (stage/('survey.'+ext)).write_text(value)
assert r.returncode==0,(stage,r.stdout,r.stderr)
lines=r.stdout.splitlines();boot=int(lines.pop(0).split()[1]);rows=[]
for line in lines:
 kind,mode,digest,name=line.split();assert kind=='F' and digest==sha(base/'target'/name),name
 rows.append({'path':name,'before':{'type':'F','mode':int(mode,8),'sha256':digest},'after':{'type':'file','mode':(root/name).stat().st_mode&0o777,'sha256':sha(root/name)}})
sources=[Path(__file__),repo/'port/scripts/phase4_candidate.py',source]
pins={str(f.relative_to(repo)):sha(f) for f in sources}
analysis.update({'revision':'C33' if rw else 'C30','new_ELF':False,'image_built':False,'sources':pins,'RAM_trial':str(trial),'RAM_trial_sha256':sha(trial/'physical-observation.json')})
(candidate/'analysis.json').write_text(json.dumps(analysis,indent=2)+'\n')
plan={'schema':1,'experiment':'C33_ALSA_RW' if rw else 'C30_ALSA_IRQ','candidate_stage':str(candidate),'candidate_analysis_sha256':sha(candidate/'analysis.json'),'boot_sequence':boot,'files':rows,'new_directories':[],'already_current_skipped':[],'factory_counter_excluded':True,'private_state_or_p3_in_payload':False,'reboot_requested':False,'previous_update_stage':str(old),'source_sha256':pins}
(stage/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
(stage/'foundation-before-source.sha256').write_bytes((base/'target/usr/libexec/muos-session/prerequisites.sha256').read_bytes())
(area/'latest-update').write_text(str(stage)+'\n');print('C30 IRQ plan, two public files; no device writes:',stage)
