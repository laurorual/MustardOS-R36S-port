#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check calibrated boot provenance and dispatch receipts without hardware."""
from pathlib import Path
import copy, json, os, shutil, subprocess, tempfile
from phase4_candidate import sha
from phase4_launcher_trial import calibrated_contract

repo = Path(__file__).resolve().parents[2]
area = repo / 'build/phase4/rootfs-candidate'
installed = Path((area / 'latest-update').read_text().strip())
plan = json.loads((installed / 'plan.json').read_text())
bound = calibrated_contract(repo, area, installed, plan)
stage = Path(tempfile.mkdtemp(prefix='launcher-trial-checks.', dir=area))
fixture = stage / 'fixture'; target_area = fixture / 'build/phase4/rootfs-candidate'
target_area.mkdir(parents=True)
installation = target_area / 'installed'; installation.mkdir()
native = target_area / 'candidate/target'; factory = target_area / 'composition/target'
for name in bound['native_file_sha256']:
    rel = name.lstrip('/')
    for root in [native, factory]:
        dest = root / rel; dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(plan['candidate_stage']) / 'target' / rel, dest)
comp = factory.parent
shutil.copyfile(native / 'usr/libexec/muos-session/prerequisites.sha256', comp / 'foundation.sha256')
checks = target_area / 'checks'; checks.mkdir()
policy = target_area / 'policy'; policy.mkdir()
original_checks = Path((area / 'latest-update-checks').read_text().strip())
original_policy = Path((area / 'latest-c25-checks').read_text().strip())
tx = json.loads((original_checks / 'analysis.json').read_text())
pc = json.loads((original_policy / 'analysis.json').read_text())
image = json.loads((Path(bound['composition_stage']) / 'analysis.json').read_text())
eq = json.loads((Path(bound['composition_stage']) / 'native-C26-equivalence.json').read_text())
manifest = json.loads((installed / 'manifest.json').read_text())
sources = set(plan['source_sha256']) | set(manifest['sources']) | set(tx['sources']) | set(image['sources']) | set(pc['source_sha256'])
sources |= {'port/scripts/run-phase4-launcher-once.py', 'port/scripts/phase4_launcher_trial.py', 'port/scripts/phase4_candidate.py'}
for name in sources:
    dest = fixture / name; dest.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(repo / name, dest)
def write(path, value): path.write_text(json.dumps(value, indent=2) + '\n')
plan['candidate_stage'] = str(native.parent)
write(installation / 'plan.json', plan); digest = sha(installation / 'plan.json')
for name in ['deployment.tar', 'install-analysis.json']: shutil.copyfile(installed / name, installation / name)
manifest['plan_sha256'] = digest; write(installation / 'manifest.json', manifest)
tx['plan_sha256'] = digest; write(checks / 'analysis.json', tx)
image['selected_native_profile_plan_sha256'] = digest; write(comp / 'analysis.json', image)
eq['native_plan_sha256'] = digest; write(comp / 'native-C26-equivalence.json', eq)
write(policy / 'analysis.json', pc)
for name, path in [('latest-update', installation), ('latest-update-checks', checks),
                   ('latest-composition', comp), ('latest-c25-checks', policy)]:
    (target_area / name).write_text(str(path) + '\n')
(installation / 'backup.tar').write_bytes(b'public fixture originals')
write(installation / 'backup-descriptor.json', {'path': str(installation / 'backup.tar'), 'sha256': sha(installation / 'backup.tar')})
cases = []
def check(name, mutate=None):
    if mutate:
        path, change = mutate; original = path.read_bytes(); change(path)
        try:
            try: calibrated_contract(fixture, target_area, installation, plan)
            except (AssertionError, FileNotFoundError): pass
            else: raise AssertionError('Unsafe contract accepted: ' + name)
        finally: path.write_bytes(original)
    else: calibrated_contract(fixture, target_area, installation, plan)
    cases.append(name)
def field(path, key, value):
    data = json.loads(path.read_text()); data[key] = value; write(path, data)
check('installed_C27_and_factory_binding')
check('private_preservation_failure_refused', (installation / 'install-analysis.json', lambda p: field(p, 'private_state_preserved', False)))
check('transaction_other_plan_refused', (checks / 'analysis.json', lambda p: field(p, 'plan_sha256', '0'*64)))
check('composition_other_plan_refused', (comp / 'analysis.json', lambda p: field(p, 'selected_native_profile_plan_sha256', '0'*64)))
check('equivalence_other_plan_refused', (comp / 'native-C26-equivalence.json', lambda p: field(p, 'native_plan_sha256', '0'*64)))
check('equivalence_false_refused', (comp / 'native-C26-equivalence.json', lambda p: field(p, 'calibration_certificate_identical', False)))
check('deployment_changed_refused', (installation / 'deployment.tar', lambda p: p.write_bytes(b'changed')))
check('stale_native_core_refused', (native / 'etc/init.d/S95muos-core', lambda p: p.write_text('old core')))
check('stale_native_inittab_refused', (native / 'etc/inittab', lambda p: p.write_text('old boot')))
check('certificate_divergence_refused', (native / 'usr/share/muos-r35s-profile/speaker-calibration.json', lambda p: field(p, 'maximum_clean_and_adequate_user_confirmed', False)))
check('source_drift_refused', (fixture / 'port/device/rk-r35s-p0/S95muos-core', lambda p: p.write_text('changed source')))

