#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compose a private candidate from clean C07 and pinned native recipe outputs."""
from pathlib import Path
import hashlib, importlib.util, json, shutil, stat, subprocess, tempfile
from phase4_candidate import inventory, local, sha, sums, validate

repo = Path(__file__).resolve().parents[2]; work = repo / 'build/phase4'
area = work / 'rootfs-candidate'; area.mkdir(exist_ok=True)
baseline = work / 'network-tools/baseline.config'
assert (work / 'graphics-config/output/.config').read_bytes() == baseline.read_bytes()
def proof(name):
    folder = repo / 'dist/phase4' / name
    for name, digest in sums(folder / 'SHA256SUMS').items(): assert sha(folder / name) == digest
    return folder
base_proof = proof('network-recovery-preboot'); session_proof = proof('session-package-independent')
proof('wifi-only-policy')
audio_proof = proof('audio-buffers-correction')
audio_plan = json.loads((audio_proof / 'installed/plan.json').read_text())
assert json.loads((audio_proof / 'analysis.json').read_text())['user_confirmed_clean_audible_installed_profile']
base = work / 'linux-diagnostic/network-recovery.zz7sq2ve'
base_meta = json.loads((base_proof / 'manifest.json').read_text())
assert sha(base / 'rootfs.ext4') == base_meta['rootfs_sha256']
assert (base / 'manifest.json').read_bytes() == (base_proof / 'manifest.json').read_bytes()
session = Path((work / 'runtime-session/latest-service').read_text().strip())
sm = json.loads((session / 'manifest.json').read_text())
assert sha(session / 'manifest.json') == json.loads((session_proof / 'analysis.json').read_text())['prepared_manifest_sha256']
for name, digest in sm['source_sha256'].items(): assert sha(repo / name) == digest, name
profile_check = Path((work / 'runtime-profile/latest-checks').read_text().strip())
profile = profile_check / 'recipe-source'
native_stage=Path((area/'latest-update').read_text().strip())
native_plan=json.loads((native_stage/'plan.json').read_text())
assert native_plan['experiment'] in ['C26_AUDIO_BUFFERS','C27_VOLUME_CALIBRATION','C36_PCM_PRIME'] and json.loads((native_stage/'install-analysis.json').read_text())['passed']
primed = native_plan['experiment'] == 'C36_PCM_PRIME'
native_root = Path(native_plan['candidate_stage'])/'target'
if primed:
    assert sha(Path(native_plan['candidate_stage'])/'analysis.json') == native_plan['candidate_analysis_sha256']
    assert validate(native_root)['foundation_files'] == 97
    for name in ['primed-launcher-boot','primed-launcher-fallback']:
        approved = proof(name)
        qualified = json.loads((approved/'analysis.json').read_text())
        assert qualified['passed'] and qualified['audio_passed'] and qualified['direct_zero_PCM_priming']
        assert sha(approved/'installation/plan.json') == sha(native_stage/'plan.json')
    approved_profile = sha(native_root/'usr/share/muos-r35s-profile/manifest.json')
else:
    approved_profile = next(row['after']['sha256'] for row in native_plan['files'] if row['path'] == 'usr/share/muos-r35s-profile/manifest.json')
assert sha(profile / 'payload/manifest.json') == approved_profile
assert json.loads((profile_check / 'report.json').read_text())['passed']
wifi = Path((work / 'network-warm/latest-wifi-policy-build').read_text().strip())
wm = json.loads((wifi / 'manifest.json').read_text())
for name, digest in wm['sources'].items():
    if name == 'port/buildroot/Config.in':
        prior=repo/'dist/phase4/wifi-only-policy/port-source/Config.in'
        assert sha(prior)==digest
        addition=b'source "$BR2_EXTERNAL_MUOS_R35S_PATH/package/muos-r35s-launcher-once/Config.in"\n'
        # C55 adds only a default-off CLI menu entry. Keep exact lineage;
        # this composition still installs only its explicitly named packages.
        addition+=b'source "$BR2_EXTERNAL_MUOS_R35S_PATH/package/muos-save-store/Config.in"\n'
        assert (repo/name).read_bytes()==prior.read_bytes()+addition
    else: assert sha(repo / name) == digest, name
survey = Path((area / 'latest-survey').read_text().strip())
installed = sums(survey / 'installed-foundation.sha256'); assert len(installed) == 55
for name, digest in installed.items():
    if name != '/etc/inittab': assert sha(local(base / 'extracted', name)) == digest, name
