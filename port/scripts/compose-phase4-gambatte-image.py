#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C78: serialize the approved additive Gambatte composition into private ext4."""
from pathlib import Path
import importlib.util, json, re, shutil, subprocess, tempfile
from phase4_candidate import inventory, sha, sums, validate
from phase4_card_image import regular_single

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
area = work / 'gambatte-image'
area.mkdir(exist_ok=True)
baseline = work / 'network-tools/baseline.config'
assert (work / 'graphics-config/output/.config').read_bytes() == baseline.read_bytes()
parents = {}
for name in ['provider-image', 'card-image', 'gambatte-package', 'gambatte-installed', 'installed-core-session']:
    proof = repo / 'dist/phase4' / name
    for n, h in sums(proof / 'SHA256SUMS').items(): assert sha(proof / n) == h, (name, n)
    parents[name] = sha(proof / 'SHA256SUMS')

source = work / 'gambatte-package/build.tgnlr06f'
base = work / 'provider-image/image.izief28e'
def report(stage, proof_name, filename='analysis.json'):
    frozen = repo / 'dist/phase4' / proof_name / filename
    assert (stage / filename).read_bytes() == frozen.read_bytes()
    row = json.loads(frozen.read_text()); assert row['passed']
    for n, h in row.get('source_sha256', {}).items(): assert sha(repo / n) == h, n
    return row

package = report(source, 'gambatte-package')
prior = report(base, 'provider-image')
card_stage = Path((work / 'card-image/latest-image').read_text().strip()).resolve()
assert card_stage.is_relative_to(work / 'card-image')
card = report(card_stage, 'card-image')
card_image = card_stage / 'muos-r35s-panel0-c70-private.img'
# The path is fixed by the frozen C70 builder, never a block device argument.
regular_single(card_image)
assert sha(card_image) == card['image_sha256']
base_image = base / 'images/rootfs.ext4'
regular_single(base_image)
assert sha(base_image) == prior['image_sha256']
before = json.loads((base / 'expected-tree.json').read_text())
expected = json.loads((source / 'expected-tree.json').read_text())
added = json.loads((source / 'composition-added.json').read_text())
assert (source / 'composition-added.json').read_bytes() == (repo / 'dist/phase4/gambatte-package/composition-added.json').read_bytes()
assert before == json.loads((repo / 'dist/phase4/provider-image/expected-tree.json').read_text())
planned = source / 'composition'
assert inventory(base / 'target') == before and inventory(planned) == expected
assert len(before) == 3386 and len(expected) == 3403 and len(added) == 17
assert set(expected) == set(before) | set(added) and not set(before) & set(added)
assert all(expected[n] == v for n, v in before.items())
assert all(expected[n] == v for n, v in added.items())
assert all(re.fullmatch(r'(opt/muos/share/core|usr/share/(licenses/)?muos-gambatte)(/[A-Za-z0-9_.-]+)*', n)
           and '..' not in Path(n).parts for n in added)
files = {n: r for n, r in added.items() if r['type'] == 'file'}
dirs = {n: r for n, r in added.items() if r['type'] == 'directory'}
assert len(files) == 9 and len(dirs) == 8 and len(files) + len(dirs) == len(added)
assert all(r['mode'] == 0o644 for r in files.values())
assert all(r['mode'] == 0o755 for r in dirs.values())
core_name = 'opt/muos/share/core/gambatte_libretro.so'
qualified = json.loads((repo / 'dist/phase4/installed-core-session/analysis.json').read_text())
assert qualified['passed'] and qualified['physical_image_input_audio_restore_and_return_confirmed']
assert qualified['core_path'] == '/' + core_name
assert qualified['core_sha256'] == package['core_sha256'] == files[core_name]['sha256']
assert qualified['installed_host_and_provider4_and_core_used'] and not qualified['core_ELF_transferred']
assert validate(planned)['foundation_files'] == 97
manifests = ['usr/share/muos-gambatte/payload.sha256', 'usr/share/muos-frontend-libs/payload.sha256',
             'usr/share/muos-muxretro-provider/payload.sha256', 'usr/share/muos-muxretro-provider/provider-runtime.sha256',
             'usr/libexec/muos-save-store/payload.sha256']
def check_payload(root):
    for name in manifests:
        for n, h in sums(root / name).items(): assert sha(root / n.lstrip('/')) == h, (name, n)
    review = json.loads((root / 'usr/share/muos-gambatte/license-review.json').read_text())
    assert review['private_experiment_only'] and not review['redistribution_approved']
    assert review['status'] == 'combined-license-review-pending'
check_payload(planned)

