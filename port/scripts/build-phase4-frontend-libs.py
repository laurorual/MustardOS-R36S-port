#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C65: source-only library provider, isolated Buildroot config and SDK harness."""
from pathlib import Path
import json, re, shutil, subprocess, tarfile, tempfile
from phase4_candidate import sha, sums

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
area = work / 'frontend-libs'
area.mkdir(exist_ok=True)
sdk_config = work / 'graphics-config/output/.config'
assert sdk_config.read_bytes() == (work / 'network-tools/baseline.config').read_bytes()
names = ['libui.so', 'libmuxcom.so', 'libmuxmod.so', 'libplutosvg.so']
foundation = work / 'foundation/frontend-source'
oldlib = work / 'rootfs-candidate/composition.w59vz7vo/target/opt/muos/frontend/lib'
old_hashes = {n: sha(oldlib / n) for n in names}
parents = {}
for name in ['muxretro-package', 'muxretro-installed', 'installed-host-session', 'muxretro-image']:
    proof = repo / 'dist/phase4' / name
    for n, digest in sums(proof / 'SHA256SUMS').items():
        assert sha(proof / n) == digest, (name, n)
    parents[name] = sha(proof / 'SHA256SUMS')
image = work / 'muxretro-image/image.n_uthilw/images/rootfs.ext4'
image_hash = '671a738792d5a6b718d698f8386488d14216c8f539541f2b6160e1bbc98a62a6'
assert sha(image) == image_hash
archive = work / 'menu/frontend-source.tar'
mojibake = repo / 'build/phase3/deps/mojibake-0.3.6.tar.gz'
assert sha(archive) == 'c638d1afd4d995792f5ee09ea647de6976a60ca80e82014591a3fdff400ee5ff'
assert sha(mojibake) == '156bb5c0c1f1265c5d75f4ef53ff4aab09c368e358b05f4f780ba6ec2575fed3'
stage = Path(tempfile.mkdtemp(prefix='build.', dir=area))
(area / 'latest-attempt').write_text(str(stage) + '\n')
reconstructed = stage / 'reconstructed'
reconstructed.mkdir()
with tarfile.open(archive) as tar:
    tar.extractall(reconstructed, filter='data')
patches = [repo / 'port/patches' / n for n in [
    '0003-frontend-r35s-panel0-board.patch', '0006-frontend-r35s-normalized-volume.patch']]
for patch in patches:
    subprocess.run(['git', '-C', str(reconstructed), 'apply', str(patch)], check=True)

def relevant(path):
    return path.suffix in {'.c', '.h', '.hpp', '.inc', '.def', '.mk'} or path.name in {
        'Makefile', 'LICENSE', 'LICENCE', 'COPYING', 'COPYING.LESSER'}

inputs = {str(p.relative_to(reconstructed)): p for p in reconstructed.rglob('*')
          if p.is_file() and relevant(p)}
old = {str(p.relative_to(foundation)): p for p in foundation.rglob('*')
       if p.is_file() and relevant(p) and p.name != 'phase4-frontend.mk'}
assert set(inputs) == set(old), (set(inputs) - set(old), set(old) - set(inputs))
for n, p in inputs.items():
    assert sha(p) == sha(old[n]), n
source = stage / 'prepared-source'
source.mkdir()
for n, p in inputs.items():
    out = source / 'frontend' / n
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(p, out)
with tarfile.open(mojibake) as tar:
    tar.extractall(stage / 'mojibake-unpack', filter='data')
moji = stage / 'mojibake-unpack/mojibake-0.3.6'
for p in moji.rglob('*'):
    if p.is_file() and (p.is_relative_to(moji / 'src') or p.name == 'LICENSE') and relevant(p):
        out = source / 'deps/mojibake-0.3.6' / p.relative_to(moji)
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, out)
        if p.is_relative_to(moji / 'src'):
            assert sha(out) == sha(work / 'foundation/deps/mojibake-0.3.6' / p.relative_to(moji))
