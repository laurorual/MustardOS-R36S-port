# SPDX-License-Identifier: MIT
"""C99: reuse the frozen C77 caller on the independently qualified C79 boot.

Boot binding, evidence namespace, guards and a private /etc RAM view change.
The dispatcher, host, core, state export and lease stay frozen.
"""
from pathlib import Path
import ast,importlib,json
import phase4_installed_core_session as legacy
from phase4_root_migration import require
from phase4_candidate import sha

REPO,WORK,NATIVE,NAMES=legacy.REPO,legacy.WORK,legacy.NATIVE,legacy.NAMES
AREA=WORK/'c79-session'
SESSION_NATIVE=REPO/'port/device/rk-r35s-p0/c79-session'
proof,watch_script,render_online=legacy.proof,legacy.watch_script,legacy.render_online


def valid_boot(report,public):
    require(report['passed'] is True and public['passed'] is True and
        type(report['schema']) is int and report['schema']==public['schema']==97,
        'Native C97 qualification required')
    require(type(report['boot_sequence']) is int and report['boot_sequence']==public['boot_sequence'] and
        report['boot_sequence']>=2,'Qualified first C79 boot counter')
    for key in ['physical_boot_after_initial_migration_qualified','seedless_no_credit_2048bits_path_verified',
        'rng_ready_before_new_creditable_seed_and_stop_verified','candidate_and_known_old_seed_hashes_absent',
        'root0755_readonly_p3_unmounted_PCM_closed_no_UI_or_once']:
        require(report[key] is public[key] is True,'Incomplete qualified first boot')
    require(report['device_written_rebooted_or_tests_rearmed_by_collector'] is False and
        public['device_written_rebooted_or_tests_rearmed_by_collector'] is False,'Read-only qualification required')
    require(report['guard_match']==public['guard_match']=={'guard_file_count':141,'C79_public_file_count':140,
        'stable_identity_guard_file_count':1} and report['stable_identity_files_verified']==4,
        'Complete C79 guard and identity inventory')


def qualified():
    boot=importlib.import_module('collect-phase4-initial-boot')
    frozen=proof('initial-boot-native')
    stage=boot.prep.initial.latest(boot.AREA,'latest-complete')
    report=json.loads((stage/'analysis.json').read_text())
    valid_boot(report,json.loads((frozen/'analysis.json').read_text()))
    checks=boot.prep.initial.latest(boot.AREA,'latest-checks')
    tested=json.loads((checks/'analysis.json').read_text())
    require(tested['passed'] is True and sha(checks/'analysis.json')==report['checks_sha256'] and
        tested['source_sha256']==report['source_sha256'],'Qualified C97 source binding')
    for n,h in report['source_sha256'].items():require(sha(REPO/n)==h,'C97 source changed')
    initial,ack,expected,stable,old,common,matching=boot.lineage()
    binding=json.loads((stage/'binding.json').read_text())
    require(expected==report['boot_sequence'] and report['initial_host_copy_sha256']==sha(initial/'host-copy.json') and
        binding['initial_host_copy_sha256']==report['initial_host_copy_sha256'] and
        binding['next_attempt_id']==ack['next_attempt_id'] and binding['next_attempt_sha256']==ack['next_attempt_sha256'],
        'Independent native migration and boot binding')
    observed=boot.entropy.decoded((stage/'stdout').read_text(),expected)
    require(observed['boot_id']==report['kernel_boot_id'] and (stage/'exit').read_text()=='0\n' and
        (stage/'checks.sh').read_text()==boot.entropy.render(common,expected,stable,old),'Authentic first boot receipts')
    return stage,report


def historical():
    qualified()
    # This executes only the already-qualified offline setup from C63-C77.
    frozen=proof('installed-core-session')
    for n,h in json.loads((frozen/'load/analysis.json').read_text())['source_sha256'].items():
        require(sha(REPO/n)==h,'Frozen C77 source changed')
    context,*rest=legacy.historical()
    # Historical asset bindings above refer to the original approved worker.
    # Only after those checks, use the explicitly reviewed RAM-view delta.
    context['worker']=SESSION_NATIVE/'worker.sh'
    context['files']['etc-view.sh']=SESSION_NATIVE/'etc-view.sh'
    context['expected']['etc-view.sh']=sha(SESSION_NATIVE/'etc-view.sh')
    return context,*rest


def current_common(common,old_boot,new_boot):
    _,report=qualified()
    require(type(new_boot) is int and new_boot==report['boot_sequence'],
        'Use the qualified C79 boot; observe a later boot separately')
    code=legacy.current_common(common,old_boot,new_boot)
    boot=importlib.import_module('collect-phase4-initial-boot')
    composition=boot.prep.initial.latest(WORK/'initial-migration','latest-complete')
    code,_=boot.matched_common(code,json.loads((composition/'tree.json').read_text()))
    return code+'[ "$(cat /proc/sys/kernel/random/boot_id)" = '+report['kernel_boot_id']+' ]\n'


def bind(prior,provider,observation,boot,boot_id):
    stage,report=qualified()
    require(type(boot) is int and boot==report['boot_sequence'] and boot_id==report['kernel_boot_id'],
        'C99 requires the exact qualified C79 boot identity')
    require(observation['C97_analysis_sha256']==sha(stage/'analysis.json') and
        observation['C97_proof_sha256']==sha(proof('initial-boot-native')/'SHA256SUMS'),
        'C99 observation must bind C97 evidence')
    return legacy.bind(prior,provider,observation,boot,boot_id)


def rendered_runner():
    source=REPO/'port/scripts/run-phase4-installed-core-session.py'
    require(source.read_bytes()==(proof('installed-core-session')/'source'/source.relative_to(REPO)).read_bytes(),
        'Use the frozen C77 runner')
    text=source.read_text()
    changes={
        'from phase4_installed_core_session import ':'from phase4_c79_session import ',
        'p = argparse.ArgumentParser(description=__doc__)':
            'from phase4_c79_session import qualified\nqualification_stage, _ = qualified()\np = argparse.ArgumentParser(description=__doc__)',
        '*NATIVE.glob(\'*.sh\')]':
            '*NATIVE.glob(\'*.sh\'), REPO / \'port/scripts/phase4_c79_session.py\', REPO / \'port/device/rk-r35s-p0/c79-session/worker.sh\', REPO / \'port/device/rk-r35s-p0/c79-session/etc-view.sh\']',
        "'root_RO_installed_payload_and_foundation_verified': True, 'agent_requested_reboot': False,":
            "'root_RO_installed_payload_and_foundation_verified': True, 'agent_requested_reboot': False,\n                   'C97_analysis_sha256': sha(qualification_stage / 'analysis.json'),\n                   'C97_proof_sha256': sha(REPO / 'dist/phase4/initial-boot-native/SHA256SUMS'),",
        "'observation_stage': str(observation_path), 'observation_sha256': sha(observation_path / 'observation.json'),":
            "'observation_stage': str(observation_path), 'observation_sha256': sha(observation_path / 'observation.json'),\n          'C97_analysis_sha256': observation['C97_analysis_sha256'], 'C97_proof_sha256': observation['C97_proof_sha256'],\n          'C99_C79_runtime_validation': True,",
        'C77 observed boot':'C99 observed C79 boot',
        'C77 session collected:':'C99 C79 session collected:',
    }
    for old,new in changes.items():
        require(text.count(old)==1,'Finite C99 runner adaptation anchor')
        text=text.replace(old,new)
    ast.parse(text);return text
