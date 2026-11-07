#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C67: source-only muxretro consumer of the C65/C66 frontend provider."""
from pathlib import Path
import json, re, shutil, subprocess, tarfile, tempfile
from phase4_candidate import inventory, sha, sums, validate

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
area = work / 'muxretro-provider'
area.mkdir(exist_ok=True)
baseline = work / 'network-tools/baseline.config'
assert (work / 'graphics-config/output/.config').read_bytes() == baseline.read_bytes()
parents = {}
for name in ['muxretro-package', 'muxretro-image', 'frontend-libs', 'frontend-libs-session', 'save-store-image']:
    proof = repo / 'dist/phase4' / name
    for n, h in sums(proof / 'SHA256SUMS').items():
        assert sha(proof / n) == h, (name, n)
    parents[name] = sha(proof / 'SHA256SUMS')
old = work / 'muxretro-package/build.mdou4mqr'
provider = work / 'frontend-libs/build.84o1r4aj'
old_report = json.loads((old / 'analysis.json').read_text())
provider_report = json.loads((provider / 'analysis.json').read_text())
qualified = json.loads((repo / 'dist/phase4/frontend-libs-session/analysis.json').read_text())
for directory, report, name in [(old, old_report, 'muxretro-package'), (provider, provider_report, 'frontend-libs')]:
    assert report['passed']
    assert (directory / 'analysis.json').read_bytes() == (repo / 'dist/phase4' / name / 'analysis.json').read_bytes()
    for n, h in report['source_sha256'].items():
        assert sha(repo / n) == h, n
assert qualified['passed'] and qualified['physical_image_input_audio_restore_and_return_confirmed']
assert qualified['parent_proofs_sha256']['frontend-libs'] == parents['frontend-libs']
assert qualified['libraries'] == {n: row['sha256'] for n, row in provider_report['libraries'].items()}
old_host = old / 'target/opt/muos/frontend/muxretro'
assert sha(old_host) == old_report['binary_sha256']
base = work / 'save-store-image/image.nlnmgzzb'
image = work / 'muxretro-image/image.n_uthilw/images/rootfs.ext4'
image_sha = json.loads((repo / 'dist/phase4/muxretro-image/analysis.json').read_text())['image_sha256']
assert sha(image) == image_sha
before = json.loads((base / 'expected-tree.json').read_text())
assert inventory(base / 'target') == before
stage = Path(tempfile.mkdtemp(prefix='build.', dir=area))
(area / 'latest-attempt').write_text(str(stage) + '\n')
source = stage / 'prepared-source'
source.mkdir()
old_sources = json.loads((old / 'source-files.json').read_text())
assert old_sources == json.loads((repo / 'dist/phase4/muxretro-package/source-files.json').read_text())
assert {str(p.relative_to(old / 'prepared-source')): sha(p) for p in (old / 'prepared-source').rglob('*') if p.is_file()} == old_sources
for n, digest in old_sources.items():
    if not n.startswith(('frontend/', 'rcheevos/')):
        continue
    src = old / 'prepared-source' / n
    assert sha(src) == digest and not src.is_symlink()
    dest = source / n
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
# C60's source-only inputs are reused, not re-investigated/repatched/rebuilt.
# The provider carries the LVGL spelling LICENCE; preserve that notice too.
shutil.copyfile(provider / 'prepared-source/frontend/vendor/lvgl/LICENCE', source / 'frontend/vendor/lvgl/LICENCE')
shared = {}
for p in (provider / 'prepared-source/frontend').rglob('*'):
    if not p.is_file():
        continue
    relative = str(p.relative_to(provider / 'prepared-source/frontend'))
    if relative.startswith('retro/') or relative == 'phase4-frontend-libs.mk':
        continue
    peer = source / 'frontend' / relative
    assert peer.is_file() and sha(peer) == sha(p), relative
    shared[relative] = sha(p)
