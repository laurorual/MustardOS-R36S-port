#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C68 read-only final health and immutable ancestry audit after RAM cleanup."""
from pathlib import Path
import argparse, json, subprocess
from phase4_candidate import sha
from phase4_muxretro_provider_session import historical, current_common, REPO, WORK, proof

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('stage', type=Path)
args = p.parse_args()
stage = args.stage.resolve()
r = json.loads((stage / 'analysis.json').read_text())
assert r['passed'] and r['RAM_removed'] and r['cleanup_passed']
assert not r['installed_host_used'] and r['host_ELF_transferred'] and r['exact_C66_boot_retained']
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
code = common + context['infra'] + '''
[ "$(stat -c '%u:%g:%a' /)" = 0:0:755 ]
[ "$(cat /proc/sys/kernel/tainted)" = 0 ]
[ "$(cat /proc/asound/card0/pcm0p/sub0/status)" = closed ]
if pidof muxfrontend muxretro muxlaunch muinput muhotkey pipewire wireplumber dbus-daemon mulog >/dev/null;then exit 64;fi
if findmnt -rn -o SOURCE | grep -Eq '^/dev/mmcblk[0-9]+p3$';then exit 64;fi
'''
code += "echo C68_FINAL_rootRO0755_PCMclosed_p3off_taint0_UIoff_installedPayloadValid\n"
ssh = ['ssh', '-p', '2222', '-i', str(WORK / 'private/c07-client'), '-oIdentitiesOnly=yes',
       '-oStrictHostKeyChecking=yes', '-oHostKeyAlias=[192.168.15.17]:2222',
       '-oUserKnownHostsFile=' + str(WORK / 'private/c07-known_hosts'), '-oBatchMode=yes',
       '-oConnectTimeout=6', 'root@' + observation['host']]
(stage / 'final-health.sh').write_text(code)
result = subprocess.run(ssh + ['sh -s'], input=code, capture_output=True, text=True, timeout=35)
for suffix, value in [('stdout', result.stdout), ('stderr', result.stderr), ('exit', str(result.returncode) + '\n')]:
    (stage / ('final-health.' + suffix)).write_text(value)
assert result.returncode == 0, (stage, result.stderr)
assert result.stdout == observation['infrastructure'] + 'C68_FINAL_rootRO0755_PCMclosed_p3off_taint0_UIoff_installedPayloadValid\n'
assert sha(WORK / 'muxretro-image/image.n_uthilw/images/rootfs.ext4') == provider['C64_image_preserved_sha256']
assert (WORK / 'graphics-config/output/.config').read_bytes() == (WORK / 'network-tools/baseline.config').read_bytes()
parents = {n: sha(proof(n) / 'SHA256SUMS') for n in
           ['installed-host-session', 'muxretro-installed', 'frontend-libs', 'muxretro-image', 'frontend-libs-session', 'muxretro-provider']}
report = {'passed': True, 'experiment': 'C68_FINAL_READONLY_HEALTH',
          'C63_identity_assets_and_boot_history_matched': True,
          'C54_C58_C61_C63_store_inventories_matched': True,
          'C64_image_preserved_sha256': provider['C64_image_preserved_sha256'],
          'SDK_config_unchanged': True, 'parent_proofs_sha256': parents,
          'source_sha256': {str(Path(__file__).resolve().relative_to(REPO)): sha(Path(__file__))}}
(stage / 'final-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print('C68 final health: rootRO0755, PCM closed, p3 off, taint0, UI off; ancestry/image/SDK preserved')