stage = Path(tempfile.mkdtemp(prefix='composition.', dir=area)); (area / 'latest-attempt').write_text(str(stage) + '\n')
root = stage / 'target'; shutil.copytree(base / 'extracted', root, symlinks=True)
original = inventory(root)
# Reuse the audited C22 ELF bytes, not the old profile-source digest. No
# compiler/SDK mutation is needed for the C25 shell package or the C26 hook.
session_source = stage / 'session-source'; shutil.copytree(session / 'recipe-source', session_source)
profile_payload = profile / 'payload'
(session_source / 'service/profile-source.sha256').write_text(''.join(sha(p) + '  ' + str(p.relative_to(profile_payload)) + '\n' for p in sorted(profile_payload.rglob('*')) if p.is_file()))
core_source = stage / 'core-source'; core_source.mkdir()
core_hook = repo / 'port/device/rk-r35s-p0/S95muos-core'
assert sha(core_hook) == (sha(native_root/'etc/init.d/S95muos-core') if primed else next(row['after']['sha256'] for row in audio_plan['files'] if row['path'] == 'etc/init.d/S95muos-core'))
shutil.copyfile(core_hook, core_source / 'S95muos-core')
launcher_source = repo / 'port/device/rk-r35s-p0/launcher-once'
# Invoke actual install macros. The base image has already had its foundation
# overlay applied; the profile hook MUST run after the three package installs.
rel = lambda p: '/work/' + str(p.relative_to(work))
harness = stage / 'install.mk'
harness.write_text(f'''TARGET_DIR := {rel(root)}
INSTALL := install
BR2_EXTERNAL_MUOS_R35S_PATH := /port/buildroot
generic-package =
include /port/buildroot/package/muos-core/muos-core.mk
include /port/buildroot/package/muos-r35s-profile/muos-r35s-profile.mk
include /port/buildroot/package/muos-r35s-session/muos-r35s-session.mk
include /port/buildroot/package/muos-r35s-wifi-only/muos-r35s-wifi-only.mk
include /port/buildroot/package/muos-r35s-launcher-once/muos-r35s-launcher-once.mk
{rel(profile / '.candidate-install')}:
\t$(MUOS_R35S_PROFILE_INSTALL_TARGET_CMDS)
{rel(session_source / '.candidate-install')}:
\t$(MUOS_R35S_SESSION_INSTALL_TARGET_CMDS)
\t$(MUOS_R35S_SESSION_INSTALL_INIT_SYSV)
{rel(wifi / 'source/.candidate-install')}:
\t$(MUOS_R35S_WIFI_ONLY_INSTALL_TARGET_CMDS)
{rel(core_source / '.candidate-install')}:
\t$(MUOS_CORE_INSTALL_INIT_SYSV)
/port/device/rk-r35s-p0/launcher-once/.candidate-install:
\t$(MUOS_R35S_LAUNCHER_ONCE_INSTALL_TARGET_CMDS)
''')
container = ['podman', 'run', '--rm', '--network=none', '--read-only', '--cap-drop=all',
    '--security-opt=no-new-privileges', '--userns=keep-id', '--tmpfs', '/tmp:rw,nosuid,nodev',
    '-v', f'{work}:/work:rw,z', '-v', f'{repo}/port:/port:ro,z', (work / 'rootfs-container.iid').read_text().strip()]
def run(label, code, timeout=120):
    (stage / (label + '.sh')).write_text(code)
    r = subprocess.run(container + ['sh', '-eu', '-c', code], capture_output=True, text=True, timeout=timeout)
    (stage / (label + '.stdout')).write_text(r.stdout); (stage / (label + '.stderr')).write_text(r.stderr)
    assert r.returncode == 0, (label, r.stderr, r.stdout[-1000:], stage)
    return r.stdout
run('install', f'make -f {rel(harness)} {rel(profile / ".candidate-install")} {rel(session_source / ".candidate-install")} {rel(wifi / "source/.candidate-install")} {rel(core_source / ".candidate-install")} /port/device/rk-r35s-p0/launcher-once/.candidate-install\n/port/scripts/phase4-runtime-post-build.sh {rel(root)}\n')
if primed:
    policy = repo/'port/device/rk-r35s-p0/core-wireplumber.conf'
    assert sha(policy) == sha(native_root/'opt/muos/device/control/wireplumber.conf')
    shutil.copyfile(policy,root/'opt/muos/device/control/wireplumber.conf')
