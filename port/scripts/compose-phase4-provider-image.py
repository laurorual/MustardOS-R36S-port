#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C69 private provider/consumer image and dependency-selective loader audit."""
from pathlib import Path
import importlib.util, json, re, shlex, shutil, subprocess, tempfile
from phase4_candidate import inventory, local, sha, sums, validate

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
area = work / 'provider-image'
area.mkdir(exist_ok=True)
baseline = work / 'network-tools/baseline.config'
assert (work / 'graphics-config/output/.config').read_bytes() == baseline.read_bytes()
parents = {}
for name in ['rootfs-pcm-primed', 'save-store-image', 'muxretro-image', 'muxretro-provider',
             'frontend-libs', 'muxretro-provider-session']:
    proof = repo / 'dist/phase4' / name
    for n, h in sums(proof / 'SHA256SUMS').items():
        assert sha(proof / n) == h, (name, n)
    parents[name] = sha(proof / 'SHA256SUMS')
source = work / 'muxretro-provider/build.f9a1ac69'
source_report = json.loads((source / 'analysis.json').read_text())
assert (source / 'analysis.json').read_bytes() == (repo / 'dist/phase4/muxretro-provider/analysis.json').read_bytes()
assert source_report['passed']
for n, h in source_report['source_sha256'].items():
    assert sha(repo / n) == h, n
qualified = json.loads((repo / 'dist/phase4/muxretro-provider-session/analysis.json').read_text())
assert qualified['passed'] and qualified['physical_image_input_audio_restore_and_return_confirmed']
assert qualified['host_binary_sha256'] == source_report['binary_sha256']
assert qualified['libraries'] == source_report['runtime_provider']
assert qualified['parent_proofs_sha256']['muxretro-provider'] == parents['muxretro-provider']
base = work / 'save-store-image/image.nlnmgzzb'
base_report = json.loads((base / 'analysis.json').read_text())
assert (base / 'analysis.json').read_bytes() == (repo / 'dist/phase4/save-store-image/analysis.json').read_bytes()
base_image = base / 'images/rootfs.ext4'
assert sha(base_image) == base_report['image_sha256']
old_image = work / 'muxretro-image/image.n_uthilw/images/rootfs.ext4'
old_image_sha = source_report['C64_image_preserved_sha256']
assert sha(old_image) == old_image_sha
before = json.loads((base / 'expected-tree.json').read_text())
planned = source / 'composition'
expected = json.loads((source / 'expected-tree.json').read_text())
assert inventory(base / 'target') == before and inventory(planned) == expected
added = json.loads((source / 'composition-added.json').read_text())
changed = json.loads((source / 'composition-changed.json').read_text())
assert set(changed) == {'opt/muos/frontend/lib/' + n for n in qualified['libraries']}
assert len(before) == 3330 and len(expected) == 3386
assert len(added) == 56 and len(changed) == 4
assert all(row['type'] in {'file', 'directory'} for row in added.values())
assert all(row['after'] == expected[n] and row['before'] == before[n] for n, row in changed.items())
assert sum(row['before']['sha256'] != row['after']['sha256'] for row in changed.values()) == 2
assert set(expected) == set(before) | set(added)
assert all(expected[n] == row for n, row in before.items() if n not in changed)
validate(planned)
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
    for suffix, value in [('stdout', r.stdout), ('stderr', r.stderr), ('exit', str(r.returncode) + '\n')]:
        (stage / (label + '.' + suffix)).write_text(value)
    assert r.returncode == 0, (stage, label, r.stderr[-2000:], r.stdout[-1000:])
    return r.stdout
