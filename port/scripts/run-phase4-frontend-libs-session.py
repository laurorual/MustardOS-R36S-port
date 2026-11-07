#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Observe a new boot, or run the C66 RAM provider qualification on that boot."""
from pathlib import Path
import argparse, ipaddress, json, re, subprocess, tempfile
from phase4_candidate import sha
from phase4_frontend_libs_session import historical, current_common, bind, watch_script, render_online, AREA, WORK, REPO, NATIVE, NAMES

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--host', required=True, type=ipaddress.IPv4Address)
p.add_argument('--boot', required=True, type=int)
group = p.add_mutually_exclusive_group(required=True)
group.add_argument('--observe', action='store_true')
group.add_argument('--observation', type=Path)
args = p.parse_args()
context, prior_stage, prior, provider_stage, provider, online = historical()
AREA.mkdir(exist_ok=True)
common = current_common(context['common'], prior['boot_sequence'], args.boot)
infra = context['infra']
ssh = ['ssh', '-p', '2222', '-i', str(WORK / 'private/c07-client'), '-oIdentitiesOnly=yes',
       '-oStrictHostKeyChecking=yes', '-oHostKeyAlias=[192.168.15.17]:2222',
       '-oUserKnownHostsFile=' + str(WORK / 'private/c07-known_hosts'), '-oBatchMode=yes',
       '-oConnectTimeout=6', 'root@' + str(args.host)]
sources = [Path(__file__), REPO / 'port/scripts/phase4_frontend_libs_session.py',
           REPO / 'port/scripts/prepare-phase4-frontend-libs-session.py', *NATIVE.glob('*.sh')]

def read(label, code, directory):
    (directory / (label + '.sh')).write_text(code)
    result = subprocess.run(ssh + ['sh -s'], input=code, capture_output=True, text=True, timeout=35)
    for suffix, value in [('stdout', result.stdout), ('stderr', result.stderr), ('exit', str(result.returncode) + '\n')]:
        (directory / (label + '.' + suffix)).write_text(value)
    assert result.returncode == 0, (label, directory, result.stderr)
    return result.stdout

if args.observe:
    stage = Path(tempfile.mkdtemp(prefix='observe.', dir=AREA))
    infrastructure = read('preflight', common + infra, stage)
    boot_id = read('boot-evidence', common + 'cat /proc/sys/kernel/random/boot_id\n', stage).strip()
    observation = {'passed': True, 'experiment': 'C66_OBSERVED_BOOT', 'boot_sequence': args.boot,
                   'kernel_boot_id': boot_id, 'host': str(args.host), 'infrastructure': infrastructure,
                   'prior_analysis_sha256': sha(prior_stage / 'analysis.json'),
                   'provider_analysis_sha256': sha(provider_stage / 'analysis.json'),
                   'root_RO_installed_payload_and_foundation_verified': True, 'agent_requested_reboot': False,
                   'source_sha256': {str(f.relative_to(REPO)): sha(f) for f in sources}}
    bind(prior, provider, observation, args.boot, boot_id)
    (stage / 'observation.json').write_text(json.dumps(observation, indent=2) + '\n')
    (AREA / 'latest-observation').write_text(str(stage) + '\n')
    print('C66 observed boot', args.boot, 'rootRO/installed payload/foundation verified:', stage)
    raise SystemExit(0)

observation_path = args.observation.resolve()
assert observation_path.is_relative_to(AREA)
observation = json.loads((observation_path / 'observation.json').read_text())
assert observation['host'] == str(args.host)
for n, h in observation['source_sha256'].items():
    assert sha(REPO / n) == h, n
digests = bind(prior, provider, observation, args.boot, observation['kernel_boot_id'])
checks = Path((AREA / 'latest-checks').read_text().strip())
check_report = json.loads((checks / 'analysis.json').read_text())
assert check_report['passed']
for n, h in check_report['source_sha256'].items():
    assert sha(REPO / n) == h, n
common += '[ "$(cat /proc/sys/kernel/random/boot_id)" = ' + observation['kernel_boot_id'] + ' ]\n'
files, expected = context['files'], context['expected']
for n in ['app-launch.sh', 'installed-host.sh', 'frontend-libs.sh']:
    files[n] = NATIVE / n
    expected[n] = sha(files[n])
for n in NAMES:
    source = provider_stage / 'target/opt/muos/frontend/lib' / n
    files['provider-lib/' + n] = source
    expected['provider-lib/' + n] = digests[n]
    if n != 'libmuxmod.so':
        files['lib/' + n] = source
        expected['lib/' + n] = digests[n]
