#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C104 freeze sanitized evidence of the explicitly observed reboot and cycle."""
from pathlib import Path
import json,os,shutil,tempfile
import phase4_reboot_layout_session as session
from phase4_backup_core import write_new,sync_dir
from phase4_root_migration import require

def main():
    os.umask(0o077);out=session.REPO/'dist/phase4/reboot-layout-session'
    require(not out.exists(),'Frozen C104 proof must not be replaced')
    old,previous=session.qualified()
    stage=Path((session.AREA/'latest-load').read_text().strip())
    require(stage.resolve().is_relative_to(session.AREA),'Known C104 session stage')
    r=json.loads((stage/'analysis.json').read_text());session.transition(previous,r['boot_sequence'],r['kernel_boot_id'])
    require(r['C104_post_reboot_layout_runtime_validation'] is True and
        r['C103_analysis_sha256']==session.sha(old/'analysis.json') and
        r['C103_proof_sha256']==session.sha(session.proof('native-layout-session')/'SHA256SUMS'),'Prior C103 binding')
    checks=Path((session.AREA/'latest-checks').read_text().strip())
    require(checks.resolve().is_relative_to(session.AREA) and session.sha(checks/'analysis.json')==r['checks_analysis_sha256'],
        'Known C104 checked sources')
    tested=json.loads((checks/'analysis.json').read_text())
    final=json.loads((stage/'final-audit.json').read_text())
    technical=json.loads((stage/'technical-analysis.json').read_text())
    physical=json.loads((stage/'physical-observation.json').read_text())
    for d in [r,tested,final,technical,physical]:require(d['passed'] is True,'Complete C104 qualification required')
    for key in ['RAM_removed','cleanup_passed','root_ro','global_mountinfo_unchanged','store_byte_identical_to_C63',
        'installed_core_used','installed_host_used','game_uses_installed_provider4','process_maps_confirmed']:
        require(r[key] is True,'Incomplete native session')
    for key in ['new_save_requested','agent_requested_reboot','host_ELF_transferred','core_ELF_transferred','store_ELF_transferred']:
        require(r[key] is False,'Unexpected session operation')
    require(physical['session_analysis_sha256']==technical['session_analysis_sha256']==session.sha(stage/'analysis.json'),
        'Technical and physical results must belong to this native session')
    for key in ['image_and_navigation_confirmed','sound_clean_and_audible_confirmed','restore_to_saved_position_confirmed','launcher_return_confirmed']:
        require(physical[key] is True,'Physical confirmation incomplete')
    for n,h in final['recorded_receipts_sha256'].items():require(session.sha(stage/n)==h,'Native receipts changed')
    request=Path((session.AREA/'latest-reboot-request').read_text().strip())
    require(request.resolve().is_relative_to(session.AREA) and
        (session.AREA/'reboot-request.claim').read_text()==str(request)+'\n','One recorded reboot request')
    intent=json.loads((request/'intent.json').read_text());sent=json.loads((request/'request.json').read_text())
    require(sent['requested'] is True and sent['normal_PID1'] is True and sent['token_rearmed'] is False and
        sent['previous_boot_sequence']==previous['boot_sequence'] and sent['expected_boot_sequence']==r['boot_sequence'] and
        intent['previous_kernel_boot_id']==previous['kernel_boot_id'] and
        intent['C103_analysis_sha256']==r['C103_analysis_sha256'] and intent['checks_sha256']==r['checks_analysis_sha256'],
        'Normal request and observed return must match')
    require((request/'request.stdout').read_text()=='C104_REQUEST_NORMAL_C07_REBOOT\n' and
        (request/'request.exit').read_text() in ('0\n','255\n'),'Authentic normal reboot request receipt')
    native_intent=json.loads((stage/'intent.json').read_text())
    worker=session.REPO/'port/device/rk-r35s-p0/app-selection/worker.sh'
    require(native_intent['worker_sha256']==session.sha(worker) and 'etc-view.sh' not in native_intent['binary_sha256'],
        'Original worker without directory views required')
    sources={Path(__file__),worker,session.REPO/'docs/archive/phase4/phase4-reboot-layout-session.md'}
    for d in [r,tested,final,technical,sent]:
        for n,h in d['source_sha256'].items():
            require(session.sha(session.REPO/n)==h,'Qualified source changed');sources.add(session.REPO/n)
    parents={n:session.sha(session.proof(n)/'SHA256SUMS') for n in ['native-layout-session','c79-layout-installed','installed-core-session']}
    public=Path(tempfile.mkdtemp(prefix='public.',dir=session.AREA))
    summary={'passed':True,'schema':104,'experiment':'C104_POST_REBOOT_INSTALLED_LAYOUT_LAUNCH_GAME_RETURN',
        'previous_boot_sequence':previous['boot_sequence'],'boot_sequence':r['boot_sequence'],
        'fresh_boot_identity_and_four_stable_identities_verified':True,'normal_PID1_reboot_requested_once':True,
        'installed_layout_and_original_worker_used':True,'physical_image_input_audio_restore_return_confirmed':True,
        'installed_host_provider4_core_maps_confirmed':True,'core_frames':r['core_frames'],
        'new_checks':tested['case_count'],'root_readonly':True,'RAM_removed':True,'global_mountinfo_unchanged':True,
        'snapshot_byte_identical':True,'new_save_requested':False,'observer_read_seed_file_or_invoked_rng':False,
        'raw_image_write_or_token_rearmed':False,'permanent_frontend_or_cold_boot_qualified':False,
        'long_run_or_power_loss_qualified':False,'private_runtime_data_or_ROM_state_ELFs_included':False,
        'redistribute':False,'parent_proofs_sha256':parents}
    metrics={n:technical[n] for n in ['reported_recent_core_hz','frame_mean_ms','audio_underruns','audio_missing_frames']}
    write_new(public/'analysis.json',(json.dumps(summary,indent=2)+'\n').encode())
    write_new(public/'metrics.json',(json.dumps(metrics,indent=2)+'\n').encode())
    write_new(public/'checks.json',(json.dumps({n:tested[n] for n in ['passed','case_count','cases',
        'C103_checks_reused','C77_checks_reused','device_or_network_accessed','reboot_executed','core_or_ROM_executed']},indent=2)+'\n').encode())
    for source in sources:
        target=public/'source'/source.relative_to(session.REPO);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    forbidden={r[n] for n in ['private_identity','ROM_sha256','kernel_boot_id','C103_analysis_sha256']}|{previous['kernel_boot_id']}
    for f in public.rglob('*'):
        require(not f.is_symlink(),'Public symlink')
        if f.is_file():
            data=f.read_bytes();require(f.suffix in {'.py','.sh','.md','.json'} and not data.startswith(b'\x7fELF') and
                not any(v.encode() in data for v in forbidden),'Unexpected private public payload')
    write_new(public/'SHA256SUMS',''.join(session.sha(f)+'  '+str(f.relative_to(public))+'\n'
        for f in sorted(public.rglob('*')) if f.is_file()).encode())
    for f in public.rglob('*'):
        if f.is_file():
            with f.open('rb') as stream:os.fsync(stream.fileno())
    for d in sorted((p for p in public.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):sync_dir(d)
    sync_dir(public);os.rename(public,out);sync_dir(out.parent)
    print('C104 post-reboot runtime proof:',out)

if __name__=='__main__':main()
