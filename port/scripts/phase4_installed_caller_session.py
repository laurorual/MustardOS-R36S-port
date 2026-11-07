# SPDX-License-Identifier: MIT
"""C106 exercise C105's installed entrypoint, retaining the C77 lifecycle."""
from pathlib import Path
import ast,json,re
import phase4_manual_caller as caller
from phase4_root_migration import require
from phase4_candidate import sha

REPO,WORK,NATIVE,NAMES=caller.REPO,caller.WORK,caller.parent.NATIVE,caller.parent.NAMES
AREA=WORK/'installed-caller-session'
legacy=caller.parent.legacy
proof=legacy.proof

def qualified():
    root=proof('manual-caller-installed')
    stage=Path((caller.AREA/'latest-complete').read_text().strip())
    require(stage.resolve().is_relative_to(caller.AREA),'Known completed C105')
    r=json.loads((stage/'analysis.json').read_text());public=json.loads((root/'analysis.json').read_text())
    require(r['schema']==105 and r['passed'] is True and all(public[k]==v for k,v in r.items()),'Frozen native C105')
    for key in ['root_read_only','RAM_removed','native_package_and_142_public_dependencies_checked',
                'native_stage_and_repeat_incomplete_run_refusal_passed','private_state_fingerprint_matched',
                'infrastructure_and_global_mounts_preserved']:require(r[key] is True,'Complete C105 closure')
    require(r['files_added']==17 and r['directories_added']==1 and r['existing_files_replaced']==0 and
        r['full_graphical_installed_caller_qualified'] is False,'Exact C105 installation scope')
    require(r['plan_sha256']==sha(stage/'plan.json'),'C105 plan binding')
    for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'Frozen C105 source changed')
    plan=json.loads((stage/'plan.json').read_text());meta=json.loads((stage/'manifest.json').read_text())
    observation=Path(plan['observation_stage']);o=json.loads((observation/'observation.json').read_text())
    require(observation.resolve().is_relative_to(caller.AREA) and
        sha(observation/'observation.json')==plan['observation_sha256'] and
        o['boot_sequence']==r['boot_sequence'] and o['kernel_boot_id']==meta['kernel_boot_id'],
        'Recorded successful C105 boot')
    require((stage/'caller-check.stdout').read_text()=='C105_CALLER_CHECK_OK_NO_UI\n' and
        (stage/'native-stage.stdout').read_text()=='C105_CALLER_STAGE_OK_RAM_ONLY\nC105_NATIVE_STAGE_AND_INCOMPLETE_RUN_REFUSAL_OK\n' and
        (stage/'cleanup.stdout').read_text()=='C105_RAM_REMOVED_ROOT_RO\n','Authentic C105 native receipts')
    for label in ['result','after','mounts-private','caller-check','native-stage','cleanup-stage','cleanup','post-cleanup-health']:
        require((stage/(label+'.exit')).read_text()=='0\n','C105 receipt failed')
    return stage,r,meta,plan

def historical():
    qualified();result=legacy.historical();ctx=result[0]
    require(ctx['worker']==REPO/'port/device/rk-r35s-p0/app-selection/worker.sh','Original worker required')
    return result

def current_common(common,old_boot,new_boot):
    _,r,meta,plan=qualified()
    require(type(new_boot) is int and new_boot==r['boot_sequence'],'C106 requires the observed C105 boot')
    code=caller.observed_common(new_boot,meta['kernel_boot_id'])
    for n,h in plan['files'].items():
        code+=f'''[ -f /{caller.PREFIX}/{n} ];[ ! -L /{caller.PREFIX}/{n} ]
[ "$(stat -c '%u:%g:%a:%h' /{caller.PREFIX}/{n})" = 0:0:644:1 ]
printf '%s  %s\\n' {h} /{caller.PREFIX}/{n} | sha256sum -c - >/dev/null
'''
    code+=f'''[ ! -L /{caller.PREFIX} ];[ "$(stat -c '%u:%g:%a' /{caller.PREFIX})" = 0:0:755 ]
[ "$(find /{caller.PREFIX} -mindepth 1 -maxdepth 1 -print | wc -l)" = 17 ]
'''
    return code

def bind(prior,provider,observation,boot,boot_id):
    stage,r,meta,_=qualified()
    require(type(boot) is int and boot==r['boot_sequence'] and boot_id==meta['kernel_boot_id'],
        'Exact observed C105 boot, never rewrite another context')
    require(observation['C105_analysis_sha256']==sha(stage/'analysis.json') and
        observation['C105_proof_sha256']==sha(proof('manual-caller-installed')/'SHA256SUMS'),
        'New observation must bind C105 installation')
    return legacy.bind(prior,provider,observation,boot,boot_id)

def watch_script(directory):
    code=legacy.watch_script(directory)
    require(code.count('seq 1 245')==1 and code.count('for attempt in')==1,'Known bounded watcher')
    code=code.replace('seq 1 245','seq 1 310').replace('first=;game=;returned=','first=;game=;returned=;worker_seen=')
    anchor='[ -d '+directory+' ] || exit 0\n'
    require(code.count(anchor)==1,'Watcher lifecycle anchor')
    check=f'''if [ -z "$worker_seen" ] && [ -f {directory}/state/manager ];then
 read manager manager_start < {directory}/state/manager
 if [ -r /proc/$manager/cmdline ] && [ "$(awk '{{print $22}}' /proc/$manager/stat)" = "$manager_start" ];then
  actual=$(tr '\\000' '\\n' < /proc/$manager/cmdline)
  expected=$(printf '%s\\n' /bin/sh /usr/libexec/muos-caller/worker.sh {directory} observe)
  if [ "$actual" = "$expected" ];then worker_seen=1;echo C106_INSTALLED_WORKER_CMDLINE_CONFIRMED;fi
 fi
fi
'''
    # Only read the manager's bounded command line; no environment/key data.
    return code.replace(anchor,anchor+check)

