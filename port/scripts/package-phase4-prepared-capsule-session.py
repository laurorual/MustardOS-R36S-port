#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C109 sanitized proof of the real installed-caller menu/game/return cycle."""
from pathlib import Path
import json,os,shutil,tempfile
import phase4_prepared_capsule_session as session
from phase4_backup_core import write_new,sync_dir

def main():
    os.umask(0o077);out=session.REPO/'dist/phase4/prepared-capsule-session'
    session.require(not out.exists(),'Never replace frozen C109 proof')
    install,_,_,_=session.qualified()
    stage=Path((session.AREA/'latest-load').read_text().strip())
    session.require(stage.resolve().is_relative_to(session.AREA),'Known C109 session')
    r=json.loads((stage/'analysis.json').read_text())
    technical=json.loads((stage/'technical-analysis.json').read_text())
    physical=json.loads((stage/'physical-observation.json').read_text())
    final=json.loads((stage/'final-audit.json').read_text())
    checks=Path((session.AREA/'latest-checks').read_text().strip())
    tested=json.loads((checks/'analysis.json').read_text())
    for row in [r,technical,physical,final,tested]:session.require(row['passed'] is True,'Complete C109 qualification')
    for k in ['C109_local_preparation_runtime_validation','installed_entrypoint_used','installed_worker_cmdline_confirmed',
              'RAM_removed','cleanup_passed','root_ro','global_mountinfo_unchanged','store_byte_identical_to_C63','process_maps_confirmed']:
        session.require(r[k] is True,'Incomplete installed caller session')
    session.require(r['schema']==109 and r['caller_scripts_transferred_by_host'] is False and
        r['new_save_requested'] is False and r['agent_requested_reboot'] is False and
        r['C111_analysis_sha256']==session.sha(install/'analysis.json') and
        r['C111_proof_sha256']==session.sha(session.proof('capsule-preparer-v3-installed')/'SHA256SUMS'),
        'Installed caller and read-only source binding')
    session.require(technical['session_analysis_sha256']==physical['session_analysis_sha256']==session.sha(stage/'analysis.json'),
        'Physical and technical receipts belong to this session')
    for k in ['image_and_navigation_confirmed','sound_clean_and_audible_confirmed',
              'restore_to_saved_position_confirmed','launcher_return_confirmed']:
        session.require(physical[k] is True,'Physical confirmation incomplete')
    for n,h in final['recorded_receipts_sha256'].items():session.require(session.sha(stage/n)==h,'Closure receipt changed')
    session.require((stage/'caller-execution.exit').read_text()=='0\n' and
        (stage/'caller-execution.stdout').read_text()=='C106_INSTALLED_CALLER_RUN_ONCE_CONFIRMED\n' and
        (stage/'watch-maps.stdout').read_text().count('C106_INSTALLED_WORKER_CMDLINE_CONFIRMED')==1,
        'Authentic installed entry/worker evidence')
    session.require(r['checks_analysis_sha256']==session.sha(checks/'analysis.json'),'Checked C109 implementation')
    session.require(r['capsule_metadata_generated_on_device'] is True and
        r['public_assets_copied_locally']==7 and r['public_assets_uploaded_by_host']==4 and
        technical['C109_local_preparation_analyzed'] is technical['timing_event_pair_valid'] is True,
        'Local preparation and sampled startup evidence')
    session.require((stage/'prepare.stdout').read_text()=='C107_CAPSULE_PREPARED_RAM_ONLY\n' and
        (stage/'prepare.exit').read_text()=='0\n','Native preparation completed')
    sources={Path(__file__),session.REPO/'docs/analysis/phase4-prepared-capsule-session.md'}
    for row in [r,tested,technical,final]:
        for n,h in row['source_sha256'].items():
            source=session.REPO/n;session.require(session.sha(source)==h,'Qualified source changed');sources.add(source)
    public=Path(tempfile.mkdtemp(prefix='public.',dir=session.AREA))
    summary={'passed':True,'schema':109,'experiment':'C109_INSTALLED_CALLER_MENU_GB_RETURN',
        'boot_sequence':r['boot_sequence'],'installed_entrypoint_and_worker_confirmed':True,
        'C105_scripts_staged_by_installed_component':True,'caller_scripts_uploaded_by_host':False,
        'image_input_audio_restore_and_return_physically_confirmed':True,'core_frames':r['core_frames'],
        'snapshot_byte_identical':True,'new_save_requested':False,'reboot_requested':False,
        'root_readonly':True,'RAM_removed':True,'global_mountinfo_unchanged':True,
        'installed_caller_payload_modified':False,'full_image_generated_or_Deck_used':False,
        'new_routing_checks':tested['case_count'],'C107_C111_cases_reused':tested['C107_C111_cases_reused'],
        'capsule_metadata_generated_on_device':True,'public_assets_copied_locally':7,
        'public_assets_uploaded_by_host':4,'host_input_files_including_private_ROM':5,
        'general_ROM_browser_or_autostart_qualified':False,'long_run_or_power_loss_qualified':False,
        'private_runtime_identity_ROM_ELF_seed_or_state_included':False,'redistribution_approved':False,
        'parent_proofs_sha256':{'capsule-preparer-v3-installed':r['C111_proof_sha256'],
            'reboot-layout-session':session.sha(session.proof('reboot-layout-session')/'SHA256SUMS')}}
    write_new(public/'analysis.json',(json.dumps(summary,indent=2)+'\n').encode())
    write_new(public/'checks.json',(json.dumps({k:tested[k] for k in ['passed','case_count','cases',
        'C107_C111_cases_reused','device_or_network_accessed',
        'core_ROM_reboot_or_image_build_executed']},indent=2)+'\n').encode())
    write_new(public/'metrics.json',(json.dumps({k:technical[k] for k in
        ['reported_recent_core_hz','frame_mean_ms','audio_underruns','audio_missing_frames',
         'observed_selection_to_present_seconds','watch_nominal_sampling_seconds','watch_scheduler_delay_bounded',
         'physical_button_timestamp_measured','core_reported_startup_ms','timing_event_pair_valid']},indent=2)+'\n').encode())
    for source in sources:
        target=public/'source'/source.relative_to(session.REPO);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    forbidden=[r[k].encode() for k in ['kernel_boot_id','ROM_sha256','private_identity']]
    for p in public.rglob('*'):
        session.require(not p.is_symlink(),'No public aliases')
        if p.is_file():
            data=p.read_bytes();session.require(p.suffix in {'.py','.sh','.json','.md'} and
                not data.startswith(b'\x7fELF') and not any(v in data for v in forbidden),'Private content in public proof')
    write_new(public/'SHA256SUMS',''.join(session.sha(p)+'  '+str(p.relative_to(public))+'\n'
        for p in sorted(public.rglob('*')) if p.is_file()).encode())
    for p in public.rglob('*'):
        if p.is_file():
            with p.open('rb') as stream:os.fsync(stream.fileno())
    for p in sorted((p for p in public.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):sync_dir(p)
    sync_dir(public);os.rename(public,out);sync_dir(out.parent)
    print('C109 installed caller sanitized proof:',out)

if __name__=='__main__':main()
