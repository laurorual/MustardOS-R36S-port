#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C71 offline exact migration/backup capsule. No SSH, mounts or media writes."""
from pathlib import Path
import json, os, shutil, subprocess, tarfile, tempfile
from phase4_candidate import sha, sums

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
area = work / 'provider-upgrade'
area.mkdir(exist_ok=True)
parents = {}
for name in ['muxretro-installed', 'muxretro-provider', 'muxretro-provider-session',
             'frontend-libs', 'provider-image', 'card-image', 'save-store-installed']:
    proof = repo / 'dist/phase4' / name
    for n, h in sums(proof / 'SHA256SUMS').items():
        assert sha(proof / n) == h, (name, n)
    parents[name] = sha(proof / 'SHA256SUMS')
new_stage = work / 'muxretro-provider/build.f9a1ac69'
new_report = json.loads((new_stage / 'analysis.json').read_text())
assert (new_stage / 'analysis.json').read_bytes() == (repo / 'dist/phase4/muxretro-provider/analysis.json').read_bytes()
qualified = json.loads((repo / 'dist/phase4/muxretro-provider-session/analysis.json').read_text())
assert qualified['passed'] and qualified['physical_image_input_audio_restore_and_return_confirmed']
assert qualified['host_binary_sha256'] == new_report['binary_sha256']
old_stage = work / 'muxretro-install/install.67io22z3'
old_plan = json.loads((old_stage / 'plan.json').read_text())
old_result = json.loads((old_stage / 'install-analysis.json').read_text())
assert old_result['passed'] and old_result['plan_sha256'] == sha(old_stage / 'plan.json')
old_proof = repo / 'dist/phase4/muxretro-installed'
assert (old_stage / 'plan.json').read_bytes() == (old_proof / 'plan.json').read_bytes()
base = work / 'save-store-image/image.nlnmgzzb/target'
old = {r['path']: {'sha256': r['sha256'], 'mode': r['mode']} for r in old_plan['files']}
old_sources = {n: old_stage / 'payload/new' / n for n in old}
for name in qualified['libraries']:
    rel = 'opt/muos/frontend/lib/' + name
    path = base / rel
    old[rel] = {'sha256': sha(path), 'mode': path.stat().st_mode & 0o777}
    old_sources[rel] = path
target = new_stage / 'target'
new = {p.relative_to(target).as_posix(): {'sha256': sha(p), 'mode': p.stat().st_mode & 0o777}
       for p in target.rglob('*') if p.is_file()}
assert len(old) == 17 and len(new) == 31 and len(set(old) & set(new)) == 5
assert len(set(old) - set(new)) == 12 and len(set(new) - set(old)) == 26
for n, r in old.items():
    assert not old_sources[n].is_symlink() and sha(old_sources[n]) == r['sha256']
    assert old_sources[n].stat().st_mode & 0o777 == r['mode']
for n in new:
    assert not (target / n).is_symlink()
added = json.loads((new_stage / 'composition-added.json').read_text())
new_dirs = sorted((n for n, r in added.items() if r['type'] == 'directory'), key=lambda n: (len(Path(n).parts), n))
old_dirs = old_plan['absent_directories']
assert len(new_dirs) == 29 and len(old_dirs) == 13 and not set(new_dirs) & set(old_dirs)
assert old_dirs == sorted(old_dirs, key=lambda n: (len(Path(n).parts), n))
preserved = sums(base / 'usr/libexec/muos-session/prerequisites.sha256')
assert len(preserved) == 97
store_plan = json.loads((repo / 'dist/phase4/save-store-installed/plan.json').read_text())
for row in store_plan['files']:
    preserved['/' + row['path']] = row['sha256']
assert len(preserved) == 101 and not set(n.lstrip('/') for n in preserved) & (set(old) | set(new))
stage = Path(tempfile.mkdtemp(prefix='prepare.', dir=area))
payload = stage / 'payload'
payload.mkdir()
for side, records in [('old', old), ('new', new)]:
    for name, row in records.items():
        source = old_sources[name] if side == 'old' else target / name
        destination = payload / side / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        destination.chmod(row['mode'])
    (payload / ('BEFORE' if side == 'old' else 'AFTER')).write_text(''.join(
        row['sha256'] + ' ' + f'{row["mode"]:o}' + ' ' + name + '\n' for name, row in sorted(records.items())))