boot = 'usr/libexec/muos-candidate-boot-checks'
run('planned-boot-contract', f'. {rel(planned / boot)}\ncandidate_boot_check {rel(planned)}\n')
images = stage / 'images'
images.mkdir()
image = images / 'rootfs.ext4'
assert not image.exists()
shutil.copyfile(base_image, image)
assert image.is_file() and not image.is_symlink() and image.stat().st_nlink == 1
old_inode_commands = stage / 'old-inodes.commands'
old_inode_commands.write_text(''.join('stat /' + n + '\n' for n in sorted(changed)))
old_inodes = run('old-inodes', f'debugfs -f {rel(old_inode_commands)} {rel(image)}\n')
for name in changed:
    match = re.search(r'debugfs: stat /' + re.escape(name) + r'\n(.*?)(?=debugfs: |\Z)', old_inodes, re.S)
    assert match and re.search(r'Type: regular', match[1])
    assert re.search(r'Links:\s+1\b', match[1]) and re.search(r'Mode:\s+0755\b', match[1])
commands = ['rm /' + n for n in sorted(changed)]
for name, row in sorted(added.items(), key=lambda item: (len(Path(item[0]).parts), item[0])):
    if row['type'] == 'directory':
        commands += ['mkdir /' + name, f'set_inode_field /{name} mode 040{row["mode"]:03o}',
                     f'set_inode_field /{name} uid 0', f'set_inode_field /{name} gid 0']
files = {n: row for n, row in added.items() if row['type'] == 'file'}
files.update({n: row['after'] for n, row in changed.items()})
assert len(files) == 31
for name, row in sorted(files.items()):
    commands += [f'write {rel(planned / name)} /{name}', f'set_inode_field /{name} mode 0100{row["mode"]:03o}',
                 f'set_inode_field /{name} uid 0', f'set_inode_field /{name} gid 0']
(stage / 'debugfs.commands').write_text('\n'.join(commands) + '\n')
run('write-image', f'debugfs -w -f {rel(stage / "debugfs.commands")} {rel(image)}\n')
image_sha = sha(image)
run('fsck', f'e2fsck -fn {rel(image)}\n')
assert sha(image) == image_sha
inodes = ['/', *('/' + n for n in sorted(set(added) | set(changed)))]
(stage / 'inode.commands').write_text(''.join('stat ' + n + '\n' for n in inodes) + 'stats\n')
inode_text = run('inodes', f'debugfs -f {rel(stage / "inode.commands")} {rel(image)}\n')
for name in inodes:
    match = re.search(r'debugfs: stat ' + re.escape(name) + r'\n(.*?)(?=debugfs: |\Z)', inode_text, re.S)
    assert match and re.search(r'User:\s+0\s+Group:\s+0', match[1]), name
    mode = 0o755 if name == '/' else expected[name.lstrip('/')]['mode']
    assert re.search(r'Mode:\s+0' + f'{mode:o}' + r'\b', match[1]), name
    if name.lstrip('/') in files:
        assert re.search(r'Type: regular', match[1]) and re.search(r'Links:\s+1\b', match[1]), name
root = stage / 'target'
root.mkdir(mode=0o755)
run('readback', f'/work/graphics-config/output/host/bin/fakeroot debugfs -R "rdump / {rel(root)}" {rel(image)}\n')
assert inventory(root) == expected
validation = validate(root)
assert validation['foundation_files'] == 97
for name in ['usr/share/muos-frontend-libs/payload.sha256', 'usr/share/muos-muxretro-provider/payload.sha256',
             'usr/libexec/muos-save-store/payload.sha256', 'usr/share/muos-muxretro-provider/provider-runtime.sha256']:
    for n, h in sums(root / name).items():
        assert sha(root / n.lstrip('/')) == h, (name, n)
