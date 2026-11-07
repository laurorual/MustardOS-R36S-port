#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C31 bound-installation and dispatch checks; fake SSH, no hardware."""
from pathlib import Path
import json, os, shutil, subprocess, tempfile
from phase4_candidate import sha
from phase4_launcher_trial import calibrated_contract
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/rootfs-candidate'
installed=Path((area/'latest-update').read_text().strip());plan=json.loads((installed/'plan.json').read_text())
assert plan['experiment'] in ['C30_ALSA_IRQ','C33_ALSA_RW','C36_PCM_PRIME']
prime=plan['experiment']=='C36_PCM_PRIME'
rw=plan['experiment'] in ['C33_ALSA_RW','C36_PCM_PRIME'];boot_before=plan['boot_sequence']
contract=calibrated_contract(repo,area,installed,plan)
stage=Path(tempfile.mkdtemp(prefix='irq-launcher-checks.',dir=area));fixture=stage/'fixture'
fa=fixture/'build/phase4/rootfs-candidate';fa.mkdir(parents=True)
clone=fa/'installed';clone.mkdir();candidate=fa/'candidate';previous=fa/'previous';previous.mkdir()
prior=Path(plan['previous_update_stage']);priorplan=json.loads((prior/'plan.json').read_text())
shutil.copytree(Path(plan['candidate_stage'])/'target',candidate/'target',symlinks=True)
shutil.copyfile(Path(plan['candidate_stage'])/'analysis.json',candidate/'analysis.json')
baseline=fa/'baseline';shutil.copytree(Path(priorplan['candidate_stage'])/'target',baseline/'target',symlinks=True)
priorplan['candidate_stage']=str(baseline)
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
write(previous/'plan.json',priorplan);shutil.copyfile(prior/'install-analysis.json',previous/'install-analysis.json')
plan['candidate_stage']=str(candidate);plan['previous_update_stage']=str(previous)
write(clone/'plan.json',plan);digest=sha(clone/'plan.json')
for name in ['deployment.tar','install-analysis.json']:shutil.copyfile(installed/name,clone/name)
manifest=json.loads((installed/'manifest.json').read_text());manifest['plan_sha256']=digest;write(clone/'manifest.json',manifest)
txpath=Path((area/'latest-update-checks').read_text().strip());tx=json.loads((txpath/'analysis.json').read_text());tx['plan_sha256']=digest
checks=fa/'checks';checks.mkdir();write(checks/'analysis.json',tx)
policy_path=Path((area/'latest-c25-checks').read_text().strip());policy=json.loads((policy_path/'analysis.json').read_text())
pc=fa/'policy';pc.mkdir();write(pc/'analysis.json',policy)
sources=set(plan['source_sha256'])|set(manifest['sources'])|set(tx['sources'])|set(policy['source_sha256'])
sources|={'port/scripts/run-phase4-launcher-once.py','port/scripts/phase4_launcher_trial.py','port/scripts/phase4_candidate.py'}
for name in sources:
 target=fixture/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(repo/name,target)
for name,path in [('latest-update',clone),('latest-update-checks',checks),('latest-c25-checks',pc)]: (fa/name).write_text(str(path)+'\n')
(clone/'backup.tar').write_text('public fixture originals only\n');write(clone/'backup-descriptor.json',{'path':str(clone/'backup.tar'),'sha256':sha(clone/'backup.tar')})
cases=[]
def positive():return calibrated_contract(fixture,fa,clone,plan)
assert positive()['foundation_hashes']==97;cases.append('C30_two_file_installed_contract_accepted')
def refuse(name,path,change):
 old=path.read_bytes();change(path)
 try:
  try:positive()
  except (AssertionError,OSError,ValueError):pass
  else:raise AssertionError('Unsafe contract accepted: '+name)
 finally:path.write_bytes(old)
 cases.append(name)
