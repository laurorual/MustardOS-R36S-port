# SPDX-License-Identifier: MIT
"""C73 exact C72 installed model; preserve every historical RAM-session guard."""
from pathlib import Path
import ast, json
import phase4_muxretro_provider_session as base
from phase4_candidate import sha, sums

REPO, WORK, NAMES, proof = base.REPO, base.WORK, base.NAMES, base.proof
AREA = WORK / 'installed-provider-session'
NATIVE = REPO / 'port/device/rk-r35s-p0/installed-provider-session'
C72 = WORK / 'provider-upgrade-native/install.otw0lflu'

def installed():
    frozen = proof('provider-upgrade-native')
    r = json.loads((C72 / 'install-analysis.json').read_text())
    f = json.loads((C72 / 'final-audit.json').read_text())
    assert r == json.loads((frozen / 'analysis.json').read_text()) and r['passed']
    assert f == json.loads((frozen / 'final-audit.json').read_text()) and f['passed'] and f['RAM_removed']
    assert f['install_analysis_sha256'] == sha(C72 / 'install-analysis.json')
    binding = json.loads((C72 / 'binding.json').read_text())
    assert r['binding_sha256'] == sha(C72 / 'binding.json')
    assert sha(C72 / 'plan.json') == r['plan_sha256']
    for report in [r, f]:
        for n, h in report['source_sha256'].items(): assert sha(REPO / n) == h, n
    return r, binding, json.loads((C72 / 'plan.json').read_text())

def historical():
    r, binding, plan = installed()
    context, prior_stage, prior, provider_stage, provider, online = base.historical()
    assert binding['kernel_boot_id'] == context['C66_report']['kernel_boot_id']
    assert binding['boot_sequence'] == context['C66_report']['boot_sequence']
    assert plan['after']['opt/muos/frontend/muxretro']['sha256'] == context['C67_report']['binary_sha256']
    context.update(C72_report=r, C72_binding=binding, C72_plan=plan)
    return context, prior_stage, prior, provider_stage, provider, online

def current_common(common, old_boot, new_boot):
    _, b, plan = installed()
    assert new_boot == b['boot_sequence']
    tree = ast.parse((REPO / 'port/scripts/run-phase4-provider-upgrade.py').read_text())
    nodes = [n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'base' for t in n.targets)]
    assert len(nodes) == 1
    code = ast.literal_eval(nodes[0].value)
    code += f'[ "$(cat "$c25_store/boot-seq")" = {new_boot} ]\n'
    code += f'[ "$(cat /proc/sys/kernel/random/boot_id)" = {b["kernel_boot_id"]} ]\n'
    for name, row in sorted(plan['after'].items()):
        code += f'[ ! -L /{name} ];[ "$(stat -c \'%u:%g:%a:%h\' /{name})" = 0:0:{row["mode"]:o}:1 ]\n'
        code += f"printf '%s  %s\\n' {row['sha256']} /{name} | sha256sum -c - >/dev/null\n"
    for name in plan['old_directories']:
        code += f'[ ! -e /{name} ];[ ! -L /{name} ]\n'
    for name, digest in sums(C72 / 'payload/preserved.sha256').items():
        code += f"printf '%s  %s\\n' {digest} /{name} | sha256sum -c - >/dev/null\n"
    return code

def bind(prior, provider, observation, boot, boot_id):
    _, b, _ = installed()
    assert observation['experiment'] == 'C73_OBSERVED_BOOT'
    assert observation['C72_analysis_sha256'] == sha(C72 / 'install-analysis.json')
    assert boot == b['boot_sequence'] and boot_id == b['kernel_boot_id']
    return base.bind(prior, provider, {**observation, 'experiment': 'C68_OBSERVED_BOOT'}, boot, boot_id)

def watch_script(directory):
    text = base.watch_script(directory)
    assert text.count('= ' + directory + '/host/muxretro ]') == 1
    text = text.replace('= ' + directory + '/host/muxretro ]', '= /opt/muos/frontend/muxretro ]')
    for name in NAMES:
        old = "grep -Fq '" + directory + '/provider-lib/' + name + "' /proc/$p/maps"
        assert text.count(old) == 1
        text = text.replace(old, "grep -Fq '/opt/muos/frontend/lib/" + name + "' /proc/$p/maps")
    return text.replace('C68_MAP_', 'C73_MAP_').replace('PROVIDER4_RAM_HOST', 'PROVIDER4_INSTALLED_HOST')

def render_online(online):
    text = base.render_online(online)
    assert text.count(' {directory}/host\\n') == 1
    text = text.replace(' {directory}/host\\n', '\\n')
    assert text.count('{directory}/host/muxretro --') == 2
    text = text.replace('{directory}/host/muxretro --', '/opt/muos/frontend/muxretro --')
    return text