run('readback-boot-contract', f'. {rel(root / boot)}\ncandidate_boot_check {rel(root)}\n')
(stage / '.config').write_bytes(baseline.read_bytes())
spec = importlib.util.spec_from_file_location('rootfs_audit', repo / 'port/scripts/verify-phase4-rootfs.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
static = audit.verify(stage)
old_static = json.loads((base / 'static-audit.json').read_text())
assert static['userspace_aarch64_count'] == old_static['userspace_aarch64_count'] + 1 == 307
for key in ['kernel_module_aarch64_et_rel_count', 'module_release', 'interpreters', 'glibc_linux_abi_note']:
    assert static[key] == old_static[key], key
for key in ['label', 'bytes', 'compat', 'incompat', 'ro_compat']:
    assert static['ext4'][key] == old_static['ext4'][key], key
(stage / 'static-audit.json').write_text(json.dumps(static, indent=2) + '\n')
# Inventory all userspace dynamic metadata once with the existing GNU readelf.
# Classify refresh by transitive dependency bytes, not simply by executable hash.
elfs = []
for p in sorted(root.rglob('*')):
    if p.is_symlink() or not p.is_file() or p.suffix == '.ko':
        continue
    with p.open('rb') as stream:
        if stream.read(4) == b'\x7fELF':
            elfs.append(p)
assert len(elfs) == static['userspace_aarch64_count']
text = run('dynamic-metadata', '/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-readelf -l -d --wide ' +
           ' '.join(shlex.quote(rel(p)) for p in elfs) + '\n')
chunks = re.split(r'^File: (.+)\n', text, flags=re.M)
metadata = {}
for i in range(1, len(chunks), 2):
    path = chunks[i]
    assert path.startswith(rel(root) + '/')
    name = path.removeprefix(rel(root) + '/')
    body = chunks[i + 1]
    needed = re.findall(r'\(NEEDED\).*\[(.*?)\]', body)
    interpreter = re.findall(r'Requesting program interpreter: (.*?)\]', body)
    assert len(interpreter) <= 1
    metadata[name] = {'needed': needed, 'interpreter': interpreter[0] if interpreter else None}
assert set(metadata) == {str(p.relative_to(root)) for p in elfs}
def closure(name):
    found = set()
    def visit(relative):
        resolved = str(local(root, relative).relative_to(root))
        if resolved in found:
            return
        assert resolved in metadata, resolved
        found.add(resolved)
        row = metadata[resolved]
        if row['interpreter']:
            visit(row['interpreter'])
        for needed in row['needed']:
            if '/' in needed:
                assert needed.startswith('/'), needed
                visit(needed)
            else:
                assert re.fullmatch('[a-zA-Z0-9_.+-]+', needed), needed
                choices = [local(root, directory + '/' + needed) for directory in
                           ['opt/muos/frontend/lib', 'lib', 'usr/lib']]
                candidates = [p for p in choices if p.is_file()]
                assert candidates, (relative, needed)
                visit(str(candidates[0].relative_to(root)))
    visit(name)
    return sorted(found)
dynamic = {n for n, row in metadata.items() if row['interpreter']}
c38 = repo / 'dist/phase4/rootfs-pcm-primed'
old_coverage = set(re.findall(r'--list "\$root/(.*?)"', (c38 / 'loader.sh').read_text()))
assert len(old_coverage) == 172
c38_tree = json.loads((c38 / 'expected-tree.json').read_text())
assert all(before[n] == row for n, row in c38_tree.items())
assert base_report['base_C38_image_sha256'] == json.loads((c38 / 'analysis.json').read_text())['image_sha256']
c56_loader = (repo / 'dist/phase4/save-store-image/new-CLI-loader.sh').read_text()
c56_coverage = set(re.findall(r'--list "\$root/(.*?)"', c56_loader))
assert len(c56_coverage) == 1
assert dynamic == old_coverage | c56_coverage | {'opt/muos/frontend/muxretro'}
refreshed, reused = [], []
dependency_records = {}
for name in sorted(dynamic):
    deps = closure(name)
    signature = {n: expected[n]['sha256'] for n in deps}
    differences = [n for n in deps if n not in before or before[n].get('sha256') != signature[n]]
    if differences:
        refreshed.append(name)
    else:
        assert name in old_coverage | c56_coverage
        reused.append(name)
    dependency_records[name] = {'resolved_dependency_sha256': signature, 'changed_or_new_paths': differences,
                                'action': 'refresh' if differences else 'reuse_C38_C56'}
assert refreshed and reused and len(refreshed) + len(reused) == len(dynamic) == 174
code = f'root={rel(root)}\n'
for name in refreshed:
    code += f'qemu-aarch64 -cpu cortex-a35 -L "$root" -E LD_BIND_NOW=1 "$root/lib/ld-linux-aarch64.so.1" --inhibit-cache --library-path "$root/opt/muos/frontend/lib:$root/lib:$root/usr/lib" --list "$root/{name}" >/dev/null\n'
    code += f'echo C69_LOADER_PASS_{name}\n'
run('affected-loaders', code, timeout=180)
assert (stage / 'affected-loaders.stdout').read_text().count('C69_LOADER_PASS_') == len(refreshed)
(stage / 'loader-coverage.json').write_text(json.dumps({
    'passed': True, 'method': 'DT_NEEDED/interpreter closure under the explicit loader library path; compare C56 bytes',
    'dynamic_programs': len(dynamic), 'refreshed': refreshed, 'reused_identical_C38_C56': reused,
    'programs': dependency_records}, indent=2, sort_keys=True) + '\n')
assert sha(image) == image_sha and sha(base_image) == base_report['image_sha256']
assert sha(old_image) == old_image_sha and inventory(planned) == expected
assert inventory(base / 'target') == before
assert (work / 'graphics-config/output/.config').read_bytes() == baseline.read_bytes()
(stage / 'expected-tree.json').write_text(json.dumps(expected, indent=2, sort_keys=True) + '\n')
sources = [Path(__file__), repo / 'port/scripts/phase4_candidate.py', repo / 'port/scripts/verify-phase4-rootfs.py',
           repo / 'port/scripts/verify-phase4-modules.py', repo / 'port/device/rk-r35s-p0/candidate/boot-checks.sh']
report = {**validation, 'passed': True, 'experiment': 'C69_PRIVATE_PROVIDER_CONSUMER_EXT4',
          'private_only': True, 'redistribution_approved': False, 'source_build': str(source),
          'source_composition': str(planned), 'parent_proofs_sha256': parents,
          'C67_analysis_sha256': sha(source / 'analysis.json'), 'image_sha256': image_sha,
          'image_bytes': image.stat().st_size, 'base_C56_image_sha256': base_report['image_sha256'],
          'C64_image_preserved_sha256': old_image_sha, 'full_readback_inventory_matched': True,
          'readback_items': len(expected), 'existing_items_changed': 4, 'existing_hashes_changed': 2,
          'new_files': 27, 'new_directories': 29, 'written_regular_single_link_files': len(files),
          'new_inodes_and_root_owned_by_root': True, 'new_inodes_modes_verified': 60,
          'fsck_exit': 0, 'C07_boot_contract_before_and_after': True, 'factory_boot_counter': 0,
          'dynamic_programs': len(dynamic), 'new_loader_resolution_checks': len(refreshed),
          'identical_C38_C56_loader_checks_reused': len(reused), 'DT_NEEDED_closure_bytes_compared': True,
          'host_sha256': qualified['host_binary_sha256'], 'provider_libraries': qualified['libraries'],
          'C68_native_component_evidence_reused': True, 'new_native_session_executed': False,
          'full_Buildroot_rebuild': False, 'candidate_boot_tested': False, 'device_contacted': False,
          'device_written': False, 'kernel_DTB_bootloader_partition_changed': False,
          'image_bit_reproducibility_qualified': False, 'SDK_config_unchanged': True,
          'source_sha256': {str(p.relative_to(repo)): sha(p) for p in sources}}
(stage / 'analysis.json').write_text(json.dumps(report, indent=2) + '\n')
(area / 'latest-image').write_text(str(stage) + '\n')
print('C69 image/readback/fsck/dependency-selective loaders passed:', stage)
print('Image SHA256:', image_sha)
print('Loaders refreshed/reused:', len(refreshed), len(reused))