pkg = repo / 'port/buildroot-muxretro/package/muos-muxretro-provider'
shutil.copyfile(pkg / 'build-host.sh', source / 'build-host.sh')
assert 'GNU GENERAL PUBLIC LICENSE' in (source / 'frontend/LICENSE').read_text()
assert 'MIT License' in (source / 'rcheevos/LICENSE').read_text()
names = list(provider_report['libraries'])
for n in names:
    assert sha(provider / 'target/opt/muos/frontend/lib' / n) == qualified['libraries'][n]
(source / 'provider-staging.sha256').write_text(''.join(qualified['libraries'][n] + '  usr/lib/' + n + '\n' for n in names))
(source / 'provider-runtime.sha256').write_text(''.join(qualified['libraries'][n] + '  /opt/muos/frontend/lib/' + n + '\n' for n in names))
meta = {'frontend_revision': json.loads((old / 'prepared-source/provenance.json').read_text())['frontend_revision'],
        'C60_source_files_manifest_sha256': sha(old / 'source-files.json'),
        'provider_recipe': 'muos-frontend-libs', 'provider_C65_analysis_sha256': sha(provider / 'analysis.json'),
        'provider_C66_proof_sha256': parents['frontend-libs-session'],
        'shared_frontend_source_files_matched': len(shared), 'headers_match_provider': True,
        'link_source': 'dependency staging/usr/lib; no private frontend SDK',
        'activation': 'manual caller only; no core, ROM, save or service',
        'build_script_sha256': sha(pkg / 'build-host.sh'), 'private_only': True}
(source / 'provenance.json').write_text(json.dumps(meta, indent=2) + '\n')
license_names = ['frontend/LICENSE', 'rcheevos/LICENSE', 'frontend/retro/core/libretro.h',
                 *('frontend/vendor/' + n + '/LICENSE' for n in ['miniz', 'xxhash', 'stb', 'mini', 'json', 'mdns']),
                 'frontend/vendor/lvgl/LICENCE']
(pkg / 'muos-muxretro-provider.hash').write_text('# Pinned source license hashes.\n' + ''.join(
    'sha256  ' + sha(source / n) + '  ' + n + '\n' for n in license_names))
expected = {str(p.relative_to(source)): sha(p) for p in source.rglob('*') if p.is_file()}
for n in expected:
    assert (source / n).suffix not in {'.o', '.a', '.so'}
    assert b'\0' not in (source / n).read_bytes(), n
(stage / 'source-files.json').write_text(json.dumps(expected, indent=2, sort_keys=True) + '\n')
(stage / 'shared-frontend-sources.json').write_text(json.dumps(shared, indent=2, sort_keys=True) + '\n')
site = area / 'source'
if site.exists():
    assert not site.is_symlink() and not any(p.is_symlink() for p in site.rglob('*'))
    assert {str(p.relative_to(site)): sha(p) for p in site.rglob('*') if p.is_file()} == expected
else:
    shutil.copytree(source, site)
rel = lambda p: '/work/' + str(p.relative_to(work))
container = (work / 'rootfs-container.iid').read_text().strip()
def run(label, code, timeout=120):
    (stage / (label + '.sh')).write_text(code)
    cmd = ['podman', 'run', '--rm', '--network=none', '--read-only', '--cap-drop=all', '--security-opt=no-new-privileges',
           '--userns=keep-id', '--tmpfs', '/tmp:rw,nosuid,nodev,size=1g',
           '-v', f'{work}:/work:rw,z', '-v', f'{repo}/port:/port:ro,z', container, 'sh', '-eu', '-c', code]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    for suffix, value in [('stdout', r.stdout), ('stderr', r.stderr), ('exit', str(r.returncode) + '\n')]:
        (stage / (label + '.' + suffix)).write_text(value)
    assert r.returncode == 0, (stage, label, r.stderr[-2000:], r.stdout[-1000:])
    return r.stdout
