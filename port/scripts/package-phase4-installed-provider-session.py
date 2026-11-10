#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C73 sanitized native receipts; never commercial content or private IDs."""
from pathlib import Path
import json, re, shutil, tempfile
from phase4_candidate import sha, sums
from phase4_installed_provider_session import AREA, REPO, WORK, historical, proof

_, _, _, provider_stage, provider, _ = historical()
stage = Path((AREA / 'latest-load').read_text().strip())
checks = Path((AREA / 'latest-checks').read_text().strip())
r = json.loads((stage / 'analysis.json').read_text())
a = json.loads((stage / 'technical-analysis.json').read_text())
c = json.loads((checks / 'analysis.json').read_text())
f = json.loads((stage / 'final-audit.json').read_text())
physical = json.loads((stage / 'physical-observation.json').read_text())
assert r['passed'] and a['passed'] and c['passed'] and f['passed']
assert r['checks_analysis_sha256'] == sha(checks / 'analysis.json')
assert a['session_analysis_sha256'] == physical['session_analysis_sha256'] == sha(stage / 'analysis.json')
assert physical['image_and_navigation_confirmed'] and physical['sound_clean_and_audible_confirmed']
assert physical['restore_to_saved_position_confirmed'] and physical['launcher_return_confirmed']
assert physical['new_save_requested'] is False
assert r['native_eager_provider_and_installed_host_CLI_passed'] and r['process_maps_confirmed']
assert r['new_boot_explicitly_bound'] and not r['exact_C63_boot_retained']
assert r['exact_C66_boot_retained'] and r['installed_host_used'] and not r['host_ELF_transferred']
assert r['store_byte_identical_to_C63'] and not r['agent_requested_reboot']
assert f['closure_uses_recorded_session_receipts'] and not f['new_SSH_or_current_boot_health_claimed']
for name, digest in f['recorded_receipts_sha256'].items():
    assert sha(stage / name) == digest, name
marker = 'C47_GLOBAL_MOUNTS_IDENTICAL\nC47_RAM_REMOVED_ROOT_RO_FOUNDATION97_NETWORK_OK\nC73_STOPPED_SCREEN_WRITTEN_NO_UI_ROOT_RO\n'
assert r['libraries'] == {n: v['sha256'] for n, v in provider['libraries'].items()}
out = REPO / 'dist/phase4/installed-provider-session'
assert not out.exists()
public = Path(tempfile.mkdtemp(prefix='public.', dir=AREA))
sources = {Path(__file__), REPO / 'docs/archive/phase4/phase4-installed-provider-session.md'}
def clean(value):
    if isinstance(value, dict):
        return {k: ('private' if k in {'ROM_sha256', 'private_identity', 'kernel_boot_id'} else clean(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [clean(v) for v in value]
    return value
for label, report in [('checks', c), ('load', r), ('technical', a), ('physical', physical), ('final', f)]:
    dest = public / label
    dest.mkdir()
    (dest / 'analysis.json').write_text(json.dumps(clean(report), indent=2, ensure_ascii=False) + '\n')
    for n, h in report.get('source_sha256', {}).items():
        assert sha(REPO / n) == h, n
        sources.add(REPO / n)
for suffix in ['py', 'stdout', 'stderr', 'exit']:
    shutil.copyfile(checks / ('fixtures.' + suffix), public / 'checks' / ('fixtures.' + suffix))
for name in ['watch-maps.stdout', 'native-provider-ABI.stdout', 'installed-host-check.stdout']:
    shutil.copyfile(stage / name, public / 'load' / name)
shutil.copyfile(stage / 'collected/state-metadata.txt', public / 'load/state-metadata.txt')
(public / 'load/final-health-markers.txt').write_text(marker)
lines = []
for name in ['core.log', 'game.log', 'return.log', 'store-seed.log', 'store-verify.log']:
    lines += [line for line in (stage / 'collected' / name).read_text().splitlines()
              if re.match(r'^(C(44|45|46|50|51|53|58|63|66|68|73)_|RETRO_RUNNER_EXIT=)', line)]
(public / 'load/markers.txt').write_text('\n'.join(lines) + '\n')
parents = {n: sha(proof(n) / 'SHA256SUMS') for n in
           ['installed-host-session', 'muxretro-installed', 'frontend-libs', 'muxretro-image', 'frontend-libs-session', 'muxretro-provider', 'provider-upgrade-native']}
for source in sorted(sources):
    dest = public / 'source' / source.relative_to(REPO)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, dest)
(public / 'analysis.json').write_text(json.dumps({
    'passed': True, 'experiment': 'C73_NATIVE_MUXRETRO_PROVIDER',
    'boot_sequence': r['boot_sequence'], 'historical_C63_boot_sequence': r['prior_boot_sequence'],
    'new_boot_explicitly_bound': True, 'historical_bindings_modified': False,
    'checks': c['case_count'], 'physical_image_input_audio_restore_and_return_confirmed': True,
    'libraries': r['libraries'], 'menu_variant_C46_sha256': r['menu_variant_C46_sha256'],
    'qualification_scope': 'C72 installed C67 host and C65 provider; C46 menu override in RAM; C57 store load-only',
    'host_binary_sha256': r['host_binary_sha256'], 'host_ELF_transferred': False, 'installed_host_used': True,
    'exact_C66_boot_retained': True, 'C67_build_analysis_sha256': r['C67_analysis_sha256'],
    'provider_libraries_installed': True, 'installed_host_modified': False,
    'store_byte_identical_to_C63': True, 'root_read_only': True, 'RAM_removed': True,
    'agent_requested_reboot': False, 'current_boot_origin_or_shutdown_verified': False,
    'image_boot_or_automatic_startup_qualified': False, 'continuous_audio_or_long_run_qualified': False,
    'new_host_internal_deadline_exercised': False,
    'recorded_session_health_boot': r['boot_sequence'], 'new_current_boot_health_claimed': False,
    'visual_footer_flicker_reported_before_and_after_session': True,
    'raw_states_ROMs_PNGs_PCM_ELFs_private_IDs_included': False, 'parent_proofs_sha256': parents
}, indent=2) + '\n')
for p in public.rglob('*'):
    assert not p.is_symlink()
    if p.is_file():
        assert p.suffix.lower() not in {'.gb', '.gbc', '.so', '.img', '.ext4', '.png', '.wav', '.sav', '.srm', '.state', '.bundle', '.ini', '.tar', '.gz'}
        data = p.read_bytes()
        assert not data.startswith(b'\x7fELF')
        assert not any(v.encode() in data for v in [r['private_identity'], r['ROM_sha256'], r['kernel_boot_id']]), p
assert (WORK / 'graphics-config/output/.config').read_bytes() == (WORK / 'network-tools/baseline.config').read_bytes()
(public / 'SHA256SUMS').write_text(''.join(sha(p) + '  ' + str(p.relative_to(public)) + '\n'
                                         for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public, out)
for n, h in sums(out / 'SHA256SUMS').items():
    assert sha(out / n) == h
print('C73 sanitized native proof frozen:', out)