# Actual CLI, with the SSH transport replaced by an executable that records
# every dispatch. The test cannot invoke the system SSH or touch hardware.
fakebin = stage / 'bin'; fakebin.mkdir()
transport = fakebin / 'ssh'; calls = stage / 'ssh-calls.jsonl'
transport.write_text('''#!/usr/bin/env python3
import json, os, sys
code=sys.stdin.read()
with open(os.environ['TRIAL_CALLS'],'a') as f: f.write(json.dumps({'argv':sys.argv[1:],'code':code})+'\\n')
if 'cat /var/lib/muos-diagnostic/boot-seq\\n' in code: print('53')
if '/sbin/reboot' in code: sys.exit(255)
'''); transport.chmod(0o755)
env = os.environ.copy(); env['PATH'] = str(fakebin) + ':' + env['PATH']; env['TRIAL_CALLS'] = str(calls)
runner = fixture / 'port/scripts/run-phase4-launcher-once.py'
def run(operation, trial=None, ok=True):
    command = ['python3', '-B', str(runner), operation, '--host', '192.0.2.1']
    if trial: command += ['--trial', str(trial)]
    result = subprocess.run(command, capture_output=True, text=True, env=env, timeout=10)
    assert (result.returncode == 0) == ok, (operation, result.stdout, result.stderr)
    return result
def count(): return len(calls.read_text().splitlines()) if calls.exists() else 0
run('arm', ok=False); assert count() == 0; cases.append('integrated_arm_without_trial_refused_before_SSH')
run('new-trial')
trial = Path((target_area / 'latest-c25-physical').read_text().strip())
assert json.loads((trial / 'trial.json').read_text())['before_boot'] == 53
cases.append('normal_C07_trial_bound_without_old_fallback_receipt')
survey = json.loads(calls.read_text().splitlines()[-1])['code']
assert '/sbin/reboot' not in survey and 'mount -o remount,rw' not in survey
cases.append('new_trial_read_only_survey')
run('arm', trial); n = count(); run('arm', trial, ok=False); assert count() == n
cases.append('arm_intent_blocks_duplicate_dispatch')
code = (trial / 'c25-arm.sh').read_text()
assert 'ONCE 54' in code and 'c25.used.BOOT0054' in code and 'c12.once' not in code
assert 'mount -o remount,ro /' in code and 'flock -n 8' in code
cases.append('arm_exact_next_boot_C25_only_root_restore_and_lock')
# Exercise the real pre-arm C07-state branch in a disposable directory. A
# normal C07 has selection/fallback but no done/result; fallback requires both.
start = code.index('if [ -e /run/muos/c25 ]')
end = code.index('if [ ! -e /run/muos/session ]', start)
branch = code[start:end]
state = stage / 'c25-state'; state.mkdir(mode=0o700)
branch = branch.replace('/run/muos/c25', str(state))
for name, value in [('selected', 'c07\n'), ('select.result', '0\n'), ('fallback', '0\n')]:
    (state / name).write_text(value)
# Override only stat's uid/gid in this rootless fixture; retain the real mode.
script = 'set -eu\nstat() { echo 0:0:700; }\n' + branch
def state_run(ok):
    result = subprocess.run(['sh', '-c', script], capture_output=True, text=True)
    assert (result.returncode == 0) == ok, result.stderr
state_run(True); cases.append('normal_C07_no_done_arm_guard_accepts')
(state / 'fallback').write_text('1\n'); state_run(False)
cases.append('fallback_without_done_arm_guard_refuses')
(state / 'done').touch(); (state / 'result').write_text('0\n'); state_run(True)
cases.append('clean_fallback_arm_guard_accepts')
(state / 'result').write_text('1\n'); state_run(False)
cases.append('failed_fallback_arm_guard_refuses')
run('request', trial); n = count(); run('request', trial, ok=False); assert count() == n
cases.append('reboot_intent_blocks_duplicate_dispatch')
meta = json.loads((trial / 'trial.json').read_text()); original = copy.deepcopy(meta)
meta['calibrated_contract']['quantum'] = 256; write(trial / 'trial.json', meta)
run('running', trial, ok=False); assert count() == n; write(trial / 'trial.json', original)
cases.append('changed_trial_binding_refused_before_SSH')
run('fallback-request', trial, ok=False); assert count() == n
cases.append('fallback_refused_before_clean_collection')
report = {'passed': True, 'cases': cases, 'hardware_accessed': False,
          'transport_mocked': True, 'native_code_changed': False,
          'source_sha256': {name: sha(repo / name) for name in [
              'port/scripts/phase4_launcher_trial.py', 'port/scripts/run-phase4-launcher-once.py',
              'port/scripts/check-phase4-launcher-trial.py']}}
write(stage / 'analysis.json', report)
(area / 'latest-launcher-trial-checks').write_text(str(stage) + '\n')
print('Calibrated launcher trial checks passed:', len(cases), stage)