output = stage / 'output'
minimal = stage / 'minimal.defconfig'
minimal.write_text('BR2_aarch64=y\nBR2_cortex_a35=y\nBR2_TOOLCHAIN_BUILDROOT_GLIBC=y\nBR2_TOOLCHAIN_BUILDROOT_CXX=y\nBR2_PACKAGE_ROCKCHIP_MALI=y\n')
external = 'BR2_EXTERNAL="/port/buildroot /port/buildroot-frontend /port/buildroot-muxretro"'
run('kconfig', f'''make -C /work/buildroot O={rel(output)} {external} BR2_DEFCONFIG={rel(minimal)} defconfig
cp {rel(output)}/.config {rel(stage)}/default.config
/work/buildroot/utils/config --file {rel(output)}/.config --enable BR2_PACKAGE_MUOS_MUXRETRO_PROVIDER
make -C /work/buildroot O={rel(output)} {external} olddefconfig
cp {rel(output)}/.config {rel(stage)}/opt-in.config
make -C /work/buildroot O={rel(output)} {external} muos-muxretro-provider-rsync
make -s --no-print-directory -C /work/buildroot O={rel(output)} {external} printvars VARS=MUOS_MUXRETRO_PROVIDER_BUILDDIR > {rel(stage)}/build-vars.txt
make -s --no-print-directory -C /work/buildroot O={rel(output)} {external} muos-muxretro-provider-show-info > {rel(stage)}/package-info.json
''')
def selected(name):
    return {s for s in (stage / name).read_text().splitlines() if s.endswith('=y')}
assert 'BR2_PACKAGE_MUOS_MUXRETRO_PROVIDER=y' not in selected('default.config')
assert 'BR2_PACKAGE_MUOS_FRONTEND_LIBS=y' not in selected('default.config')
for n in ['MUOS_MUXRETRO_PROVIDER', 'MUOS_FRONTEND_LIBS', 'SDL2', 'SDL2_IMAGE', 'SDL2_MIXER', 'SDL2_TTF',
          'HARFBUZZ', 'FREETYPE', 'LIBPNG', 'LIBCURL', 'FFMPEG', 'FFMPEG_SWSCALE', 'LIBARCHIVE', 'OPENSSL', 'ZLIB']:
    assert 'BR2_PACKAGE_' + n + '=y' in selected('opt-in.config'), n
for n in ['MUOS_MUXRETRO', 'MUOS_CORE', 'MUOS_R35S_SESSION', 'MUOS_R35S_BOOT', 'MUOS_R35S_LAUNCHER_ONCE', 'MUOS_SAVE_STORE']:
    assert 'BR2_PACKAGE_' + n + '=y' not in selected('opt-in.config'), n
assert 'BR2_MUOS_PRIVATE_FRONTEND_SDK=y' not in selected('opt-in.config')
info = json.loads((stage / 'package-info.json').read_text())['muos-muxretro-provider']
assert 'muos-frontend-libs' in info['dependencies']
match = re.fullmatch(r'MUOS_MUXRETRO_PROVIDER_BUILDDIR=(/work/[^\n]+)\n', (stage / 'build-vars.txt').read_text())
assert match
build = work / match[1].removeprefix('/work/')
assert build.is_relative_to(stage)
assert {str(p.relative_to(build)): sha(p) for p in build.rglob('*') if p.is_file() and not p.name.startswith('.')} == expected
run('legal-info', f'make -C /work/buildroot O={rel(output)} {external} muos-muxretro-provider-legal-info\n')
archives = list((output / 'legal-info').rglob('muos-muxretro-provider-*.tar.gz'))
assert len(archives) == 1
with tarfile.open(archives[0]) as tar:
    members = {str(Path(m.name).relative_to('muos-muxretro-provider-1')): tar.extractfile(m).read()
               for m in tar.getmembers() if m.isfile()}
assert set(members) == set(expected)
for n, data in members.items():
    assert data == (source / n).read_bytes(), n