for p in (moji / 'src').glob('*.h'):
    out = source / 'deps/include/mojibake' / p.name
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(p, out)
    assert sha(out) == sha(work / 'foundation/deps/include/mojibake' / p.name)
assert 'MIT License' in (source / 'deps/mojibake-0.3.6/LICENSE').read_text()
assert 'Version 3, 29 June 2007' in (source / 'frontend/LICENSE').read_text()
pkg = repo / 'port/buildroot-frontend/package/muos-frontend-libs'
makefile = repo / 'port/packaging/phase4-frontend-libs.mk'
probe_source = repo / 'port/diagnostics/phase4-frontend-libs-load.c'
shutil.copyfile(pkg / 'build-libs.sh', source / 'build-libs.sh')
shutil.copyfile(makefile, source / 'frontend/phase4-frontend-libs.mk')
provenance = {
    'frontend_revision': '5e8635b3b485eec9ad2ace141c415fd2df47d8f1',
    'frontend_archive_sha256': sha(archive), 'mojibake_archive_sha256': sha(mojibake),
    'patches': {p.name: sha(p) for p in patches}, 'upstream_text_files_matching_foundation': len(inputs),
    'build_makefile_sha256': sha(makefile), 'build_script_sha256': sha(pkg / 'build-libs.sh'),
    'variant': 'foundation; no C46 diagnostic patches', 'private_prebuilt_frontend_SDK_used': False,
    'automatic_activation': False, 'original_and_test_cards_accessed': False}