stage = Path(tempfile.mkdtemp(prefix='image.', dir=area))
(area / 'latest-attempt').write_text(str(stage) + '\n')
rel = lambda p: '/work/' + str(p.relative_to(work))
container = (work / 'rootfs-container.iid').read_text().strip()
def run(label, code, timeout=90):
    (stage / (label + '.sh')).write_text(code)
    cmd = ['podman', 'run', '--rm', '--network=none', '--read-only', '--cap-drop=all',
           '--security-opt=no-new-privileges', '--userns=keep-id', '--tmpfs', '/tmp:rw,nosuid,nodev,size=1g',
           '-v', f'{work}:/work:rw,z', container, 'sh', '-eu', '-c', code]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    for ext, v in [('stdout', r.stdout), ('stderr', r.stderr), ('exit', str(r.returncode) + '\n')]:
        (stage / (label + '.' + ext)).write_text(v)
    assert r.returncode == 0, (stage, label, r.stderr[-1800:], r.stdout[-800:])
    return r.stdout

boot = 'usr/libexec/muos-candidate-boot-checks'
run('planned-boot-contract', f'. {rel(planned / boot)}\ncandidate_boot_check {rel(planned)}\n')
(stage / 'images').mkdir()
image = stage / 'images/rootfs.ext4'
# Exclusive creation in a new stage; neither existing images nor devices are writable targets.
with base_image.open('rb') as src, image.open('xb') as dest: shutil.copyfileobj(src, dest)
regular_single(image)
assert image.stat().st_ino != base_image.stat().st_ino or image.stat().st_dev != base_image.stat().st_dev
commands = []
for n, r in sorted(dirs.items(), key=lambda item: (len(Path(item[0]).parts), item[0])):
    commands += [f'mkdir /{n}', f'set_inode_field /{n} mode 040{r["mode"]:03o}',
                 f'set_inode_field /{n} uid 0', f'set_inode_field /{n} gid 0']
for n, r in sorted(files.items()):
    commands += [f'write {rel(planned / n)} /{n}', f'set_inode_field /{n} mode 0100{r["mode"]:03o}',
                 f'set_inode_field /{n} uid 0', f'set_inode_field /{n} gid 0']
(stage / 'debugfs.commands').write_text('\n'.join(commands) + '\n')
run('write-image', f'debugfs -w -f {rel(stage / "debugfs.commands")} {rel(image)}\n')
image_sha = sha(image)
run('fsck', f'e2fsck -fn {rel(image)}\n')
assert sha(image) == image_sha
(stage / 'inode.commands').write_text(''.join('stat /' + n + '\n' for n in ['', *sorted(added)]) + 'stats\n')
inodes = run('inodes', f'debugfs -f {rel(stage / "inode.commands")} {rel(image)}\n')
for n in ['', *sorted(added)]:
    match = re.search(r'debugfs: stat ' + re.escape('/' + n) + r'\n(.*?)(?=debugfs: |\Z)', inodes, re.S)
    assert match and re.search(r'User:\s+0\s+Group:\s+0', match[1]), n
    mode = added[n]['mode'] if n else 0o755
    assert re.search(r'Mode:\s+0' + f'{mode:o}' + r'\b', match[1]), n
    if n in files:
        assert re.search(r'Type: regular', match[1]) and re.search(r'Links:\s+1\b', match[1]), n
    else: assert re.search(r'Type: directory', match[1]), n
root = stage / 'target'; root.mkdir(mode=0o755)
run('readback', f'/work/graphics-config/output/host/bin/fakeroot debugfs -R "rdump / {rel(root)}" {rel(image)}\n')
assert inventory(root) == expected and root.stat().st_mode & 0o777 == 0o755
validation = validate(root); assert validation['foundation_files'] == 97
check_payload(root)
run('readback-boot-contract', f'. {rel(root / boot)}\ncandidate_boot_check {rel(root)}\n')
(stage / '.config').write_bytes(baseline.read_bytes())
spec = importlib.util.spec_from_file_location('rootfs_audit', repo / 'port/scripts/verify-phase4-rootfs.py')
audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
static = audit.verify(stage)
old_static = json.loads((base / 'static-audit.json').read_text())
assert static['userspace_aarch64_count'] == old_static['userspace_aarch64_count'] + 1 == 308
assert static['elf_aarch64_count'] == old_static['elf_aarch64_count'] + 1
for k in ['kernel_module_aarch64_et_rel_count', 'module_release', 'interpreters', 'glibc_linux_abi_note']:
    assert static[k] == old_static[k], k
for k in ['label', 'bytes', 'compat', 'incompat', 'ro_compat']: assert static['ext4'][k] == old_static['ext4'][k], k
assert static['ext4']['sha256'] == image_sha
(stage / 'static-audit.json').write_text(json.dumps(static, indent=2) + '\n')