for n in license_names:
    assert sha(output / 'legal-info/licenses/muos-muxretro-provider-1' / n) == sha(source / n), n
run('kconfig-refusals', f'''/work/buildroot/utils/config --file {rel(output)}/.config --enable BR2_MUOS_PRIVATE_FRONTEND_SDK --enable BR2_PACKAGE_MUOS_MUXRETRO
make -C /work/buildroot O={rel(output)} {external} olddefconfig
cp {rel(output)}/.config {rel(stage)}/old-host-conflict.config
cp {rel(stage)}/opt-in.config {rel(output)}/.config
/work/buildroot/utils/config --file {rel(output)}/.config --keep-case --disable BR2_aarch64 --enable BR2_i386 --enable BR2_PACKAGE_MUOS_MUXRETRO_PROVIDER
make -C /work/buildroot O={rel(output)} {external} olddefconfig
cp {rel(output)}/.config {rel(stage)}/wrong-arch.config
cp {rel(stage)}/opt-in.config {rel(output)}/.config
make -C /work/buildroot O={rel(output)} {external} olddefconfig
cmp {rel(stage)}/opt-in.config {rel(output)}/.config
''')
assert 'BR2_PACKAGE_MUOS_MUXRETRO=y' in selected('old-host-conflict.config')
assert 'BR2_PACKAGE_MUOS_MUXRETRO_PROVIDER=y' not in selected('old-host-conflict.config')
assert 'BR2_i386=y' in selected('wrong-arch.config')
assert 'BR2_PACKAGE_MUOS_MUXRETRO_PROVIDER=y' not in selected('wrong-arch.config')
# Copy the existing dependency sysroot. Never install provider files into the shared SDK.
sysroot = stage / 'staging'
run('copy-staging', f'cp -a --reflink=auto /work/graphics-config/output/host/aarch64-buildroot-linux-gnu/sysroot {rel(sysroot)}\n')
for n in names:
    assert not (sysroot / 'usr/lib' / n).exists()
provider_build = provider / 'output/build/muos-frontend-libs-1'
for n in names:
    assert sha(provider_build / 'frontend-bin/lib' / n) == qualified['libraries'][n]
target = stage / 'target'
target.mkdir()
harness = stage / 'recipe.mk'
harness.write_text(f'''TARGET_CC := /work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc
TARGET_AR := /work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-ar
PKG_CONFIG_HOST_BINARY := /work/graphics-config/output/host/bin/pkg-config
STAGING_DIR := {rel(sysroot)}
TARGET_CFLAGS := -O2 -mcpu=cortex-a35
TARGET_DIR := {rel(target)}
INSTALL := install
sep = $(newline)
define newline


endef
generic-package =
include /port/buildroot-frontend/package/muos-frontend-libs/muos-frontend-libs.mk
include /port/buildroot-muxretro/package/muos-muxretro-provider/muos-muxretro-provider.mk
.PHONY: all
all: {rel(build)}/.c67-build
{rel(provider_build)}/.c67-staging:
\t$(MUOS_FRONTEND_LIBS_INSTALL_STAGING_CMDS)
{rel(provider_build)}/.c67-target:
\t$(MUOS_FRONTEND_LIBS_INSTALL_TARGET_CMDS)
{rel(build)}/.c67-build: {rel(provider_build)}/.c67-staging
\t$(MUOS_MUXRETRO_PROVIDER_BUILD_CMDS)
\t$(MUOS_MUXRETRO_PROVIDER_INSTALL_TARGET_CMDS)
{rel(build)}/.c67-install:
\t$(MUOS_MUXRETRO_PROVIDER_INSTALL_TARGET_CMDS)
''')
marker = stage / 'compiler-was-run'
stub = stage / 'compiler-must-not-run.sh'
stub.write_text('#!/bin/sh\ntouch ' + rel(marker) + '\nexit 94\n')
stub.chmod(0o755)
for bad in ['missing', *names]:
    fixture = stage / ('bad-' + bad)
    (fixture / 'usr/lib').mkdir(parents=True)
    if bad != 'missing':
        for n in names:
            shutil.copyfile(provider / 'target/opt/muos/frontend/lib' / n, fixture / 'usr/lib' / n)
        with (fixture / 'usr/lib' / bad).open('ab') as stream:
            stream.write(b'C67 intentional corruption\n')
    guard = stage / ('guard-' + bad + '.mk')
    guard.write_text(f'include {rel(harness)}\nTARGET_CC := {rel(stub)}\nSTAGING_DIR := {rel(fixture)}\n{rel(build)}/.c67-guard:\n\t$(MUOS_MUXRETRO_PROVIDER_BUILD_CMDS)\n')
    run('guard-' + bad, f'if make -f {rel(guard)} {rel(build)}/.c67-guard;then exit 1;fi\n[ ! -e {rel(marker)} ]\n')