def render_online(online):
    text=legacy.render_online(online)
    def change(old,new):
        nonlocal text
        require(text.count(old)==1,'Finite C106 online anchor: '+old[:70]);text=text.replace(old,new)
    change('for n,f in files.items():\n r=subprocess.run',
           'for n,f in files.items():\n if n in caller_scripts:continue\n r=subprocess.run')
    line=[s for s in text.splitlines() if s.startswith('code=common+f"printf') and 'C47_WORKER' in s]
    require(len(line)==1,'Original RAM worker preparation anchor')
    change(line[0],'''code=common+f"sh /usr/libexec/muos-caller/caller.sh stage {directory}\\nprintf '%s\\\\n' {sha(files['app-launch.sh'])} > {directory}/launcher.sha256\\nmkdir -m 700 {directory}/state {directory}/owner {directory}/watchdog\\n"''')
    change("remote('prepare',code)","remote('prepare',code,timeout=120)")
    change("entry=f'/bin/sh {directory}/worker.sh {directory} {native_mode}'",
           "entry=f'/bin/sh /usr/libexec/muos-caller/caller.sh run {directory} {native_mode}'")
    change('{directory}/runner 240 {directory}/watchdog /usr/libexec/muos-session/mount-namespace {entry}', '{entry}')
    change('timeout=255,required=False','timeout=300,required=False')
    anchor="remote('mount-health',common+f'cmp /proc/1/mountinfo {directory}/global-before.txt\\necho C47_GLOBAL_MOUNTS_IDENTICAL\\n')"
    change(anchor,anchor+'''\nremote('caller-execution',common+f'[ -d {directory}/caller-stage/run.once ];[ ! -L {directory}/caller-stage/run.once ]\\n[ "$(stat -c %u:%g:%a {directory}/caller-stage/run.once)" = 0:0:700 ]\\ncmp /usr/libexec/muos-caller/worker.sh {directory}/worker.sh\\necho C106_INSTALLED_CALLER_RUN_ONCE_CONFIRMED\\n')''')
    ast.parse(text);return text

def rendered_runner():
    source=REPO/'port/scripts/run-phase4-installed-core-session.py'
    require(source.read_bytes()==(proof('installed-core-session')/'source'/source.relative_to(REPO)).read_bytes(),
        'Frozen C77 runner')
    text=source.read_text()
    changes={
        'from phase4_installed_core_session import ':'from phase4_installed_caller_session import ',
        'p = argparse.ArgumentParser(description=__doc__)':
            'from phase4_installed_caller_session import qualified, caller, proof\nqualification_stage, _, _, _ = qualified()\np = argparse.ArgumentParser(description=__doc__)',
        '*NATIVE.glob(\'*.sh\')]':
            '*NATIVE.glob(\'*.sh\'), REPO / \'port/scripts/phase4_installed_caller_session.py\']',
        "'root_RO_installed_payload_and_foundation_verified': True, 'agent_requested_reboot': False,":
            "'root_RO_installed_payload_and_foundation_verified': True, 'agent_requested_reboot': False,\n                   'C105_analysis_sha256': sha(qualification_stage / 'analysis.json'),\n                   'C105_proof_sha256': sha(proof('manual-caller-installed') / 'SHA256SUMS'),",
        "observation=observation, NAMES=NAMES, watch_script=watch_script)":
            "observation=observation, NAMES=NAMES, watch_script=watch_script, caller_scripts=caller.SCRIPTS)",
        "passed = context['passed'] and all(maps.count(n) == 1 for n in required_maps)":
            "passed = context['passed'] and all(maps.count(n) == 1 for n in required_maps)\npassed = passed and maps.count('C106_INSTALLED_WORKER_CMDLINE_CONFIRMED') == 1\npassed = passed and (stage/'caller-execution.stdout').read_text() == 'C106_INSTALLED_CALLER_RUN_ONCE_CONFIRMED\\n'",
        "'observation_stage': str(observation_path), 'observation_sha256': sha(observation_path / 'observation.json'),":
            "'observation_stage': str(observation_path), 'observation_sha256': sha(observation_path / 'observation.json'),\n          'schema':106, 'C106_installed_caller_runtime_validation':True, 'installed_entrypoint_used':True,\n          'caller_scripts_transferred_by_host':False, 'installed_worker_cmdline_confirmed':True,\n          'C105_analysis_sha256':sha(qualification_stage/'analysis.json'),\n          'C105_proof_sha256':sha(proof('manual-caller-installed')/'SHA256SUMS'),",
        'C77 observed boot':'C106 installed caller observed boot',
        'C77 session collected:':'C106 installed caller session collected:',
    }
    for old,new in changes.items():
        require(text.count(old)==1,'Finite C106 runner anchor');text=text.replace(old,new)
    ast.parse(text);return text
