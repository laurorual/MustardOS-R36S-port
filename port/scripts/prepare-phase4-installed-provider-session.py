#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C73 derive a final bounded load-only session for installed C72 bytes."""
from pathlib import Path
import ast
from phase4_installed_provider_session import REPO, WORK, NATIVE, installed, proof

_, _, plan = installed()
NATIVE.mkdir(exist_ok=True)
parent = REPO / 'port/device/rk-r35s-p0/muxretro-provider-session'
for name in ['app-launch.sh', 'frontend-libs.sh']:
    text = (parent / name).read_text()
    text = text.replace('$capsule/provider-lib:/opt/muos/frontend/lib', '/opt/muos/frontend/lib')
    if name == 'frontend-libs.sh': text = text.replace('C66_PROVIDER_VALID', 'C73_PROVIDER_VALID')
    (NATIVE / name).write_text(text)
text = (parent / 'installed-host.sh').read_text()
start = text.index("done <<'C63_PINNED_PAYLOAD'\n")
end = text.index('\nC63_PINNED_PAYLOAD\n', start) + len('\nC63_PINNED_PAYLOAD\n')
rows = ''.join(r['sha256'] + ' ' + f'{r["mode"]:o}' + ' ' + n + '\n' for n, r in sorted(plan['after'].items()))
text = text[:start] + "done <<'C73_PINNED_PAYLOAD'\n" + rows + 'C73_PINNED_PAYLOAD\n' + text[end:]
start = text.index('[ -d "$capsule/host" ]')
end = text.index('/bin/sh "$capsule/frontend-libs.sh"', start)
text = text[:start] + text[end:]
text = text.replace('for name in muxretro save-store;', 'for name in muxretro save-store host;')
text = text.replace('exec "$capsule/host/muxretro"', 'exec /opt/muos/frontend/muxretro')
text = text.replace('C63_INSTALLED_HOST_VALID files=13', 'C73_INSTALLED_HOST_VALID files=31')
text = text.replace('# All thirteen hashes, including the manifest itself, are pinned from C62.', '# All 31 installed leaves are pinned from C72, including package manifests.')
(NATIVE / 'installed-host.sh').write_text(text)
(NATIVE / 'stopped-screen.sh').write_text((parent / 'stopped-screen.sh').read_text().replace('C68', 'C73'))
frozen = proof('muxretro-provider-session') / 'source/port/scripts/run-phase4-muxretro-provider-session.py'
source = REPO / 'port/scripts/run-phase4-muxretro-provider-session.py'
assert source.read_bytes() == frozen.read_bytes()
text = source.read_text().replace('phase4_muxretro_provider_session', 'phase4_installed_provider_session').replace('C68', 'C73')
def change(old, new):
    global text
    assert text.count(old) == 1, (old, text.count(old))
    text = text.replace(old, new)
change("REPO / 'port/scripts/prepare-phase4-muxretro-provider-session.py'", "REPO / 'port/scripts/prepare-phase4-installed-provider-session.py'")
change("REPO / 'port/scripts/phase4_installed_provider_session.py'", "REPO / 'port/scripts/phase4_installed_provider_session.py'")
change("'C67_analysis_sha256': sha(context['C67_stage'] / 'analysis.json'),", "'C67_analysis_sha256': sha(context['C67_stage'] / 'analysis.json'),\n                   'C72_analysis_sha256': sha(WORK / 'provider-upgrade-native/install.otw0lflu/install-analysis.json'),")
change("files['host/muxretro'] = context['C67_stage'] / 'target/opt/muos/frontend/muxretro'\nexpected['host/muxretro'] = context['C67_report']['binary_sha256']\n", '')
change("'C73_MAP_GAME_PROVIDER4_RAM_HOST'", "'C73_MAP_GAME_PROVIDER4_INSTALLED_HOST'")
change("'C66_PROVIDER_VALID files=7 operation=launch'", "'C73_PROVIDER_VALID files=7 operation=launch'")
change("'installed_host_used': False", "'installed_host_used': True")
change("'host_ELF_transferred': True", "'host_ELF_transferred': False")
change("'provider_ELFs_RAM_only': True", "'provider_ELFs_RAM_only': False, 'game_uses_installed_provider4': True")
change("'native_eager_provider_and_RAM_host_CLI_passed'", "'native_eager_provider_and_installed_host_CLI_passed'")
change("'C67_analysis_sha256': observation['C67_analysis_sha256'],", "'C67_analysis_sha256': observation['C67_analysis_sha256'],\n          'C72_analysis_sha256': observation['C72_analysis_sha256'],")
ast.parse(text)
(REPO / 'port/scripts/run-phase4-installed-provider-session.py').write_text(text)
print('C73 exact installed31 guard and bounded load-only runner prepared; historical sources unchanged')