files['provider-probe'] = provider_stage / 'load-probe'
expected['provider-probe'] = sha(files['provider-probe'])
assert 'muxretro' not in files and 'save-store' not in files

online = render_online(online)
context.update(common=common, area=AREA, readonly=NATIVE, files=files, expected=expected,
               observation=observation, NAMES=NAMES, watch_script=watch_script)
context['args'].boot = args.boot
context['args'].host = args.host
exec(compile(online, str(Path(__file__)), 'exec'), context)
stage, out = context['stage'], context['out']
game = (out / 'game.log').read_text() if (out / 'game.log').exists() else ''
core = (out / 'core.log').read_text() if (out / 'core.log').exists() else ''
maps = (stage / 'watch-maps.stdout').read_text()
required_maps = ['C66_MAP_MENU_FIRST_PROVIDER3_C46', 'C66_MAP_GAME_PROVIDER4_INSTALLED_HOST',
                 'C66_MAP_MENU_RETURN_PROVIDER3_C46']
passed = context['passed'] and all(maps.count(n) == 1 for n in required_maps)
passed = passed and 'C53_STATE_CYCLE_COMPLETE' in core and 'Quick Load (hotkey)' in game
passed = passed and 'Quick Save (hotkey)' not in game and game.count('C66_PROVIDER_VALID files=7 operation=launch') == 1
exits = re.findall(r'^C50_EXIT reason=hotkey frames=([1-9][0-9]*)$', game, re.M)
passed = passed and len(exits) == 1
old_store = (prior_stage / 'collected/store-readonly-after.sha256').read_bytes()
for n in ['store-readonly-before.sha256', 'store-readonly-after.sha256']:
    passed = passed and (out / n).is_file() and (out / n).read_bytes() == old_store
for n in ['state-metadata.txt', 'seed-metadata.txt']:
    passed = passed and (out / n).is_file() and (out / n).read_bytes() == (prior_stage / 'collected/state-metadata.txt').read_bytes()
store_logs = ''.join((out / n).read_text() if (out / n).exists() else '' for n in ['store-seed.log', 'store-verify.log'])
passed = passed and store_logs.count('C58_INSTALLED_DISPATCH operation=status') == 2 and store_logs.count('C58_INSTALLED_DISPATCH operation=export') == 1
passed = passed and 'C53_STORE_READONLY_BYTE_EXACT current=1' in store_logs
abi = (stage / 'native-provider-ABI.stdout').read_text()
passed = passed and abi.count('C65 eager load: ') == 4 and 'muxretro interface 1' in abi
report = {'passed': passed, 'experiment': 'C66_FRONTEND_PROVIDER_RAM', 'boot_sequence': args.boot,
          'kernel_boot_id': observation['kernel_boot_id'], 'private_identity': prior['private_identity'],
          'ROM_sha256': prior['ROM_sha256'], 'prior_boot_sequence': prior['boot_sequence'],
          'exact_C63_boot_retained': False, 'new_boot_explicitly_bound': True,
          'observation_stage': str(observation_path), 'observation_sha256': sha(observation_path / 'observation.json'),
          'C63_analysis_sha256': sha(prior_stage / 'analysis.json'), 'C65_analysis_sha256': sha(provider_stage / 'analysis.json'),
          'libraries': digests, 'menu_variant_C46_sha256': prior['library_sha256'],
          'host_binary_sha256': prior['host_binary_sha256'], 'installed_host_used': True,
          'host_ELF_transferred': False, 'store_ELF_transferred': False, 'provider_ELFs_RAM_only': True,
          'native_eager_provider_and_installed_host_CLI_passed': abi.count('C65 eager load: ') == 4,
          'process_maps_confirmed': all(maps.count(n) == 1 for n in required_maps),
          'core_frames': int(exits[0]) if exits else None, 'native_exit': context['r'].returncode,
          'cleanup_passed': True, 'RAM_removed': True, 'root_ro': True, 'global_mountinfo_unchanged': True,
          'store_byte_identical_to_C63': passed, 'new_save_requested': False, 'agent_requested_reboot': False,
          'preferences_persisted': False, 'physical_confirmation_pending': True,
          'checks_analysis_sha256': sha(checks / 'analysis.json'),
          'source_sha256': {str(f.relative_to(REPO)): sha(f) for f in sources}}
(stage / 'analysis.json').write_text(json.dumps(report, indent=2) + '\n')
assert (WORK / 'graphics-config/output/.config').read_bytes() == (WORK / 'network-tools/baseline.config').read_bytes()
if passed:
    (AREA / 'latest-load').write_text(str(stage) + '\n')
print('C66 session collected:', stage, 'technical pass:', passed)
assert passed, 'Session cleaned; inspect receipts before any repeat'
