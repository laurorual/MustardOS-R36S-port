# SPDX-License-Identifier: MIT
"""C77: installed C72 host/providers and C76 core, with fresh boot binding."""
from pathlib import Path
import ast, json
import phase4_installed_provider_session as parent
import phase4_frontend_libs_session as binding_base
import phase4_gambatte_install as package
from phase4_candidate import sha

REPO, WORK, NAMES, proof = parent.REPO, parent.WORK, parent.NAMES, parent.proof
AREA = WORK / 'installed-core-session'
NATIVE = REPO / 'port/device/rk-r35s-p0/installed-core-session'
C76 = WORK / 'gambatte-install/install.ucdyhb4b'
CORE = '/opt/muos/share/core/gambatte_libretro.so'
STATE = '/run/muos/storage/pickles/state/gambatte/GB/private'

def installed():
    frozen = proof('gambatte-installed')
    report = json.loads((C76 / 'install-analysis.json').read_text())
    assert report == json.loads((frozen / 'install-analysis.json').read_text())
    assert report['passed'] and report['RAM_removed'] and report['root_read_only']
    assert report['plan_sha256'] == sha(C76 / 'plan.json')
    for n, h in report['source_sha256'].items(): assert sha(REPO / n) == h, n
    plan = json.loads((C76 / 'plan.json').read_text())
    assert len(plan['files']) == 9
    return report, plan

def historical():
    report, plan = installed()
    result = parent.historical()
    context = result[0]
    assert context['nr']['core_sha256'] == report['core_sha256']
    context.update(C76_report=report, C76_plan=plan)
    return result

def current_common(common, old_boot, new_boot):
    report, plan = installed()
    assert type(new_boot) is int and report['boot_sequence'] <= new_boot <= 999999
    code = package.context()[-1]
    code += f'[ "$(cat "$c25_store/boot-seq")" = {new_boot} ]\n'
    for row in plan['files']:
        n = row['path']
        code += f'[ -f /{n} ];[ ! -L /{n} ];[ "$(stat -c \'%u:%g:%a:%h\' /{n})" = 0:0:{row["mode"]:o}:1 ]\n'
        code += f"printf '%s  %s\\n' {row['sha256']} /{n} | sha256sum -c - >/dev/null\n"
    for n in plan['absent_directories']:
        code += f'[ -d /{n} ];[ ! -L /{n} ];[ "$(stat -c \'%u:%g:%a\' /{n})" = 0:0:755 ]\n'
    return code

def bind(prior, provider, observation, boot, boot_id):
    report, _ = installed()
    assert observation['experiment'] == 'C77_OBSERVED_BOOT'
    assert observation['C76_analysis_sha256'] == sha(C76 / 'install-analysis.json')
    assert observation['C72_analysis_sha256'] == sha(parent.C72 / 'install-analysis.json')
    assert observation['C66_analysis_sha256'] == sha(WORK / 'frontend-libs-session/load.o2agwm0q/analysis.json')
    assert observation['C67_analysis_sha256'] == sha(WORK / 'muxretro-provider/build.f9a1ac69/analysis.json')
    assert type(boot) is int and report['boot_sequence'] <= boot <= 999999
    if boot == report['boot_sequence']:
        assert boot_id == json.loads((C76 / 'manifest.json').read_text())['kernel_boot_id']
    return binding_base.bind(prior, provider, {**observation, 'experiment': 'C66_OBSERVED_BOOT'}, boot, boot_id)

def watch_script(directory):
    text = parent.watch_script(directory).replace('C73_MAP_', 'C77_MAP_')
    anchor = ' if [ "$ok" = 1 ]'
    assert text.count(anchor) == 1
    return text.replace(anchor, f" grep -Fq '{CORE}' /proc/$p/maps || ok=0\n" + anchor)

def render_online(online):
    text = parent.render_online(online)
    old = "{nr['core_sha256']} core.so"
    assert text.count(old) == 1
    text = text.replace(old, "{nr['core_sha256']} " + CORE)
    ast.parse(text)
    return text
