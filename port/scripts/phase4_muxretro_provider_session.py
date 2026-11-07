# SPDX-License-Identifier: MIT
"""C68 pinned RAM host; preserve C66 lifecycle and exact observed boot."""
from pathlib import Path
import ast, json
from phase4_candidate import sha
import phase4_frontend_libs_session as base

REPO, WORK, NAMES, proof = base.REPO, base.WORK, base.NAMES, base.proof
AREA = WORK / 'muxretro-provider-session'
NATIVE = REPO / 'port/device/rk-r35s-p0/muxretro-provider-session'
C66 = WORK / 'frontend-libs-session/load.o2agwm0q'
C67 = WORK / 'muxretro-provider/build.f9a1ac69'

def historical():
    frozen = proof('frontend-libs-session')
    r66 = json.loads((C66 / 'analysis.json').read_text())
    clean = {k: ('private' if k in {'private_identity', 'ROM_sha256', 'kernel_boot_id'} else v) for k, v in r66.items()}
    assert clean == json.loads((frozen / 'load/analysis.json').read_text())
    for relative, public in [('physical-observation.json', 'physical/analysis.json'), ('technical-analysis.json', 'technical/analysis.json')]:
        assert json.loads((C66 / relative).read_text()) == json.loads((frozen / public).read_text())
    physical = json.loads((C66 / 'physical-observation.json').read_text())
    assert physical['session_analysis_sha256'] == sha(C66 / 'analysis.json')
    for key in ['image_and_navigation_confirmed', 'sound_clean_and_audible_confirmed',
                'restore_to_saved_position_confirmed', 'launcher_return_confirmed']:
        assert physical[key] is True
    for n, h in r66['source_sha256'].items():
        assert sha(REPO / n) == h, n
    c67_proof = proof('muxretro-provider')
    r67 = json.loads((C67 / 'analysis.json').read_text())
    assert r67 == json.loads((c67_proof / 'analysis.json').read_text()) and r67['passed']
    assert not r67['private_frontend_SDK_required'] and not r67['C66_native_evidence_reused']
    assert r67['runtime_provider'] == r66['libraries']
    assert r67['parent_proofs_sha256']['frontend-libs-session'] == sha(frozen / 'SHA256SUMS')
    for n, h in r67['source_sha256'].items():
        assert sha(REPO / n) == h, n
    for n, h in base.sums(C67 / 'target/usr/share/muos-muxretro-provider/payload.sha256').items():
        assert sha(C67 / 'target' / n.lstrip('/')) == h, n
    assert sha(C67 / 'target/opt/muos/frontend/muxretro') == r67['binary_sha256'] != r66['host_binary_sha256']
    context, prior_stage, prior, provider_stage, provider, online = base.historical()
    assert r66['private_identity'] == prior['private_identity'] == context['identity']
    assert r66['ROM_sha256'] == prior['ROM_sha256'] == context['nr']['ROM_sha256']
    assert r66['libraries'] == {n: v['sha256'] for n, v in provider['libraries'].items()}
    context.update(C66_report=r66, C67_report=r67, C67_stage=C67)
    return context, prior_stage, prior, provider_stage, provider, online

def current_common(common, old_boot, new_boot):
    r66 = json.loads((C66 / 'analysis.json').read_text())
    assert type(new_boot) is int and new_boot == r66['boot_sequence']
    return base.current_common(common, old_boot, new_boot)

def bind(prior, provider, observation, boot, boot_id):
    assert observation['experiment'] == 'C68_OBSERVED_BOOT'
    r66 = json.loads((C66 / 'analysis.json').read_text())
    assert type(boot) is int and boot == r66['boot_sequence'] and boot_id == r66['kernel_boot_id']
    assert observation['C66_analysis_sha256'] == sha(C66 / 'analysis.json')
    assert observation['C67_analysis_sha256'] == sha(C67 / 'analysis.json')
    copy = {**observation, 'experiment': 'C66_OBSERVED_BOOT'}
    return base.bind(prior, provider, copy, boot, boot_id)

def watch_script(directory):
    text = base.watch_script(directory)
    assert text.count('= /opt/muos/frontend/muxretro ]') == 1
    text = text.replace('= /opt/muos/frontend/muxretro ]', '= ' + directory + '/host/muxretro ]')
    return text.replace('C66_MAP_', 'C68_MAP_').replace('PROVIDER4_INSTALLED_HOST', 'PROVIDER4_RAM_HOST')

def render_online(online):
    text = base.render_online(online)
    assert text.count('{directory}/provider-lib\\n') == 1
    text = text.replace('{directory}/provider-lib\\n', '{directory}/provider-lib {directory}/host\\n')
    assert text.count('/opt/muos/frontend/muxretro --') == 2
    text = text.replace('/opt/muos/frontend/muxretro --', '{directory}/host/muxretro --')
    ast.parse(text)
    return text