def field(path,key,value): data=json.loads(path.read_text());data[key]=value;write(path,data)
refuse('incorrect_foundation_count_refused',clone/'install-analysis.json',lambda p:field(p,'foundation_hash_count',96))
refuse('private_preservation_failure_refused',clone/'install-analysis.json',lambda p:field(p,'private_state_preserved',False))
refuse('third_file_claim_refused',clone/'install-analysis.json',lambda p:field(p,'public_files_written',3))
refuse('transaction_other_plan_refused',checks/'analysis.json',lambda p:field(p,'plan_sha256','0'*64))
refuse('changed_deployment_refused',clone/'deployment.tar',lambda p:p.write_bytes(b'changed'))
refuse('unplanned_candidate_change_refused',candidate/'target/etc/inittab',lambda p:p.write_text('changed'))
refuse('wrong_previous_experiment_refused',previous/'plan.json',lambda p:field(p,'experiment','other'))
refuse('source_drift_refused',fixture/'port/device/rk-r35s-p0/core-wireplumber.conf',lambda p:p.write_text('changed'))
binpath=stage/'bin';binpath.mkdir();calls=stage/'calls.jsonl';transport=binpath/'ssh'
transport.write_text('''#!/usr/bin/env python3
import json,os,sys
code=sys.stdin.read()
with open(os.environ['C31_CALLS'],'a') as f:f.write(json.dumps(code)+'\\n')
if 'cat /var/lib/muos-diagnostic/boot-seq\\n' in code:print(os.environ['C31_BEFORE'])
if '/sbin/reboot' in code:sys.exit(255)
''');transport.chmod(0o755)
env=os.environ.copy();env['PATH']=str(binpath)+':'+env['PATH'];env['C31_CALLS']=str(calls);env['C31_BEFORE']=str(boot_before)
def count():return len(calls.read_text().splitlines()) if calls.exists() else 0
def run(op,trial=None,ok=True):
 cmd=['python3','-B',str(fixture/'port/scripts/run-phase4-launcher-once.py'),op,'--host','192.0.2.1']
 if trial:cmd+=['--trial',str(trial)]
 r=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=40)
 assert (r.returncode==0)==ok,(op,r.stdout,r.stderr)
run('arm',ok=False);assert count()==0;cases.append('C30_arm_without_trial_refused_before_SSH')
run('new-trial');trial=Path((fa/'latest-c25-physical').read_text().strip());meta=json.loads((trial/'trial.json').read_text())
assert meta['experiment']==('C37_PRIMED_LAUNCHER_BOOT' if prime else ('C34_RW_LAUNCHER_BOOT' if rw else 'C31_IRQ_LAUNCHER_BOOT')) and meta['expected_boot']==boot_before+1 and meta['expected_fallback']==boot_before+2
cases.append('C31_correct_boot_and_fallback_bound')
survey=(trial/'c25-repeat-survey.sh').read_text()
# Real completed-generation branch, with only the session adapter mocked.
start=survey.index('if [ -e /run/muos/session/current ]');end=survey.index('\n[ ! -e "$c25_store/c25.once" ]',start)
branch=survey[start:end];base=stage/'session';base.mkdir();pkg=stage/'package';pkg.mkdir()
(base/'current').touch();cycle=base/'run-0003';cycle.mkdir();(cycle/'done').touch();(cycle/'result').write_text('0\n')
script=branch.replace('/usr/libexec/muos-session',str(pkg)).replace('/run/muos/session',str(base))
def generation(ok,live=False,result='0',done=True):
 (cycle/'result').write_text(result+'\n')
 if done:(cycle/'done').touch()
 elif (cycle/'done').exists():(cycle/'done').unlink()
 (pkg/'control-functions.sh').write_text('session_current() { cycle='+str(cycle)+'; }\nsession_identity() { '+('true' if live else 'false')+'; }\n')
 r=subprocess.run(['sh','-c','set -eu\n'+script],text=True,capture_output=True)
 assert (r.returncode==0)==ok,r.stderr
generation(True);cases.append('completed_manual_generation_accepted')
generation(False,live=True);cases.append('live_manual_generation_refused')
generation(False,result='1');cases.append('failed_manual_cleanup_refused')
generation(False,done=False);cases.append('incomplete_manual_cleanup_refused')
run('arm',trial);n=count();run('arm',trial,ok=False);assert count()==n;cases.append('duplicate_arm_no_dispatch')
arm=(trial/'c25-arm.sh').read_text();assert f'ONCE {boot_before+1}' in arm and f'c25.used.BOOT{boot_before+1:04d}' in arm
cases.append('C25_token_only_for_exact_next_boot')
run('request',trial);n=count();run('request',trial,ok=False);assert count()==n;cases.append('duplicate_reboot_no_dispatch')
changed=json.loads((trial/'trial.json').read_text());changed['calibrated_contract']['IRQ_scheduling']=False;write(trial/'trial.json',changed)
run('running',trial,ok=False);assert count()==n;write(trial/'trial.json',meta)
cases.append('changed_IRQ_trial_binding_refused')
run('fallback-request',trial,ok=False);assert count()==n;cases.append('fallback_before_clean_collection_refused')
sources=[Path(__file__),repo/'port/scripts/phase4_launcher_trial.py',repo/'port/scripts/run-phase4-launcher-once.py']
(stage/'analysis.json').write_text(json.dumps({'passed':True,'cases':cases,'hardware_accessed':False,'SSH_transport_mocked':True,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}},indent=2)+'\n')
(area/'latest-irq-launcher-checks').write_text(str(stage)+'\n');print('C31 installation/trial checks passed:',len(cases),stage)