# No additions under any loader search directory and no old bytes changed:
# preserve all C69 executable dependency signatures instead of replaying 174 loaders.
coverage = json.loads((base / 'loader-coverage.json').read_text())
assert coverage == json.loads((repo / 'dist/phase4/provider-image/loader-coverage.json').read_text())
assert coverage['passed'] and coverage['dynamic_programs'] == len(coverage['programs']) == 174
search_dirs = {'opt/muos/frontend/lib', 'lib', 'usr/lib'}
assert all(str(Path(n).parent) not in search_dirs for n in added)
for name, row in coverage['programs'].items():
    deps = row['resolved_dependency_sha256']; assert name in deps
    assert all(before[n]['sha256'] == expected[n]['sha256'] == h for n, h in deps.items()), name
(stage / 'loader-reuse.json').write_text(json.dumps({'passed': True, 'programs_reused': 174,
    'C69_coverage_sha256': sha(base / 'loader-coverage.json'), 'no_loader_search_directory_additions': True,
    'all_transitive_dependency_hashes_unchanged': True}, indent=2) + '\n')
# Exercise dlopen against the extracted image, using the same pinned metadata-only probe.
# The probe calls API/version metadata, never retro_init or retro_load_game.
probe_source = stage / 'identity-check.c'
shutil.copyfile(repo / 'port/diagnostics/phase4-gb-identity-check.c', probe_source)
assert sha(probe_source) == package['source_sha256']['port/diagnostics/phase4-gb-identity-check.c']
probe = stage / 'identity-check'
abi = run('core-readback-ABI', f'''/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc -O2 -mcpu=cortex-a35 -I{rel(root)}/usr/share/licenses/muos-gambatte/libgambatte/libretro-common/include {rel(probe_source)} -ldl -o {rel(probe)}
/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-readelf -h -l -d --wide {rel(root / core_name)}
qemu-aarch64 -cpu cortex-a35 -L {rel(root)} -E LD_BIND_NOW=1 -E LD_LIBRARY_PATH={rel(root)}/usr/lib:{rel(root)}/lib {rel(probe)} {rel(root / core_name)}
''')
assert 'C48_GB_IDENTITY_OK API=1 memory_content=1 ROM_loaded=0' in abi
assert 'AArch64' in abi and 'GNU_RELRO' in abi and '(BIND_NOW)' in abi
assert sha(image) == image_sha and sha(base_image) == prior['image_sha256']
assert sha(card_image) == card['image_sha256'] and inventory(base / 'target') == before
assert inventory(planned) == expected
assert (work / 'graphics-config/output/.config').read_bytes() == baseline.read_bytes()
(stage / 'expected-tree.json').write_text(json.dumps(expected, indent=2, sort_keys=True) + '\n')
sources = [Path(__file__), repo / 'port/scripts/phase4_candidate.py', repo / 'port/scripts/phase4_card_image.py',
           repo / 'port/scripts/verify-phase4-rootfs.py', repo / 'port/scripts/verify-phase4-modules.py',
           repo / 'port/device/rk-r35s-p0/candidate/boot-checks.sh', repo / 'port/diagnostics/phase4-gb-identity-check.c']
result = {**validation, 'passed': True, 'experiment': 'C78_PRIVATE_GAMBATTE_EXT4',
    'private_only': True, 'redistribution_approved': False, 'combined_license_review_pending': True,
    'source_build': str(source), 'source_composition': str(planned), 'parent_proofs_sha256': parents,
    'C75_analysis_sha256': sha(source / 'analysis.json'), 'base_C69_image_sha256': prior['image_sha256'],
    'C70_card_image_preserved_sha256': card['image_sha256'], 'image_sha256': image_sha,
    'image_bytes': image.stat().st_size, 'core_sha256': package['core_sha256'],
    'new_files': 9, 'new_directories': 8, 'existing_items_changed': 0, 'base_items_preserved': 3386,
    'readback_items': 3403, 'full_readback_inventory_matched': True, 'fsck_exit': 0,
    'new_inodes_and_root_owned_by_root': True, 'new_and_root_inode_modes_verified': 18,
    'written_regular_single_link_files': 9, 'C07_boot_contract_before_and_after': True,
    'factory_boot_counter': 0, 'all_package_manifests_verified': True, 'ext4_features_preserved': True,
    'C69_dependency_loader_checks_reused': 174, 'core_eager_API1_readback_probe_passed': True,
    'probe_sha256': sha(probe), 'core_initialized': False, 'ROM_loaded': False,
    'C77_native_component_evidence_reused': True, 'new_native_session_executed': False,
    'diagnostic_caller_included': False, 'ROM_saves_credentials_seed_or_hostkeys_included': False,
    'device_contacted': False, 'device_written': False, 'original_32GB_or_Deck_accessed': False,
    'candidate_boot_tested': False, 'full_Buildroot_rebuild': False, 'SDK_config_unchanged': True,
    'image_bit_reproducibility_qualified': False, 'source_sha256': {str(p.relative_to(repo)): sha(p) for p in sources}}
(stage / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
(area / 'latest-image').write_text(str(stage) + '\n')
print('C78 private ext4/readback/fsck/core metadata passed:', stage)
print('Image SHA256:', image_sha)
