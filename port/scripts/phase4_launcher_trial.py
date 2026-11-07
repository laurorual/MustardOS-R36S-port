# SPDX-License-Identifier: MIT
"""Bind a C25 boot trial to the installed, calibrated C27 public payload."""
from pathlib import Path
import json
from phase4_candidate import sha, inventory, validate


def irq_contract(repo, area, installation, plan):
    prime = plan['experiment'] == 'C36_PCM_PRIME'
    digest=sha(installation/'plan.json')
    installed=json.loads((installation/'install-analysis.json').read_text())
    assert installed['passed'] and installed['root_ro'] and installed['private_state_preserved']
    assert installed['foundation_hash_count']==97 and installed['public_files_written']==2
    assert installed['boot_sequence']==plan['boot_sequence']
    manifest=json.loads((installation/'manifest.json').read_text())
    assert manifest['prepared'] and manifest['plan_sha256']==digest
    assert manifest['deployment_sha256']==sha(installation/'deployment.tar')
    checks=Path((area/'latest-update-checks').read_text().strip())
    assert checks.resolve().is_relative_to(area.resolve())
    tx=json.loads((checks/'analysis.json').read_text());assert tx['passed'] and tx['plan_sha256']==digest
    for pins in [plan['source_sha256'],manifest['sources'],tx['sources']]:
        for name,expected in pins.items():
            assert name.startswith('port/') and '..' not in Path(name).parts
            assert sha(repo/name)==expected,name
    candidate=Path(plan['candidate_stage']);previous=Path(plan['previous_update_stage'])
    for path in [candidate,previous]:assert path.resolve().is_relative_to(area.resolve())
    assert sha(candidate/'analysis.json')==plan['candidate_analysis_sha256']
    before=json.loads((previous/'plan.json').read_text());assert before['experiment'] in (['C33_ALSA_RW'] if prime else ['C27_VOLUME_CALIBRATION','C30_ALSA_IRQ'])
    assert json.loads((previous/'install-analysis.json').read_text())['passed']
    root=candidate/'target';baseline=Path(before['candidate_stage'])/'target'
    assert baseline.resolve().is_relative_to(area.resolve())
    old,new=inventory(baseline),inventory(root)
    changed={n for n in set(old)|set(new) if old.get(n)!=new.get(n)}
    assert changed=={('etc/init.d/S95muos-core' if prime else 'opt/muos/device/control/wireplumber.conf'),'usr/libexec/muos-session/prerequisites.sha256'}
    report=validate(root);assert report['ALSA_irq_scheduling'] and report['foundation_files']==97
    names=['usr/libexec/muos-session/prerequisites.sha256','usr/libexec/muos-session/payload.sha256',
           'usr/libexec/muos-session/profile-source.sha256','usr/libexec/muos-c25/payload.sha256',
           'etc/inittab','etc/init.d/S95muos-core','usr/share/muos-r35s-profile/profile.json',
           'usr/share/muos-r35s-profile/speaker-calibration.json','opt/muos/device/control/wireplumber.conf']
    pins={}
    for name in names:
        f=root/name;assert f.is_file() and not f.is_symlink();pins['/'+name]=sha(f)
    rw=plan['experiment'] in ['C33_ALSA_RW','C36_PCM_PRIME']
    if rw:assert '      api.alsa.disable-mmap = true' in (root/'opt/muos/device/control/wireplumber.conf').read_text().splitlines()
    if prime:
        hook=(root/'etc/init.d/S95muos-core').read_text()
        assert 'if ! audio_prime_pcm;' in hook and '--period-size=1024 --buffer-size=4096 -d 1 /dev/zero' in hook
        assert hook.index('if ! audio_prime_pcm;') < hook.index('if ! "$audio_service" start;')
    result={'schema':1,'experiment':'C37_PRIMED_LAUNCHER_BOOT' if prime else ('C34_RW_LAUNCHER_BOOT' if rw else 'C31_IRQ_LAUNCHER_BOOT'),'installation_stage':str(installation),
            'plan_sha256':digest,'candidate_analysis_sha256':sha(candidate/'analysis.json'),
            'previous_C27_plan_sha256':sha(previous/'plan.json'),'only_two_public_changes':True,
            'transaction_checks_sha256':sha(checks/'analysis.json'),'native_file_sha256':pins,
            'codec_gain':215,'quantum':1024,'IRQ_scheduling':True,'RW_access':rw,'foundation_hashes':97,
            'full_factory_image_boot_claimed':False}
    if prime: result['direct_PCM_priming']=True
    return result