(root / 'etc/default/muos-session').write_text('# C23 private composition; no automatic session.\nenabled=0\npreferences_enabled=0\nlease_seconds=180\nprofile_dir=/usr/share/muos-r35s-profile\nprerequisites=/usr/libexec/muos-session/prerequisites.sha256\n')
(root / 'etc/default/muos-session').chmod(0o644)
tab = root / 'etc/inittab'; tab_text = tab.read_text(); assert 'muos-c25' not in tab_text
tab_text = tab_text.replace('::sysinit:/usr/libexec/muos-c07-run\n', '::sysinit:/usr/libexec/muos-c25/select.sh\n::sysinit:/usr/libexec/muos-c07-run\n::sysinit:/usr/libexec/muos-c25/session.sh start\n')
tab_text = tab_text.replace('::shutdown:/usr/libexec/muos-c07-run stop\n', '::shutdown:/usr/libexec/muos-c25/session.sh stop\n::shutdown:/usr/libexec/muos-c07-run stop\n'); tab.write_text(tab_text)
# The factory C07 source predates C10's passive audio template and the
# diagnostic counter normally provisioned by the old directed installer.
bootstrap = root / 'sbin/muos-ext4-diag'
old_audio_guard = "grep -qx audio=0 /etc/default/muos-core || fail 'Audio must be disabled'"
text = bootstrap.read_text(); assert text.count(old_audio_guard) == 1
text = text.replace(old_audio_guard, ". /usr/libexec/muos-candidate-boot-checks\ncandidate_boot_check || fail 'C23 boot contract failed'")
bootstrap.write_text(text)
boot_checks = repo / 'port/device/rk-r35s-p0/candidate/boot-checks.sh'
shutil.copyfile(boot_checks, root / 'usr/libexec/muos-candidate-boot-checks')
(root / 'usr/libexec/muos-candidate-boot-checks').chmod(0o644)
c07_source = repo / 'port/device/rk-r35s-p0/network-diagnostic/run.sh'
assert 'umask 077' in c07_source.read_text() and 'chmod 600 "$sequence_dir/boot-seq.tmp"' in c07_source.read_text()
shutil.copyfile(c07_source, root / 'usr/libexec/muos-c07-run');(root / 'usr/libexec/muos-c07-run').chmod(0o755)
state = root / 'var/lib/muos-diagnostic'; assert not state.exists()
state.mkdir(mode=0o700)
(state / 'boot-seq').write_text('0\n'); (state / 'boot-seq').chmod(0o600)
paths = set(installed)
paths.update('/' + name for name in json.loads((root / 'usr/share/muos-r35s-profile/manifest.json').read_text())['files'])
paths.update('/' + name for name in [
    'bin/busybox', 'opt/muos/frontend/muvarctl',
    'opt/muos/frontend/muinput', 'opt/muos/frontend/muos-sdl-map', 'usr/libexec/muos-diag-card-guard',
    'etc/default/muos-session', 'etc/default/muos-core', 'etc/default/muos-ui',
    'etc/init.d/S98muos-session', 'etc/modprobe.d/90-muos-r35s-wifi-only.conf',
    'usr/libexec/muos-session/payload.sha256', 'usr/libexec/muos-candidate-boot-checks'])
paths.update('/' + str(p.relative_to(root)) for p in (root / 'usr/libexec/muos-c25').iterdir() if p.is_file())
paths.add('/usr/share/licenses/muos-r35s-launcher-once/LICENSE')
if primed: paths.add('/opt/muos/device/control/wireplumber.conf')
for command in ['findmnt', 'flock', 'blkid', 'mount', 'alsactl', 'wpctl', 'jq']:
    locations = [f'/{prefix}/{command}' for prefix in ['bin', 'sbin', 'usr/bin', 'usr/sbin'] if local(root, f'/{prefix}/{command}').is_file()]
    assert locations, command
    paths.add(locations[0])
foundation = {name: sha(local(root, name)) for name in sorted(paths)}
if primed:
    # Preserve the approved native manifest's order as well as its 97 hashes.
    approved_foundation=sums(native_root/'usr/libexec/muos-session/prerequisites.sha256')
    assert foundation == approved_foundation and len(foundation)==97
    foundation=approved_foundation
