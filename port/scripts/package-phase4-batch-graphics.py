#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C121 publish only a closed native cycle with bound physical confirmation."""
import json,os,shutil,tempfile
from pathlib import Path
import phase4_batch_graphics as m
from phase4_backup_core import write_new,sync_dir

def main():
    os.umask(0o077);out=m.REPO/'dist/phase4/batch-graphics'
    m.require(not out.exists(),'Never replace frozen C121 proof')
    native,parent=m.qualified()
    stage=Path((m.AREA/'latest-load').read_text().strip())
    m.require(stage.resolve().is_relative_to(m.AREA),'Known C121 cycle')
    rows={n:json.loads((stage/n).read_text()) for n in ['analysis.json','technical-analysis.json','physical-observation.json','final-audit.json']}
    r,t,p,f=(rows[n] for n in ['analysis.json','technical-analysis.json','physical-observation.json','final-audit.json'])
    checks=Path((m.AREA/'latest-checks').read_text().strip())
    m.require(checks.resolve().is_relative_to(m.AREA),'Known C121 checks')
    tested=json.loads((checks/'analysis.json').read_text())
    for row in [*rows.values(),tested]:m.require(row['passed'] is True,'Complete C121 qualification')
    m.require(r['schema']==121 and r['checks_analysis_sha256']==m.sha(checks/'analysis.json'),'Exact checked C121 cycle')
    for key in ['C121_graphical_provider_routing','versioned_RAM_entrypoint_used','installed_worker_cmdline_confirmed',
      'RAM_removed','cleanup_passed','root_ro','global_mountinfo_unchanged','store_byte_identical_to_C63','process_maps_confirmed',
      'ROM_source_internal_p3','capsule_metadata_generated_on_device']:
        m.require(r[key] is True,'Native cycle incomplete: '+key)
    for key in ['installed_entrypoint_used','legacy_caller_scripts_transferred_by_host','new_save_requested','agent_requested_reboot']:
        m.require(r[key] is False,'Unexpected cycle behavior: '+key)
    m.require(r['runtime_input_uploads']==0 and r['RAM_contract_files_uploaded']==6 and r['public_assets_copied_locally']==11 and
      r['public_assets_uploaded_by_host']==0 and r['adopted_host_code_uploaded'] is True,'Only source bundle uploaded')
    m.require(r['C120_native_analysis_sha256']==m.sha(native/'analysis.json') and
      r['C120_proof_sha256']==m.sha(m.proof('batch-run')/'SHA256SUMS') and
      r['bundle_sha256']==parent['bundle_sha256']==tested['bundle_sha256'],'C120 contract binding')
    m.require(t['session_analysis_sha256']==p['session_analysis_sha256']==m.sha(stage/'analysis.json'),'Bound physical/technical reports')
    m.require(t['C121_batch_graphics_analyzed'] is t['timing_event_pair_valid'] is True,'Native timing evidence')
    for key in ['image_and_navigation_confirmed','sound_clean_and_audible_confirmed','restore_to_saved_position_confirmed','launcher_return_confirmed']:
        m.require(p[key] is True,'Physical confirmation incomplete')
    for n,h in f['recorded_receipts_sha256'].items():m.require(m.sha(stage/n)==h,'Recorded closure changed')
    for label in ['prepare','batch-bundle','batch-adopt','batch-stage','installed-host-check','native-provider-ABI','native','postflight','mount-health','caller-execution','cleanup','stopped-screen']:
        m.require((stage/(label+'.exit')).read_text()=='0\n','Native receipt incomplete: '+label)
    m.require((stage/'caller-execution.stdout').read_text()=='C120_BATCH_CALLER_RUN_ONCE_CONFIRMED\n','New run-once confirmation')
    m.require((stage/'watch-maps.stdout').read_text().count('C106_INSTALLED_WORKER_CMDLINE_CONFIRMED')==1,'Installed worker confirmed')
    m.require((stage/'prepare.stdout').read_text()=='C112_RESIDENT_PREPARED_ZERO_UPLOADS\n','Resident ROM source')
    m.require((stage/'preflight.stdout').read_bytes()==(stage/'postflight.stdout').read_bytes(),'Infrastructure preserved')
    source={Path(__file__),m.REPO/'docs/archive/phase4/phase4-batch-graphics-session.md'}
    for row in [*rows.values(),tested]:
        for name,h in row.get('source_sha256',{}).items():
            path=m.REPO/name;m.require(m.sha(path)==h,'Qualified source changed');source.add(path)
    public=Path(tempfile.mkdtemp(prefix='public.',dir=m.AREA))
    summary={'passed':True,'schema':121,'experiment':'C121_BATCH_HOST_MENU_GB_RETURN','boot_sequence':r['boot_sequence'],
      'native_graphical_dispatch_qualified':True,'image_input_audio_restore_and_return_physically_confirmed':True,
      'installed_worker_and_provider_used':True,'versioned_RAM_entrypoint_used':True,'original_installed_caller_modified':False,
      'host_batch_validation_used_for_launch':True,'core_frames':r['core_frames'],'snapshot_byte_identical':True,
      'runtime_input_uploads':0,'RAM_contract_files_uploaded':6,'ROM_source_internal_p3':True,
      'new_save_requested':False,'reboot_requested':False,'root_readonly':True,'RAM_removed':True,'global_mountinfo_unchanged':True,
      'full_image_generated_or_Deck_used':False,'general_ROM_browser_or_autostart_qualified':False,'long_run_or_power_loss_qualified':False,
      'offline_routing_cases':tested['case_count'],'bundle_sha256':r['bundle_sha256'],
      'parent_proofs_sha256':{'batch-run':r['C120_proof_sha256'],'resident-boot-session':m.sha(m.proof('resident-boot-session')/'SHA256SUMS')},
      'private_ROM_ELF_seed_or_snapshot_included':False,'redistribution_approved':False}
    write_new(public/'analysis.json',(json.dumps(summary,indent=2)+'\n').encode())
    write_new(public/'checks.json',(json.dumps({k:tested[k] for k in ['passed','case_count','cases','local_ROM_reads_prohibited','device_or_GUI_executed']},indent=2)+'\n').encode())
    metric_names=['reported_recent_core_hz','frame_mean_ms','audio_underruns','audio_missing_frames','observed_selection_to_present_seconds',
      'watch_nominal_sampling_seconds','watch_scheduler_delay_bounded','physical_button_timestamp_measured','core_reported_startup_ms','timing_event_pair_valid']
    write_new(public/'metrics.json',(json.dumps({k:t[k] for k in metric_names},indent=2)+'\n').encode())
    for src in source:
        dst=public/'source'/src.relative_to(m.REPO);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    forbidden=[r[k].encode() for k in ['kernel_boot_id','private_identity','ROM_sha256']]
    for path in public.rglob('*'):
        m.require(not path.is_symlink(),'No public aliases')
        if path.is_file():
            b=path.read_bytes();m.require(path.suffix in {'.py','.sh','.md','.json'} and not b.startswith(b'\x7fELF') and
              not any(value in b for value in forbidden),'Private content in proof')
    write_new(public/'SHA256SUMS',''.join(m.sha(path)+'  '+str(path.relative_to(public))+'\n' for path in sorted(public.rglob('*')) if path.is_file()).encode())
    for path in public.rglob('*'):
        if path.is_file():
            with path.open('rb') as handle:os.fsync(handle.fileno())
    for path in sorted((p for p in public.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):sync_dir(path)
    sync_dir(public);os.rename(public,out);sync_dir(out.parent)
    print('C121 native graphical sanitized proof:',out)
if __name__=='__main__':main()
