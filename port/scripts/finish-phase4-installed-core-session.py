#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C77 offline closure of authentic postflight/cleanup receipts after interruption."""
from pathlib import Path
import argparse, json, subprocess
from phase4_candidate import sha
from phase4_installed_core_session import historical, current_common, REPO, WORK, proof

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('stage', type=Path)
args = p.parse_args()
stage = args.stage.resolve()
r = json.loads((stage / 'analysis.json').read_text())
assert r['passed'] and r['RAM_removed'] and r['cleanup_passed']
assert r['installed_host_used'] and not r['host_ELF_transferred'] and not r['exact_C66_boot_retained'] and r['installed_core_used'] and not r['core_ELF_transferred']
context, prior_stage, prior, provider_stage, provider, _ = historical()
assert prior['private_identity'] == context['identity'] == r['private_identity']
assert prior['ROM_sha256'] == context['nr']['ROM_sha256'] == r['ROM_sha256']
assert prior['kernel_boot_id'] == context['source_session_report']['kernel_boot_id']
for key, digest in {**context['assets'], 'host_binary_sha256': context['host_digest']}.items():
    assert prior[key] == digest, key
for old in [context['qualified_stage'], context['installed_stage'], context['prior_stage']]:
    assert (prior_stage / 'collected/store-readonly-after.sha256').read_bytes() == (old / 'collected/store-readonly-after.sha256').read_bytes()
observation_path = Path(r['observation_stage'])
observation = json.loads((observation_path / 'observation.json').read_text())
assert sha(observation_path / 'observation.json') == r['observation_sha256']
common = current_common(context['common'], prior['boot_sequence'], r['boot_sequence'])
common += '[ "$(cat /proc/sys/kernel/random/boot_id)" = ' + r['kernel_boot_id'] + ' ]\n'
assert common + context['infra'] == (stage / 'preflight.sh').read_text()
# The session's exact boot may have ended during interruption. Close only
# the authentic already-recorded receipts; never synthesize a new SSH success.
for label in ['native', 'postflight', 'mount-health', 'cleanup', 'stopped-screen']:
    assert (stage / (label + '.exit')).read_text() == '0\n', label
assert (stage / 'postflight.stdout').read_bytes() == (stage / 'preflight.stdout').read_bytes()
assert (stage / 'mount-health.stdout').read_text() == 'C47_GLOBAL_MOUNTS_IDENTICAL\n'
assert (stage / 'cleanup.stdout').read_text() == 'C47_RAM_REMOVED_ROOT_RO_FOUNDATION97_NETWORK_OK\n'
assert (stage / 'stopped-screen.stdout').read_text() == 'C77_STOPPED_SCREEN_WRITTEN_NO_UI_ROOT_RO\n'
evidence = {label + '.' + ext: sha(stage / (label + '.' + ext))
            for label in ['postflight', 'mount-health', 'cleanup', 'stopped-screen']
            for ext in ['sh', 'stdout', 'stderr', 'exit']}
assert sha(WORK / 'muxretro-image/image.n_uthilw/images/rootfs.ext4') == provider['C64_image_preserved_sha256']
assert (WORK / 'graphics-config/output/.config').read_bytes() == (WORK / 'network-tools/baseline.config').read_bytes()
parents = {n: sha(proof(n) / 'SHA256SUMS') for n in
           ['installed-host-session', 'muxretro-installed', 'frontend-libs', 'muxretro-image', 'frontend-libs-session', 'muxretro-provider', 'provider-upgrade-native']}
report = {'passed': True, 'experiment': 'C77_FINAL_READONLY_HEALTH',
          'C63_identity_assets_and_boot_history_matched': True,
          'C54_C58_C61_C63_store_inventories_matched': True,
          'C64_image_preserved_sha256': provider['C64_image_preserved_sha256'],
          'SDK_config_unchanged': True, 'parent_proofs_sha256': parents,
          'closure_uses_recorded_session_receipts': True, 'recorded_health_boot': r['boot_sequence'],
          'new_SSH_or_current_boot_health_claimed': False, 'recorded_receipts_sha256': evidence,
          'source_sha256': {str(Path(__file__).resolve().relative_to(REPO)): sha(Path(__file__))}}
(stage / 'final-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print('C77 final health: rootRO0755, PCM closed, p3 off, taint0, UI off; ancestry/image/SDK preserved')