def calibrated_contract(repo, area, installation, plan):
    repo, area, installation = map(Path, (repo, area, installation))
    assert installation.resolve().is_relative_to(area.resolve())
    if plan['experiment'] in ['C30_ALSA_IRQ','C33_ALSA_RW','C36_PCM_PRIME']:
        return irq_contract(repo,area,installation,plan)
    assert plan['experiment'] == 'C27_VOLUME_CALIBRATION'
    digest = sha(installation / 'plan.json')
    installed = json.loads((installation / 'install-analysis.json').read_text())
    assert installed['passed'] and installed['root_ro'] and installed['private_state_preserved']
    assert installed['boot_sequence'] == plan['boot_sequence']
    assert installed['foundation_hash_count'] == 96 and installed['public_files_written'] == 8
    manifest = json.loads((installation / 'manifest.json').read_text())
    assert manifest['prepared'] and manifest['plan_sha256'] == digest
    assert manifest['deployment_sha256'] == sha(installation / 'deployment.tar')
    checks = Path((area / 'latest-update-checks').read_text().strip())
    assert checks.resolve().is_relative_to(area.resolve())
    tx = json.loads((checks / 'analysis.json').read_text())
    assert tx['passed'] and tx['plan_sha256'] == digest
    composition = Path((area / 'latest-composition').read_text().strip())
    assert composition.resolve().is_relative_to(area.resolve())
    image = json.loads((composition / 'analysis.json').read_text())
    equivalent = json.loads((composition / 'native-C26-equivalence.json').read_text())
    assert image['passed'] and image['experiment'] == 'MUOS-R35S-CANDIDATE-P4-C27'
    assert image['selected_native_profile_plan_sha256'] == digest
    assert image['C25_and_C26_integrated'] and not image['automatic_session']
    assert equivalent['passed'] and equivalent['native_plan_sha256'] == digest
    for name in ['calibrated_profile', 'foundation96_identical_to_installed_target',
                 'payload15_identical', 'calibration_certificate_identical']:
        assert equivalent[name], name
    assert equivalent['codec_gain'] == 215
    # Check each provenance set separately so conflicting pins cannot be hidden
    # by dict merging. These inputs are public sources, never private state.
    for pins in [plan['source_sha256'], manifest['sources'], tx['sources'], image['sources']]:
        for name, expected in pins.items():
            assert name.startswith('port/') and '..' not in Path(name).parts
            assert sha(repo / name) == expected, name
    candidate = Path(plan['candidate_stage'])
    assert candidate.resolve().is_relative_to(area.resolve())
    native = candidate / 'target'
    factory = composition / 'target'
    names = ['usr/libexec/muos-session/prerequisites.sha256',
             'usr/libexec/muos-session/payload.sha256',
             'usr/libexec/muos-session/profile-source.sha256',
             'usr/libexec/muos-c25/payload.sha256', 'etc/inittab',
             'etc/init.d/S95muos-core', 'usr/share/muos-r35s-profile/profile.json',
             'usr/share/muos-r35s-profile/speaker-calibration.json']
    pins = {}
    for name in names:
        left, right = native / name, factory / name
        assert left.is_file() and not left.is_symlink(), name
        assert right.is_file() and not right.is_symlink(), name
        assert left.read_bytes() == right.read_bytes(), name
        pins['/' + name] = sha(left)
    foundation = native / names[0]
    assert len(foundation.read_text().splitlines()) == 96
    assert sha(foundation) == sha(composition / 'foundation.sha256')
    profile = json.loads((native / names[-2]).read_text())
    cert = json.loads((native / names[-1]).read_text())
    assert profile['name'] == 'rk-r35s-p0-private-bringup-v3'
    assert profile['audio']['codec_gain'] == 215 and profile['audio']['pipewire_quantum'] == 1024
    assert profile['speaker_calibration_sha256'] == pins['/' + names[-1]]
    assert cert['board'] == 'rk-r35s-p0' and cert['codec_gain'] == 215
    assert cert['pipewire_quantum'] == 1024 and cert['software_max'] == 100
    assert cert['maximum_clean_and_adequate_user_confirmed'] is True
    return {'schema': 1, 'experiment': 'C28_CALIBRATED_LAUNCHER_BOOT',
            'installation_stage': str(installation), 'plan_sha256': digest,
            'composition_stage': str(composition),
            'composition_analysis_sha256': sha(composition / 'analysis.json'),
            'equivalence_sha256': sha(composition / 'native-C26-equivalence.json'),
            'transaction_checks_sha256': sha(checks / 'analysis.json'),
            'native_file_sha256': pins, 'codec_gain': 215, 'quantum': 1024}