(source / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
license_names = ['frontend/LICENSE', 'frontend/vendor/lvgl/LICENCE',
                 'frontend/vendor/plutosvg/LICENSE', 'frontend/vendor/plutosvg/plutovg/LICENSE',
                 *('frontend/vendor/' + n + '/LICENSE' for n in ['json', 'mini', 'miniz', 'xxhash', 'stb', 'mdns']),
                 'deps/mojibake-0.3.6/LICENSE']
(pkg / 'muos-frontend-libs.hash').write_text('# Computed from the pinned prepared sources.\n' + ''.join(
    'sha256  ' + sha(source / n) + '  ' + n + '\n' for n in license_names))
expected = {str(p.relative_to(source)): sha(p) for p in source.rglob('*') if p.is_file()}
for n in expected:
    data = (source / n).read_bytes()
    assert b'\0' not in data and not data.startswith(b'\x7fELF'), n
(stage / 'source-files.json').write_text(json.dumps(expected, indent=2, sort_keys=True) + '\n')
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
    cmd = ['podman', 'run', '--rm', '--network=none', '--read-only', '--cap-drop=all',
           '--security-opt=no-new-privileges', '--userns=keep-id', '--memory=12g', '--pids-limit=2048',
           '--tmpfs', '/tmp:rw,nosuid,nodev,size=2g', '-v', f'{work}:/work:rw,z',
           '-v', f'{repo}/port:/port:ro,z', container, 'sh', '-eu', '-c', code]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    for suffix, value in [('stdout', result.stdout), ('stderr', result.stderr), ('exit', str(result.returncode) + '\n')]:
        (stage / (label + '.' + suffix)).write_text(value)
    assert result.returncode == 0, (label, stage, result.stderr[-2000:], result.stdout[-1000:])
    return result.stdout

output = stage / 'output'
minimal = stage / 'minimal.defconfig'
minimal.write_text('BR2_aarch64=y\nBR2_cortex_a35=y\nBR2_TOOLCHAIN_BUILDROOT_GLIBC=y\nBR2_TOOLCHAIN_BUILDROOT_CXX=y\nBR2_PACKAGE_ROCKCHIP_MALI=y\n')
external = 'BR2_EXTERNAL="/port/buildroot /port/buildroot-frontend"'
run('kconfig', f'''make -C /work/buildroot O={rel(output)} {external} BR2_DEFCONFIG={rel(minimal)} defconfig
cp {rel(output)}/.config {rel(stage)}/default.config
/work/buildroot/utils/config --file {rel(output)}/.config --enable BR2_PACKAGE_MUOS_FRONTEND_LIBS
make -C /work/buildroot O={rel(output)} {external} olddefconfig
cp {rel(output)}/.config {rel(stage)}/opt-in.config
make -C /work/buildroot O={rel(output)} {external} muos-frontend-libs-rsync
make -s --no-print-directory -C /work/buildroot O={rel(output)} {external} printvars VARS=MUOS_FRONTEND_LIBS_BUILDDIR > {rel(stage)}/build-vars.txt
make -s --no-print-directory -C /work/buildroot O={rel(output)} {external} muos-frontend-libs-show-info > {rel(stage)}/package-info.json
''')

def selected(name):
    return {s for s in (stage / name).read_text().splitlines() if s.endswith('=y')}

assert 'BR2_PACKAGE_MUOS_FRONTEND_LIBS=y' not in selected('default.config')
assert 'BR2_PACKAGE_MUOS_FRONTEND_LIBS=y' in selected('opt-in.config')
for n in ['SDL2', 'SDL2_IMAGE', 'SDL2_MIXER', 'SDL2_TTF', 'HARFBUZZ', 'FREETYPE', 'LIBPNG',
          'LIBCURL', 'FFMPEG', 'FFMPEG_SWSCALE', 'LIBARCHIVE', 'OPENSSL', 'ZLIB']:
    assert 'BR2_PACKAGE_' + n + '=y' in selected('opt-in.config'), n
for n in ['MUOS_MUXRETRO', 'MUOS_CORE', 'MUOS_R35S_SESSION', 'MUOS_R35S_BOOT',
          'MUOS_R35S_LAUNCHER_ONCE', 'MUOS_SAVE_STORE']:
    assert 'BR2_PACKAGE_' + n + '=y' not in selected('opt-in.config'), n
assert 'BR2_MUOS_PRIVATE_FRONTEND_SDK=y' not in selected('opt-in.config')
match = re.fullmatch(r'MUOS_FRONTEND_LIBS_BUILDDIR=(/work/[^\n]+)\n', (stage / 'build-vars.txt').read_text())
assert match
build = work / match[1].removeprefix('/work/')
assert build.is_relative_to(stage)
assert {str(p.relative_to(build)): sha(p) for p in build.rglob('*')
        if p.is_file() and not p.name.startswith('.')} == expected
run('legal-info', f'make -C /work/buildroot O={rel(output)} {external} muos-frontend-libs-legal-info\n')
archives = list((output / 'legal-info').rglob('muos-frontend-libs-*.tar.gz'))
assert len(archives) == 1
with tarfile.open(archives[0]) as tar:
    members = {str(Path(m.name).relative_to('muos-frontend-libs-1')): tar.extractfile(m).read()
               for m in tar.getmembers() if m.isfile()}
assert set(members) == set(expected)
for n, data in members.items():
    assert data == (source / n).read_bytes(), n
for n in license_names:
    assert sha(output / 'legal-info/licenses/muos-frontend-libs-1' / n) == sha(source / n), n
run('wrong-arch', f'''/work/buildroot/utils/config --file {rel(output)}/.config --keep-case --disable BR2_aarch64 --enable BR2_i386 --enable BR2_PACKAGE_MUOS_FRONTEND_LIBS
make -C /work/buildroot O={rel(output)} {external} olddefconfig
cp {rel(output)}/.config {rel(stage)}/wrong-arch.config
''')
assert 'BR2_i386=y' in selected('wrong-arch.config')
assert 'BR2_PACKAGE_MUOS_FRONTEND_LIBS=y' not in selected('wrong-arch.config')
target = stage / 'target'
staging = stage / 'staging'
target.mkdir()
staging.mkdir()
harness = stage / 'recipe.mk'
harness.write_text(f'''TARGET_CC := /work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc
TARGET_AR := /work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-ar
PKG_CONFIG_HOST_BINARY := /work/graphics-config/output/host/bin/pkg-config
STAGING_DIR := /work/graphics-config/output/host/aarch64-buildroot-linux-gnu/sysroot
TARGET_CFLAGS := -O2 -mcpu=cortex-a35
TARGET_DIR := {rel(target)}
INSTALL := install
sep = $(newline)
define newline


endef
generic-package =
include /port/buildroot-frontend/package/muos-frontend-libs/muos-frontend-libs.mk
.PHONY: all
all: {rel(build)}/.c65-build
{rel(build)}/.c65-build:
\t$(MUOS_FRONTEND_LIBS_BUILD_CMDS)
\t$(MUOS_FRONTEND_LIBS_INSTALL_TARGET_CMDS)
{rel(build)}/.c65-staging:
\t$(MUOS_FRONTEND_LIBS_INSTALL_STAGING_CMDS)
''')
run('recipe', f'make -f {rel(harness)} all\n', timeout=360)
# Install staging into a separate directory, never the shared SDK sysroot.
run('staging', f'make -f {rel(harness)} {rel(build)}/.c65-staging STAGING_DIR={rel(staging)}\n')
assert {str(p.relative_to(staging)) for p in staging.rglob('*') if p.is_file()} == {'usr/lib/' + n for n in names}
payload = sums(target / 'usr/share/muos-frontend-libs/payload.sha256')
assert len(payload) == 5 + len(license_names)
for n, digest in payload.items():
    assert sha(target / n.lstrip('/')) == digest, n
assert {str(p.relative_to(target)) for p in target.rglob('*') if p.is_file()} == {
    n.lstrip('/') for n in payload} | {'usr/share/muos-frontend-libs/payload.sha256'}
newlib = target / 'opt/muos/frontend/lib'
abi = {}
for n in names:
    assert sha(staging / 'usr/lib' / n) == sha(newlib / n)
    assert (newlib / n).stat().st_mode & 0o777 == 0o644
    run('elf-' + n, f'/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-readelf -h -l -d -V --dyn-syms --wide {rel(newlib / n)}\n')
    run('old-elf-' + n, f'/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-readelf -h -l -d -V --dyn-syms --wide {rel(oldlib / n)}\n')
    elf = (stage / ('elf-' + n + '.stdout')).read_text()
    oldelf = (stage / ('old-elf-' + n + '.stdout')).read_text()
    for token in ['AArch64', 'DYN (Shared object file)', 'GNU_RELRO', 'BIND_NOW']:
        assert token in elf, (n, token)
    needed = lambda text: sorted(re.findall(r'\(NEEDED\).*\[(.*?)\]', text))
    symbols = lambda text: sorted((s[3], s[4], s[5], s[7]) for line in text.splitlines()
                                 if len(s := line.split()) == 8 and s[0].rstrip(':').isdigit()
                                 and s[3] in {'FUNC', 'OBJECT', 'TLS', 'NOTYPE'} and s[4] in {'GLOBAL', 'WEAK'}
                                 and s[6] != 'UND')
    assert needed(elf) == needed(oldelf), (n, 'NEEDED changed')
    assert symbols(elf) == symbols(oldelf), (n, 'exported ABI changed')
    objects = lambda text: sorted((s[7], s[2], s[4], s[5]) for line in text.splitlines()
                                 if len(s := line.split()) == 8 and s[0].rstrip(':').isdigit()
                                 and s[3] in {'OBJECT', 'TLS'} and s[4] in {'GLOBAL', 'WEAK'} and s[6] != 'UND')
    assert objects(elf) == objects(oldelf), (n, 'exported object size changed')
    assert set(re.findall(r'GLIBC_[0-9.]+', elf)) == set(re.findall(r'GLIBC_[0-9.]+', oldelf)), n
    runpaths = re.findall(r'\((?:RUNPATH|RPATH)\).*\[(.*?)\]', elf)
    assert runpaths == ([] if n == 'libplutosvg.so' else ['$ORIGIN']), (n, runpaths)
    abi[n] = {'sha256': sha(newlib / n), 'foundation_sha256': old_hashes[n],
              'byte_identical': sha(newlib / n) == old_hashes[n],
              'needed': needed(elf), 'exported_symbols_matched': len(symbols(elf)),
              'exported_object_sizes_and_GLIBC_versions_matched': True, 'runpath': runpaths}
root = work / 'rootfs-candidate/composition.w59vz7vo/target'
host = work / 'muxretro-package/build.mdou4mqr/target/opt/muos/frontend/muxretro'
assert sha(host) == '8d519958cdb1ae599e2b2af2f6ee90053bca1a83cce0380baa3a1d7150983f05'
run('loader', f'''sdk=/work/graphics-config/output/host
"$sdk/bin/aarch64-buildroot-linux-gnu-gcc" -O2 -mcpu=cortex-a35 /port/diagnostics/phase4-frontend-libs-load.c -ldl -o {rel(stage)}/load-probe
libs="{rel(newlib)}:{rel(root)}/lib:{rel(root)}/usr/lib"
qemu-aarch64 -cpu cortex-a35 -L / -E LD_BIND_NOW=1 {rel(root)}/lib/ld-linux-aarch64.so.1 --inhibit-cache --library-path "$libs" {rel(stage)}/load-probe {' '.join(rel(newlib / n) for n in names)}
for op in --version --help; do
 qemu-aarch64 -cpu cortex-a35 -L / -E LD_BIND_NOW=1 {rel(root)}/lib/ld-linux-aarch64.so.1 --inhibit-cache --library-path "$libs" {rel(host)} "$op"
done
''')
assert (stage / 'loader.stdout').read_text().count('C65 eager load: ') == 4
assert sdk_config.read_bytes() == (work / 'network-tools/baseline.config').read_bytes()
assert sha(image) == image_hash
for n in names:
    assert sha(oldlib / n) == old_hashes[n]
for name, digest in parents.items():
    proof = repo / 'dist/phase4' / name
    assert sha(proof / 'SHA256SUMS') == digest
    for n, h in sums(proof / 'SHA256SUMS').items():
        assert sha(proof / n) == h, (name, n)
sources = [Path(__file__), *pkg.iterdir(), *patches, makefile, probe_source,
           *(repo / 'port/buildroot-frontend' / n for n in ['Config.in', 'external.desc', 'external.mk'])]
report = {
    'passed': True, 'experiment': 'C65_FRONTEND_LIBRARY_PROVIDER', 'default_off': True,
    'real_Kconfig_rsync_legal_info': True, 'wrong_arch_refused': True,
    'source_only_legal_archive_verified': True, 'source_files': len(expected),
    'upstream_text_files_matching_foundation': len(inputs), 'license_files': len(license_names),
    'source_archive_sha256': sha(archives[0]), 'clean_source_build': True,
    'private_prebuilt_frontend_SDK_used': False, 'four_library_provider_recipe_integrated': True,
    'historical_C60_consumer_switched_to_provider': False, 'headers_SDK_installed': False,
    'target_files': sorted(n.lstrip('/') for n in payload) + ['usr/share/muos-frontend-libs/payload.sha256'],
    'staging_files': ['usr/lib/' + n for n in names], 'libraries': abi,
    'four_eager_dlopen_and_C60_version_help_passed': True,
    'all_libraries_byte_identical_to_foundation': all(v['byte_identical'] for v in abi.values()),
    'native_runtime_qualified': False, 'full_Buildroot_rebuild': False, 'device_contacted': False,
    'new_image_built': False, 'C64_image_preserved_sha256': image_hash, 'SDK_config_unchanged': True,
    'C46_diagnostic_variant_included': False, 'parent_proofs_sha256': parents,
    'source_sha256': {str(p.relative_to(repo)): sha(p) for p in sources}}
(stage / 'analysis.json').write_text(json.dumps(report, indent=2) + '\n')
(area / 'latest-build').write_text(str(stage) + '\n')
print('C65 provider source/legal/build/ABI/eager-load checks passed:', stage)
print('All foundation library bytes identical:', report['all_libraries_byte_identical_to_foundation'])
