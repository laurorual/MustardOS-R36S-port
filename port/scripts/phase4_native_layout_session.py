# SPDX-License-Identifier: MIT
"""C103: original C77 worker on the qualified, installed C102 layout.

No C99 /etc or /mnt views; only the existing per-file runtime isolation.
The installed host/provider/core, snapshot export, input and lease stay frozen.
"""
from pathlib import Path
import ast,importlib,json
import phase4_installed_core_session as legacy
from phase4_candidate import sha
from phase4_root_migration import require

REPO,WORK,NATIVE,NAMES=legacy.REPO,legacy.WORK,legacy.NATIVE,legacy.NAMES
AREA=WORK/'native-layout-session'
proof,watch_script,render_online=legacy.proof,legacy.watch_script,legacy.render_online

def valid_install(report,public):
    require(report['schema']==public['schema']==102 and type(report['schema']) is int,
        'Qualified C102 schema required')
    for key in ['passed','public_template_unchanged','root_read_only','private_state_fingerprint_matched',
        'infrastructure_and_global_mounts_preserved','RAM_capsule_removed']:
        require(report[key] is public[key] is True,'Incomplete C102 qualification')
    for key in ['p1_or_p3_mounted','seed_counter_or_user_data_updated','reboot_or_UI_started']:
        require(report[key] is public[key] is False,'C102 must preserve data and activation')
    for key,value in [('public_file_added_bytes',444),('empty_directory_added',1),
        ('existing_files_replaced',0),('foundation_files_reverified',141)]:
        require(type(report[key]) is int and report[key]==public[key]==value,'Exact C102 delta required')
    require(type(report['boot_sequence']) is int and report['boot_sequence']==public['boot_sequence'],
        'Exact C102 boot counter')

def qualified():
    installer=importlib.import_module('run-phase4-c79-layout-install')
    common,_,boot,parents,boot_sha=installer.inputs()
    stage=Path((installer.AREA/'latest-complete').read_text().strip())
    require(stage.resolve().is_relative_to(installer.AREA),'Known C102 completion stage')
    r=json.loads((stage/'analysis.json').read_text())
    public=json.loads((proof('c79-layout-installed')/'analysis.json').read_text())
    valid_install(r,public)
    require(all(public[k]==v for k,v in r.items()),'Native C102 report must match frozen proof')
    plan=json.loads((stage/'plan.json').read_text());manifest=json.loads((stage/'manifest.json').read_text())
    require(r['plan_sha256']==manifest['plan_sha256']==sha(stage/'plan.json') and
        r['parent_proofs_sha256']==plan['parent_proofs_sha256']==parents and
        plan['C97_analysis_sha256']==boot_sha and r['boot_sequence']==boot['boot_sequence'] and
        manifest['kernel_boot_id']==boot['kernel_boot_id'],'Installed layout and first C79 boot lineage')
    require(r['source_sha256']==plan['source_sha256'],'C102 source binding')
    for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'C102 source changed')
    require((stage/'collected-result.txt').read_text()=='0\nC102_INSTALLED_444_BYTES_ONE_DIRECTORY_ROOT_RO\n' and
        (stage/'cleanup.stdout').read_text()=='C102_RAM_REMOVED_ROOT_RO\n','Authentic C102 native completion')
    for label in ['inspect','dispatch','result','after','mounts-private','cleanup','post-cleanup-health']:
        require((stage/(label+'.exit')).read_text()=='0\n','Successful C102 native receipt')
    require((stage/'before.stdout').read_bytes()==(stage/'after.stdout').read_bytes()==
        (stage/'post-cleanup-health.stdout').read_bytes(),'C102 infrastructure preserved')
    return stage,r,common+installer.HEALTH,manifest

def historical():
    qualified()
    frozen=proof('installed-core-session')
    for n,h in json.loads((frozen/'load/analysis.json').read_text())['source_sha256'].items():
        require(sha(REPO/n)==h,'Frozen C77 source changed')
    result=legacy.historical();context=result[0]
    require(context['worker']==REPO/'port/device/rk-r35s-p0/app-selection/worker.sh' and
        'etc-view.sh' not in context['files'],'Use original worker without C99 directory views')
    return result

def current_common(common,old_boot,new_boot):
    _,report,guard,_=qualified()
    require(type(new_boot) is int and new_boot==report['boot_sequence'],
        'Use the qualified installed-layout boot; observe a later boot separately')
    return guard

def bind(prior,provider,observation,boot,boot_id):
    stage,report,_,manifest=qualified()
    require(type(boot) is int and boot==report['boot_sequence'] and boot_id==manifest['kernel_boot_id'],
        'C103 requires the exact C102 boot identity')
    require(observation['C102_analysis_sha256']==sha(stage/'analysis.json') and
        observation['C102_proof_sha256']==sha(proof('c79-layout-installed')/'SHA256SUMS'),
        'C103 observation must bind installed layout evidence')
    return legacy.bind(prior,provider,observation,boot,boot_id)

def rendered_runner():
    source=REPO/'port/scripts/run-phase4-installed-core-session.py'
    require(source.read_bytes()==(proof('installed-core-session')/'source'/source.relative_to(REPO)).read_bytes(),
        'Use frozen C77 runner')
    text=source.read_text()
    changes={
        'from phase4_installed_core_session import ':'from phase4_native_layout_session import ',
        'p = argparse.ArgumentParser(description=__doc__)':
            'from phase4_native_layout_session import qualified\nqualification_stage, _, _, _ = qualified()\np = argparse.ArgumentParser(description=__doc__)',
        '*NATIVE.glob(\'*.sh\')]':
            '*NATIVE.glob(\'*.sh\'), REPO / \'port/scripts/phase4_native_layout_session.py\']',
        "'root_RO_installed_payload_and_foundation_verified': True, 'agent_requested_reboot': False,":
            "'root_RO_installed_payload_and_foundation_verified': True, 'agent_requested_reboot': False,\n                   'C102_analysis_sha256': sha(qualification_stage / 'analysis.json'),\n                   'C102_proof_sha256': sha(REPO / 'dist/phase4/c79-layout-installed/SHA256SUMS'),",
        "'observation_stage': str(observation_path), 'observation_sha256': sha(observation_path / 'observation.json'),":
            "'observation_stage': str(observation_path), 'observation_sha256': sha(observation_path / 'observation.json'),\n          'C102_analysis_sha256': observation['C102_analysis_sha256'], 'C102_proof_sha256': observation['C102_proof_sha256'],\n          'C103_native_layout_runtime_validation': True,",
        'C77 observed boot':'C103 observed installed-layout boot',
        'C77 session collected:':'C103 native-layout session collected:',
    }
    for old,new in changes.items():
        require(text.count(old)==1,'Finite C103 runner adaptation anchor');text=text.replace(old,new)
    ast.parse(text);return text