(payload / 'preserved.sha256').write_text(''.join(h + '  ' + n.lstrip('/') + '\n' for n, h in sorted(preserved.items())))
policy = stage / 'policy.sh'
functions = {'c71_before': (payload / 'BEFORE').read_text().splitlines(),
             'c71_after': (payload / 'AFTER').read_text().splitlines(),
             'c71_union': sorted(set(old) | set(new)), 'c71_removed': sorted(set(old) - set(new)),
             'c71_old_dirs': old_dirs, 'c71_new_dirs': new_dirs,
             'c71_metadata_roots': ['usr/share/muos-muxretro', 'usr/share/licenses/muos-muxretro',
                 'usr/share/muos-frontend-libs', 'usr/share/muos-muxretro-provider',
                 'usr/share/licenses/muos-frontend-libs', 'usr/share/licenses/muos-muxretro-provider']}
policy.write_text('# SPDX-License-Identifier: MIT\n# Generated exact C71 policy; no runtime path arguments.\n' + ''.join(
    name + "() {\ncat <<'C71_FIXED_POLICY'\n" + '\n'.join(rows) + '\nC71_FIXED_POLICY\n}\n'
    for name, rows in functions.items()))
transaction = repo / 'port/device/rk-r35s-p0/provider-upgrade/transaction.sh'
shutil.copyfile(transaction, stage / 'transaction.sh')
sources = [Path(__file__), transaction, repo / 'port/scripts/phase4_candidate.py']
plan = {'passed': True, 'experiment': 'C71_OFFLINE_PROVIDER_UPGRADE_PLAN',
    'parent_proofs_sha256': parents, 'C67_analysis_sha256': sha(new_stage / 'analysis.json'),
    'C62_plan_sha256': sha(old_stage / 'plan.json'), 'before': old, 'after': new,
    'old_directories': old_dirs, 'new_directories': new_dirs, 'replace_files': 5,
    'add_files': 26, 'remove_obsolete_metadata_files': 12, 'preserved_prerequisites': 101,
    'selective_backup_files': 17, 'selective_backup_contains_only_public_payloads': True,
    'snapshot_private_counter_seed_keys_preferences_or_saves_copied': False,
    'native_C68_component_qualification_reused': True,
    'runtime_requires_C46_menu_override': True, 'activation': 'manual only',
    'new_native_session_executed': False, 'device_contacted': False, 'device_written': False,
    'image_C70_flashed': False, 'source_sha256': {str(p.relative_to(repo)): sha(p) for p in sources}}
(stage / 'plan.json').write_text(json.dumps(plan, indent=2, sort_keys=True) + '\n')
with (stage / 'backup.json').open('x') as stream:
    json.dump({'schema': 1, 'plan_sha256': sha(stage / 'plan.json'), 'before_files': old,
        'directories_originally_present': old_dirs, 'directories_originally_absent': new_dirs,
        'restore_private_state': False, 'original_public_payloads_in': 'payload/old'}, stream, indent=2)
    stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
files = [p for p in sorted(payload.rglob('*')) if p.is_file()] + [policy, stage / 'transaction.sh']
(stage / 'SHA256SUMS').write_text(''.join(sha(p) + '  ' + str(p.relative_to(stage)) + '\n' for p in files))
with tarfile.open(stage / 'deployment.tar', 'w') as archive:
    for p in files + [stage / 'SHA256SUMS']:
        info = archive.gettarinfo(str(p), arcname=str(p.relative_to(stage)))
        info.uid = info.gid = 0; info.uname = info.gname = 'root'
        with p.open('rb') as stream:
            archive.addfile(info, stream)
(stage / 'manifest.json').write_text(json.dumps({'plan_sha256': sha(stage / 'plan.json'),
    'backup_sha256': sha(stage / 'backup.json'), 'deployment_sha256': sha(stage / 'deployment.tar')}, indent=2) + '\n')
for p in [stage / 'plan.json', stage / 'backup.json', stage / 'manifest.json', stage / 'deployment.tar']:
    with p.open('rb') as stream: os.fsync(stream.fileno())
fd = os.open(stage, os.O_DIRECTORY); os.fsync(fd); os.close(fd)
assert (work / 'graphics-config/output/.config').read_bytes() == (work / 'network-tools/baseline.config').read_bytes()
subprocess.run(['bash', '-n', str(stage / 'transaction.sh')], check=True)
subprocess.run(['bash', '-n', str(policy)], check=True)
(area / 'latest-plan').write_text(str(stage) + '\n')
print('C71 exact plan and public rollback payload prepared offline:', stage)
