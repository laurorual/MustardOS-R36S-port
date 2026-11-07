# SPDX-License-Identifier: MIT
"""C104: explicitly observe the boot after C103; retain the installed layout.

Reuses the frozen C77 session without editing any C97/C102/C103 source.
Only stable network/key identity metadata is checked; seed files are not read.
"""
from pathlib import Path
import ast,importlib,json,re
import phase4_native_layout_session as native
from phase4_root_migration import require
from phase4_candidate import sha

REPO,WORK,NATIVE,NAMES=native.REPO,native.WORK,native.NATIVE,native.NAMES
AREA=WORK/'reboot-layout-session'
legacy=native.legacy
proof,watch_script,render_online=legacy.proof,legacy.watch_script,legacy.render_online

def qualified():
    native.qualified()
    public=json.loads((proof('native-layout-session')/'analysis.json').read_text())
    stage=Path((native.AREA/'latest-load').read_text().strip())
    require(stage.resolve().is_relative_to(native.AREA),'Known completed C103 session')
    r=json.loads((stage/'analysis.json').read_text())
    require(public['schema']==103 and public['passed'] is True and
        public['physical_image_input_audio_restore_and_return_confirmed'] is True and
        public['original_worker_used'] is True and public['C99_etc_or_mnt_directory_views_used'] is False and
        public['installed_layout_restored'] is True and r['C103_native_layout_runtime_validation'] is True and
        type(r['boot_sequence']) is int and r['boot_sequence']==public['boot_sequence'],
        'Qualified physical C103 installed-layout session required')
    for key in ['passed','RAM_removed','cleanup_passed','root_ro','global_mountinfo_unchanged',
        'store_byte_identical_to_C63','process_maps_confirmed']:
        require(r[key] is True,'Incomplete prior session')
    require(r['new_save_requested'] is False and r['agent_requested_reboot'] is False,'Unmodified prior data/boot')
    for name in ['physical-observation.json','technical-analysis.json']:
        d=json.loads((stage/name).read_text())
        require(d['passed'] is True and d['session_analysis_sha256']==sha(stage/'analysis.json'),
            'C103 physical/technical receipt binding')
    physical=json.loads((stage/'physical-observation.json').read_text())
    for key in ['image_and_navigation_confirmed','sound_clean_and_audible_confirmed',
        'restore_to_saved_position_confirmed','launcher_return_confirmed']:
        require(physical[key] is True,'Prior physical confirmation incomplete')
    final=json.loads((stage/'final-audit.json').read_text());require(final['passed'] is True,'C103 closure required')
    for n,h in final['recorded_receipts_sha256'].items():require(sha(stage/n)==h,'C103 receipt changed')
    for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'C103 source changed')
    return stage,r

def transition(previous,new_boot,new_uuid):
    require(type(new_boot) is int and type(previous['boot_sequence']) is int and
        2<=new_boot<=9998 and new_boot==previous['boot_sequence']+1,'Observe exactly the planned next boot')
    require(type(new_uuid) is str and re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}',new_uuid) and
        new_uuid!=previous['kernel_boot_id'],'Fresh, well-formed kernel boot identity required')

def stable_identity_guard():
    # native.qualified() already checked this C94 package via C97 lineage.
    area=WORK/'p2-initial';package=Path((area/'latest-package').read_text().strip())
    require(package.resolve().is_relative_to(area),'Known C94 package')
    bundle=package/'bundle';manifest=json.loads((bundle/'package.json').read_text())
    require(sha(bundle/'context.json')==manifest['files']['context.json'],'Stable metadata package binding')
    ctx=json.loads((bundle/'context.json').read_text())
    names={'etc/muos-network-authorized_key','var/lib/muos-network/dropbear_ed25519_host_key',
        'var/lib/muos-network/dropbear_ed25519_host_key.tmp.pub','var/lib/muos-network/network.conf'}
    rows={n:r for n,r in ctx['physical_capture']['backup_private_files'].items() if n in names}
    require(set(rows)==names,'Complete four-file stable identity inventory')
    code=''
    for name,row in sorted(rows.items()):
        mode=0o644 if name=='etc/muos-network-authorized_key' else 0o600
        require(row['mode']==mode and row['uid']==row['gid']==0 and row['links']==1 and
            type(row['bytes']) is int and 0<row['bytes']<=65536 and
            re.fullmatch('[0-9a-f]{64}',row['sha256']),'Qualified stable identity metadata')
        code+=f'''[ -f /{name} ];[ ! -L /{name} ]
[ "$(stat -c '%u:%g:%a:%h:%s' /{name})" = 0:0:{mode:o}:1:{row['bytes']} ]
[ "$(sha256sum /{name} | cut -d' ' -f1)" = {row['sha256']} ]
'''
    return code