(root / 'usr/libexec/muos-session/prerequisites.sha256').write_text(''.join(h + '  ' + n + '\n' for n, h in foundation.items()))
(root / 'usr/libexec/muos-session/prerequisites.sha256').chmod(0o644)
report = validate(root)
run('boot-contract', f'. {rel(root)}/usr/libexec/muos-candidate-boot-checks\ncandidate_boot_check {rel(root)}\n')
final = inventory(root)
assert set(original) <= set(final), 'No removals allowed in C23'
changed = {n: v for n, v in final.items() if original.get(n) != v}
allowed = set(json.loads((root / 'usr/share/muos-r35s-profile/manifest.json').read_text())['files'])
allowed.update(['etc/inittab', 'etc/init.d/S95muos-core', 'etc/default/muos-session', 'etc/init.d/S98muos-session', 'etc/modprobe.d/90-muos-r35s-wifi-only.conf', 'sbin/muos-ext4-diag', 'usr/libexec/muos-candidate-boot-checks', 'usr/libexec/muos-c07-run', 'var/lib/muos-diagnostic/boot-seq'])
if primed: allowed.add('opt/muos/device/control/wireplumber.conf')
for name, record in changed.items():
    if record['type'] == 'directory': continue
    assert record['type'] == 'file' and (name in allowed or name.startswith(('usr/libexec/muos-c25/', 'usr/libexec/muos-session/', 'usr/share/muos-r35s-profile/', 'usr/share/licenses/muos-r35s-'))), name
(stage / 'changes.json').write_text(json.dumps(changed, indent=2) + '\n')
(stage / 'foundation.sha256').write_bytes((root / 'usr/libexec/muos-session/prerequisites.sha256').read_bytes())
(stage / 'expected-tree.json').write_text(json.dumps(final, sort_keys=True, indent=2) + '\n')
images = stage / 'images'; images.mkdir(); image = images / 'rootfs.ext4'
shutil.copyfile(base / 'rootfs.ext4', image)
commands = []
for name, record in sorted(changed.items(), key=lambda item: (len(Path(item[0]).parts), item[0])):
    if record['type'] == 'directory':
        assert name not in original
        commands.extend([f'mkdir /{name}', f'set_inode_field /{name} mode 040{record["mode"]:03o}', f'set_inode_field /{name} uid 0', f'set_inode_field /{name} gid 0'])
for name, record in sorted(changed.items()):
    if record['type'] != 'file': continue
    if name in original: commands.append(f'rm /{name}')
    commands.extend([f'write {rel(root / name)} /{name}', f'set_inode_field /{name} mode 0100{record["mode"]:03o}', f'set_inode_field /{name} uid 0', f'set_inode_field /{name} gid 0'])
(stage / 'debugfs.commands').write_text('\n'.join(commands) + '\n')
run('image', f'debugfs -w -f {rel(stage / "debugfs.commands")} {rel(image)}\ne2fsck -fn {rel(image)}\ndebugfs -R "stat /" {rel(image)}\n')
root.rename(stage / 'planned-target'); root.mkdir()
run('readback', f'/work/graphics-config/output/host/bin/fakeroot debugfs -R "rdump / {rel(root)}" {rel(image)}\n')
assert inventory(root) == final, 'Full image readback differs from planned files/modes/symlinks'
assert 'Mode:  0755' in (stage / 'image.stdout').read_text()
report = validate(root)
(stage / '.config').write_bytes(baseline.read_bytes())
spec = importlib.util.spec_from_file_location('rootfs_audit', repo / 'port/scripts/verify-phase4-rootfs.py')
audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
static = audit.verify(stage); (stage / 'static-audit.json').write_text(json.dumps(static, indent=2) + '\n')
# Resolve every dynamic userspace ELF through the final candidate loader under
# QEMU. Never execute target init or start device services on the host.
elfs = []
for name, record in final.items():
    if record['type'] != 'file' or name.startswith('lib/modules/'): continue
    path = root / name
    with path.open('rb') as source: magic = source.read(4)
    if magic == b'\x7fELF' and audit.elf_info(path)['interpreter']: elfs.append(name)
code = f'root={rel(root)}\n'
for name in elfs:
    code += f'qemu-aarch64 -cpu cortex-a35 -L "$root" -E LD_BIND_NOW=1 "$root/lib/ld-linux-aarch64.so.1" --inhibit-cache --library-path "$root/opt/muos/frontend/lib:$root/lib:$root/usr/lib" --list "$root/{name}" >/dev/null\n'
for path in [*(root / 'usr/libexec/muos-session').glob('*.sh'), *(root / 'usr/libexec/muos-c25').glob('*.sh'), root / 'etc/init.d/S95muos-core', root / 'usr/libexec/muos-candidate-boot-checks', root / 'sbin/muos-ext4-diag']:
    code += f'qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh -n {rel(path)}\n'