run('recipe', f'make -f {rel(harness)} all\nmake -f {rel(harness)} {rel(provider_build)}/.c67-target\n', timeout=240)
binary = target / 'opt/muos/frontend/muxretro'
for n in names:
    assert sha(sysroot / 'usr/lib' / n) == sha(target / 'opt/muos/frontend/lib' / n) == qualified['libraries'][n]
run('elf', f'/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-readelf -h -l -d -n {rel(binary)}\n')
elf = (stage / 'elf.stdout').read_text()
for token in ['AArch64', 'DYN (Position-Independent Executable file)', '/lib/ld-linux-aarch64.so.1', 'GNU_RELRO', 'BIND_NOW', '/opt/muos/frontend/lib']:
    assert token in elf, token
assert re.findall(r'\(RUNPATH\).*\[(.*?)\]', elf) == ['/opt/muos/frontend/lib']
assert rel(sysroot / 'usr/lib') in (stage / 'recipe.stdout').read_text()
assert '/muxretro-package/platform' not in (stage / 'recipe.stdout').read_text()
manifests = ['usr/share/muos-muxretro-provider/payload.sha256', 'usr/share/muos-frontend-libs/payload.sha256']
target_files = set()
for name in manifests:
    records = sums(target / name)
    for n, h in records.items():
        assert sha(target / n.lstrip('/')) == h
    target_files |= {n.lstrip('/') for n in records} | {name}
assert {str(p.relative_to(target)) for p in target.rglob('*') if p.is_file()} == target_files
for n, h in sums(target / 'usr/share/muos-muxretro-provider/provider-runtime.sha256').items():
    assert sha(target / n.lstrip('/')) == h
composition = stage / 'composition'
shutil.copytree(base / 'target', composition, symlinks=True)
run('composition', f'make -f {rel(harness)} {rel(provider_build)}/.c67-target TARGET_DIR={rel(composition)}\nmake -f {rel(harness)} {rel(build)}/.c67-install TARGET_DIR={rel(composition)}\n')
after = inventory(composition)
changed = {n: {'before': v, 'after': after[n]} for n, v in before.items() if v != after[n]}
assert set(changed) == {'opt/muos/frontend/lib/' + n for n in names}
assert sum(row['before']['sha256'] != row['after']['sha256'] for row in changed.values()) == 2
assert all(row['before']['mode'] == 0o755 and row['after']['mode'] == 0o644 for row in changed.values())
added = {n: v for n, v in after.items() if n not in before}
assert {n for n, v in added.items() if v['type'] == 'file'} == target_files - set(before)
assert set(before) <= set(after)
validation = validate(composition)
assert validation['foundation_files'] == 97
for name in [*manifests, 'usr/libexec/muos-save-store/payload.sha256']:
    for n, h in sums(composition / name).items():
        assert sha(composition / n.lstrip('/')) == h, (name, n)