def current_common(common,old_boot,new_boot):
    _,previous=qualified()
    require(type(new_boot) is int and new_boot==previous['boot_sequence']+1 and new_boot<=9998,
        'C104 requires the next boot; never reuse or rewrite the C103 UUID')
    code=legacy.current_common('',previous['boot_sequence'],new_boot)
    boot=importlib.import_module('collect-phase4-initial-boot')
    composition=Path((WORK/'initial-migration/latest-complete').read_text().strip())
    require(composition.resolve().is_relative_to(WORK/'initial-migration'),'Known C93 tree')
    code,_=boot.matched_common(code,json.loads((composition/'tree.json').read_text()))
    installer=importlib.import_module('run-phase4-c79-layout-install')
    # The template and destinations are public, pinned additions. No old UUID.
    from phase4_c79_layout import TEMPLATE,TEMPLATE_SHA
    code+=f'''[ ! -L /{TEMPLATE} ];[ "$(stat -c '%u:%g:%a:%h:%s' /{TEMPLATE})" = 0:0:755:1:444 ]
printf '%s  %s\\n' {TEMPLATE_SHA} /{TEMPLATE} | sha256sum -c - >/dev/null
'''
    return code+installer.HEALTH+stable_identity_guard()

def historical():
    qualified();result=legacy.historical();ctx=result[0]
    require(ctx['worker']==REPO/'port/device/rk-r35s-p0/app-selection/worker.sh' and
        'etc-view.sh' not in ctx['files'],'Original C77 worker required')
    return result

def bind(prior,provider,observation,boot,boot_id):
    stage,previous=qualified();transition(previous,boot,boot_id)
    require(observation['C103_analysis_sha256']==sha(stage/'analysis.json') and
        observation['C103_proof_sha256']==sha(proof('native-layout-session')/'SHA256SUMS'),
        'Fresh observation must bind the C103 qualification')
    return legacy.bind(prior,provider,observation,boot,boot_id)

def rendered_runner():
    source=REPO/'port/scripts/run-phase4-installed-core-session.py'
    require(source.read_bytes()==(proof('installed-core-session')/'source'/source.relative_to(REPO)).read_bytes(),
        'Frozen C77 runner required')
    text=source.read_text()
    changes={
        'from phase4_installed_core_session import ':'from phase4_reboot_layout_session import ',
        'p = argparse.ArgumentParser(description=__doc__)':
            'from phase4_reboot_layout_session import qualified\nqualification_stage, _ = qualified()\np = argparse.ArgumentParser(description=__doc__)',
        '*NATIVE.glob(\'*.sh\')]':
            '*NATIVE.glob(\'*.sh\'), REPO / \'port/scripts/phase4_reboot_layout_session.py\']',
        "'root_RO_installed_payload_and_foundation_verified': True, 'agent_requested_reboot': False,":
            "'root_RO_installed_payload_and_foundation_verified': True, 'agent_requested_reboot': False,\n                   'C103_analysis_sha256': sha(qualification_stage / 'analysis.json'),\n                   'C103_proof_sha256': sha(REPO / 'dist/phase4/native-layout-session/SHA256SUMS'),",
        "'observation_stage': str(observation_path), 'observation_sha256': sha(observation_path / 'observation.json'),":
            "'observation_stage': str(observation_path), 'observation_sha256': sha(observation_path / 'observation.json'),\n          'C103_analysis_sha256': observation['C103_analysis_sha256'], 'C103_proof_sha256': observation['C103_proof_sha256'],\n          'C104_post_reboot_layout_runtime_validation': True,",
        'C77 observed boot':'C104 observed post-reboot layout boot',
        'C77 session collected:':'C104 post-reboot session collected:',
    }
    for old,new in changes.items():
        require(text.count(old)==1,'Finite C104 runner adaptation anchor');text=text.replace(old,new)
    ast.parse(text);return text