code += f'if qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh "$root/sbin/muos-ext4-diag"; then exit 1; else test "$?" = 64; fi\n'
run('loader', code)
run('readback-boot-contract', f'. {rel(root)}/usr/libexec/muos-candidate-boot-checks\ncandidate_boot_check {rel(root)}\n')
assert (work / 'graphics-config/output/.config').read_bytes() == baseline.read_bytes()
assert sha(base / 'rootfs.ext4') == base_meta['rootfs_sha256']
if primed:
    equivalent=['usr/libexec/muos-session/prerequisites.sha256','usr/libexec/muos-session/payload.sha256',
                'usr/libexec/muos-session/profile-source.sha256','usr/libexec/muos-c25/payload.sha256',
                'etc/inittab','etc/init.d/S95muos-core','opt/muos/device/control/wireplumber.conf',
                'usr/share/muos-r35s-profile/manifest.json','usr/share/muos-r35s-profile/profile.json',
                'usr/share/muos-r35s-profile/speaker-calibration.json']
    for name in equivalent: assert (root/name).read_bytes()==(native_root/name).read_bytes(),name
    (stage/'native-C36-equivalence.json').write_text(json.dumps({'passed':True,
        'native_plan_sha256':sha(native_stage/'plan.json'),'foundation97_identical':True,
        'public_file_sha256':{name:sha(root/name) for name in equivalent},
        'factory_counter':0,'live_counter_reset':False,'image_boot_tested':False},indent=2)+'\n')
record = {**report, 'experiment': 'MUOS-R35S-CANDIDATE-P4-C38' if primed else 'MUOS-R35S-CANDIDATE-P4-C27', 'private_only': True,
    'redistribution_approved': False, 'image_sha256': sha(image), 'image_bytes': image.stat().st_size,
    'base_image_sha256': base_meta['rootfs_sha256'], 'C22_manifest_sha256': sha(session / 'manifest.json'),
    'C07_base_matches_legacy_foundation_snapshot_except_inittab': 54, 'C07_counter_owns_umask_and_tmp_mode':True, 'post_overlay_profile_applied': True,
    'full_readback_inventory_matched': True, 'dynamic_ELF_loader_checks': len(elfs),
    'root_inode_mode': '0755', 'kernel_or_DTB_or_partition_changed': False, 'device_written': False,
    'candidate_boot_tested': False, 'boot_contract_checked_before_and_after_image':True, 'bootstrap_non_PID1_refused':True, 'factory_boot_counter':0, 'full_Buildroot_rebuild': False, 'SDK_baseline_preserved': True,
    'image_bit_reproducibility_qualified': False,
    'C25_and_C26_integrated': True, 'native_C26_plan_sha256':sha(audio_proof / 'installed/plan.json'),
    'selected_native_profile_plan_sha256':sha(native_stage/'plan.json'),
    'sources': {str(p.relative_to(repo)): sha(p) for p in [Path(__file__), repo / 'port/scripts/phase4_candidate.py', repo / 'port/scripts/apply-phase4-runtime-profile.py', repo / 'port/scripts/phase4-runtime-post-build.sh', boot_checks, c07_source, core_hook, repo / 'port/device/rk-r35s-p0/runtime-profile.json', repo / 'port/device/rk-r35s-p0/speaker-calibration.json', repo / 'port/buildroot/Config.in', repo / 'port/scripts/prepare-phase4-runtime-profile.py', repo / 'port/scripts/verify-phase4-rootfs.py', repo / 'port/scripts/verify-phase4-modules.py', *sorted(launcher_source.glob('*')), *sorted((repo / 'port/buildroot/package/muos-r35s-launcher-once').glob('*')), *[repo / f'port/buildroot/package/{n}/{n}.mk' for n in ['muos-core','muos-r35s-session','muos-r35s-profile','muos-r35s-wifi-only']]]}}
if primed:
    record['C36_direct_zero_PCM_integrated']=True
    record['native_C36_equivalence_sha256']=sha(stage/'native-C36-equivalence.json')
    record['sources'][str(policy.relative_to(repo))]=sha(policy)
(stage / 'analysis.json').write_text(json.dumps(record, indent=2) + '\n')
(area / 'latest-composition').write_text(str(stage) + '\n')
print('C38 primed private rootfs composed and statically verified:' if primed else 'C27/C25+C26 private rootfs composed and statically verified:', stage)
