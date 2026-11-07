#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C77 derive new sources without modifying any frozen historical guard."""
from pathlib import Path
import ast
from phase4_installed_core_session import REPO, WORK, NATIVE, CORE, STATE, installed, historical, proof

_, plan = installed()
context, *_ = historical()
NATIVE.mkdir(exist_ok=True)
parent = REPO / 'port/device/rk-r35s-p0/installed-provider-session'

def once(text, old, new):
    assert text.count(old) == 1, (old, text.count(old))
    return text.replace(old, new)

text = (parent / 'installed-host.sh').read_text()
text = text.replace('muxretro save-store host;', 'muxretro save-store host core.so;')
text = once(text, 'C73_PINNED_PAYLOAD\n# Pinning', ''.join(r['sha256'] + ' ' + f'{r["mode"]:o}' + ' ' + r['path'] + '\n' for r in plan['files']) + 'C73_PINNED_PAYLOAD\n# Pinning')
text = text.replace('"$capsule/core.so"', '"' + CORE + '"')
text = text.replace('C73_INSTALLED_HOST_VALID files=31', 'C77_INSTALLED_HOST_CORE_VALID files=40')
text = text.replace('# C68 fixed RAM host, installed package preserved;', '# C77 fixed installed host and core;')
text = text.replace('# All 31 installed leaves are pinned from C72, including package manifests.', '# Pin all 40 C72/C76 leaves, including manifests and core license review.')
(NATIVE / 'installed-host.sh').write_text(text)
text = (parent / 'app-launch.sh').read_text()
text = text.replace('$2!="core.so"', '$2!="' + CORE + '"')
text = text.replace('for file in core.so private.gb;', 'for file in private.gb;')
text = once(text, '(cd "$capsule" && sha256sum -c gb-assets.sha256)', '''[ ! -e "$capsule/core.so" ] && [ ! -L "$capsule/core.so" ] || exit 64
# The fixed dispatcher verifies all C76 leaves before this manifest is consumed.
/bin/sh "$capsule/installed-host.sh" "$capsule" check
(cd "$capsule" && sha256sum -c gb-assets.sha256)''')
(NATIVE / 'app-launch.sh').write_text(text)
for name in ['frontend-libs.sh', 'stopped-screen.sh']:
    (NATIVE / name).write_text((parent / name).read_text().replace('C73', 'C77'))
# Export the existing immutable snapshot into the native installed-core namespace.
# Its content/core identity and the on-card store are unchanged.
for name, source in [('select.sh', context['files']['select.sh']),
                     ('store-base.sh', context['files']['store-base.sh']),
                     ('installed-store.sh', context['files']['installed-store.sh'])]:
    text = source.read_text()
    assert '/state/core.so' in text
    (NATIVE / name).write_text(text.replace('/state/core.so', '/state/gambatte'))

text = (REPO / 'port/scripts/run-phase4-installed-provider-session.py').read_text()
assert text == (proof('installed-provider-session') / 'source/port/scripts/run-phase4-installed-provider-session.py').read_text()
text = text.replace('phase4_installed_provider_session', 'phase4_installed_core_session').replace('C73', 'C77')
text = text.replace('prepare-phase4-installed-provider-session.py', 'prepare-phase4-installed-core-session.py')
text = once(text, "'C72_analysis_sha256': sha(WORK / 'provider-upgrade-native/install.otw0lflu/install-analysis.json'),", "'C72_analysis_sha256': sha(WORK / 'provider-upgrade-native/install.otw0lflu/install-analysis.json'),\n                   'C76_analysis_sha256': sha(WORK / 'gambatte-install/install.ucdyhb4b/install-analysis.json'),")
text = once(text, "for n in ['app-launch.sh', 'installed-host.sh', 'frontend-libs.sh']:", "for n in ['core.so', 'core-check']:\n    del files[n]; del expected[n]\nfor n in ['app-launch.sh', 'installed-host.sh', 'frontend-libs.sh', 'select.sh', 'store-base.sh', 'installed-store.sh']:")
text = once(text, "'exact_C66_boot_retained': True", "'exact_C66_boot_retained': False")
text = once(text, "'C72_analysis_sha256': observation['C72_analysis_sha256'],", "'C72_analysis_sha256': observation['C72_analysis_sha256'],\n          'C76_analysis_sha256': observation['C76_analysis_sha256'],\n          'core_ELF_transferred': False, 'installed_core_used': True,\n          'core_sha256': context['nr']['core_sha256'],\n          'state_namespace': 'gambatte',")
text = once(text, "'C77_FRONTEND_PROVIDER_RAM'", "'C77_INSTALLED_CORE_SESSION'")
text = once(text, "assert 'muxretro' not in files and 'save-store' not in files", "assert all(n not in files for n in ['muxretro', 'save-store', 'core.so', 'core-check'])")
text = once(text, "passed = passed and len(exits) == 1", "passed = passed and len(exits) == 1\npassed = passed and game.count('C77_INSTALLED_HOST_CORE_VALID files=40 operation=launch') == 1\npassed = passed and \"Loaded state from '/run/muos/storage/pickles/state/gambatte/GB/private/\" in game")
ast.parse(text)
(REPO / 'port/scripts/run-phase4-installed-core-session.py').write_text(text)
print('C77 installed core caller40 and RAM-only state namespace adapter prepared')
