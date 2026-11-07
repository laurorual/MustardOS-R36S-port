#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C68 as exact C66 source deltas; never rewrite historical sources."""
from pathlib import Path
import ast, shutil
from phase4_muxretro_provider_session import historical, proof, REPO, NATIVE

context, _, _, _, _, _ = historical()
parent = REPO / 'port/device/rk-r35s-p0/frontend-libs-session'
NATIVE.mkdir(exist_ok=True)
for name in ['app-launch.sh', 'frontend-libs.sh']:
    shutil.copyfile(parent / name, NATIVE / name)
guard = (parent / 'installed-host.sh').read_text()
anchor = '/bin/sh "$capsule/frontend-libs.sh" "$capsule" "$operation"'
assert guard.count(anchor) == 1
host_guard = '''[ -d "$capsule/host" ] && [ ! -L "$capsule/host" ]
[ "$(stat -c '%u:%g:%a' "$capsule/host")" = 0:0:700 ]
[ -f "$capsule/host/muxretro" ] && [ ! -L "$capsule/host/muxretro" ]
[ "$(stat -c '%u:%g:%a:%h' "$capsule/host/muxretro")" = 0:0:700:1 ]
[ "$(sha256sum "$capsule/host/muxretro" | cut -d' ' -f1)" = ''' + context['C67_report']['binary_sha256'] + ''' ]
printf 'C68_RAM_HOST_VALID operation=%s\\n' "$operation"
'''
guard = guard.replace(anchor, host_guard + anchor)
old = 'exec /opt/muos/frontend/muxretro "$capsule/core.so" "$content" --fresh --diagnostic-content --diagnostic-seconds=45 --diagnostic-hotkey-exit'
assert guard.count(old) == 1
guard = guard.replace(old, old.replace('/opt/muos/frontend/muxretro', '"$capsule/host/muxretro"'))
guard = guard.replace('# C63 fixed installed host;', '# C68 fixed RAM host, installed package preserved;')
(NATIVE / 'installed-host.sh').write_text(guard)
(NATIVE / 'stopped-screen.sh').write_text((parent / 'stopped-screen.sh').read_text().replace('C66', 'C68'))
frozen = proof('frontend-libs-session') / 'source'
def derive(name):
    file = REPO / 'port/scripts' / name
    text = file.read_text()
    assert text == (frozen / file.relative_to(REPO)).read_text()
    return text
text = derive('run-phase4-frontend-libs-session.py')
def change(old, new):
    global text
    assert text.count(old) == 1, (old, text.count(old))
    text = text.replace(old, new)
text = text.replace('C66', 'C68').replace('phase4_frontend_libs_session', 'phase4_muxretro_provider_session')
change("REPO / 'port/scripts/prepare-phase4-frontend-libs-session.py'", "REPO / 'port/scripts/prepare-phase4-muxretro-provider-session.py'")
change("files['provider-probe'] = provider_stage / 'load-probe'", """files['host/muxretro'] = context['C67_stage'] / 'target/opt/muos/frontend/muxretro'
expected['host/muxretro'] = context['C67_report']['binary_sha256']
files['provider-probe'] = provider_stage / 'load-probe'""")
change("'provider_analysis_sha256': sha(provider_stage / 'analysis.json'),", """'provider_analysis_sha256': sha(provider_stage / 'analysis.json'),
                   'C66_analysis_sha256': sha(WORK / 'frontend-libs-session/load.o2agwm0q/analysis.json'),
                   'C67_analysis_sha256': sha(context['C67_stage'] / 'analysis.json'),""")
change("'C68_MAP_GAME_PROVIDER4_INSTALLED_HOST'", "'C68_MAP_GAME_PROVIDER4_RAM_HOST'")
change("'C68_PROVIDER_VALID files=7 operation=launch'", "'C66_PROVIDER_VALID files=7 operation=launch'")
change("'host_binary_sha256': prior['host_binary_sha256'], 'installed_host_used': True,", """'host_binary_sha256': context['C67_report']['binary_sha256'], 'installed_host_used': False,
          'exact_C66_boot_retained': True, 'C66_analysis_sha256': observation['C66_analysis_sha256'],
          'C67_analysis_sha256': observation['C67_analysis_sha256'],""")
change("'host_ELF_transferred': False", "'host_ELF_transferred': True")
change("'native_eager_provider_and_installed_host_CLI_passed'", "'native_eager_provider_and_RAM_host_CLI_passed'")
ast.parse(text)
(REPO / 'port/scripts/run-phase4-muxretro-provider-session.py').write_text(text)
text = derive('analyze-phase4-frontend-libs-session.py')
text = text.replace('C66', 'C68').replace('phase4_frontend_libs_session', 'phase4_muxretro_provider_session')
change("'native_eager_provider_and_installed_host_CLI_passed'", "'native_eager_provider_and_RAM_host_CLI_passed'")
change("assert r['installed_host_used'] and not r['host_ELF_transferred'] and not r['store_ELF_transferred']",
       "assert not r['installed_host_used'] and r['host_ELF_transferred'] and not r['store_ELF_transferred']\nassert r['exact_C66_boot_retained']")
ast.parse(text)
(REPO / 'port/scripts/analyze-phase4-muxretro-provider-session.py').write_text(text)
text = derive('finish-phase4-frontend-libs-session.py')
text = text.replace('C66', 'C68').replace('phase4_frontend_libs_session', 'phase4_muxretro_provider_session')
# C66-specific names in the immutable audit's variable labels are descriptive only.
text = text.replace("'frontend-libs', 'muxretro-image']", "'frontend-libs', 'muxretro-image', 'frontend-libs-session', 'muxretro-provider']")
change("assert r['passed'] and r['RAM_removed'] and r['cleanup_passed']", """assert r['passed'] and r['RAM_removed'] and r['cleanup_passed']
assert not r['installed_host_used'] and r['host_ELF_transferred'] and r['exact_C66_boot_retained']""")
ast.parse(text)
(REPO / 'port/scripts/finish-phase4-muxretro-provider-session.py').write_text(text)
print('C68 fixed RAM host runner/guards/analyzer/audit rendered; historical sources unchanged')