run('composition-loader', f'''root={rel(composition)}
. "$root/usr/libexec/muos-candidate-boot-checks"
candidate_boot_check "$root"
for op in --version --help;do
 qemu-aarch64 -cpu cortex-a35 -L / -E LD_BIND_NOW=1 -E LD_DEBUG=libs "$root/lib/ld-linux-aarch64.so.1" --inhibit-cache --library-path "$root/opt/muos/frontend/lib:$root/lib:$root/usr/lib" "$root/opt/muos/frontend/muxretro" "$op"
done
echo C67_PROVIDER_COMPOSITION_C07_AND_EAGER_CLI_PASSED
''')
loader = (stage / 'composition-loader.stderr').read_text()
for n in names:
    assert ('calling init: ' + rel(composition / 'opt/muos/frontend/lib' / n)) in loader, n
assert sha(image) == image_sha and inventory(base / 'target') == before
assert (work / 'graphics-config/output/.config').read_bytes() == baseline.read_bytes()
for n in names:
    assert not (work / 'graphics-config/output/host/aarch64-buildroot-linux-gnu/sysroot/usr/lib' / n).exists()
for name, h in parents.items():
    proof = repo / 'dist/phase4' / name
    assert sha(proof / 'SHA256SUMS') == h
    for n, digest in sums(proof / 'SHA256SUMS').items():
        assert sha(proof / n) == digest, (name, n)
(stage / 'composition-changed.json').write_text(json.dumps(changed, indent=2, sort_keys=True) + '\n')
(stage / 'composition-added.json').write_text(json.dumps(added, indent=2, sort_keys=True) + '\n')
(stage / 'expected-tree.json').write_text(json.dumps(after, indent=2, sort_keys=True) + '\n')
sources = [Path(__file__), *pkg.iterdir(),
           *(repo / 'port/buildroot-muxretro' / n for n in ['Config.in', 'external.desc', 'external.mk'])]
report = {'passed': True, 'experiment': 'C67_MUXRETRO_PROVIDER_CONSUMER',
          'default_off': True, 'real_Kconfig_rsync_legal_info': True,
          'wrong_arch_and_historical_host_conflict_refused': True, 'dependency_graph_contains_frontend_provider': True,
          'private_frontend_SDK_required': False, 'provider_staging_guard_cases': 5,
          'source_only_legal_archive_verified': True, 'source_archive_sha256': sha(archives[0]),
          'source_files': len(expected), 'shared_frontend_source_files_matched': len(shared), 'license_files': len(license_names),
          'binary_sha256': sha(binary), 'C60_binary_byte_identical': sha(binary) == old_report['binary_sha256'],
          'C66_native_evidence_reused': sha(binary) == old_report['binary_sha256'], 'new_native_session_executed': False,
          'runtime_provider': qualified['libraries'], 'C65_provider_recompiled': False,
          'provider_staging_installed_using_real_macro': True, 'staging_isolated': True,
          'shared_SDK_unchanged': True, 'target_files': sorted(target_files), 'private_composition': validation,
          'C56_existing_items': len(before), 'existing_items_changed': len(changed), 'existing_hashes_changed': 2,
          'existing_library_modes_changed_755_to_644': 4, 'composition_new_files': sum(v['type'] == 'file' for v in added.values()),
          'composition_new_directories': sum(v['type'] == 'directory' for v in added.values()),
          'composition_items': len(after), 'C56_items_removed': 0,
          'C07_boot_contract_and_eager_loader_passed': True, 'full_Buildroot_rebuild': False,
          'image_built_or_booted': False, 'C64_image_preserved_sha256': image_sha, 'device_contacted': False,
          'parent_proofs_sha256': parents, 'source_sha256': {str(p.relative_to(repo)): sha(p) for p in sources}}
(stage / 'analysis.json').write_text(json.dumps(report, indent=2) + '\n')
(area / 'latest-build').write_text(str(stage) + '\n')
print('C67 provider consumer source/legal/build/composition/CLI checks passed:', stage)
print('C60 binary byte identical:', report['C60_binary_byte_identical'])
