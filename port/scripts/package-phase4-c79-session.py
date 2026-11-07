#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze public C99 evidence only after physical confirmation and cleanup."""
from pathlib import Path
import json,os,shutil,tempfile
import phase4_c79_session as session
from phase4_backup_core import write_new,sync_dir
from phase4_root_migration import require


def main():
    os.umask(0o077);out=session.REPO/'dist/phase4/c79-session'
    require(not out.exists(),'Frozen C99 proof must not be replaced')
    qualified,boot=session.qualified()
    stage=Path((session.AREA/'latest-load').read_text().strip())
    require(stage.resolve().is_relative_to(session.AREA),'Known C99 session stage')
    report=json.loads((stage/'analysis.json').read_text())
    checks=Path((session.AREA/'latest-checks').read_text().strip())
    require(checks.resolve().is_relative_to(session.AREA),'Known C99 checks stage')
    tested=json.loads((checks/'analysis.json').read_text())
    final=json.loads((stage/'final-audit.json').read_text())
    physical=json.loads((stage/'physical-observation.json').read_text())
    technical=json.loads((stage/'technical-analysis.json').read_text())
    native_stage=Path((session.AREA/'latest-native-etc').read_text().strip())
    require(native_stage.resolve().is_relative_to(session.AREA),'Known C99 native isolation stage')
    native=json.loads((native_stage/'analysis.json').read_text())
    require(all(r['passed'] is True for r in [report,tested,final,physical,technical,native]),'Complete C99 evidence required')
    require(native['boot_sequence']==boot['boot_sequence'] and native['checks_analysis_sha256']==session.sha(checks/'analysis.json') and
        native['original_mmc_mountpoint_remains_absent'] is True and native['original_asound_remains_absent'] is True and
        native['capsule_removed'] is True,'Native C79 runtime isolation qualification required')
    require(report['C99_C79_runtime_validation'] is True and report['boot_sequence']==boot['boot_sequence'] and
        report['kernel_boot_id']==boot['kernel_boot_id'] and report['C97_analysis_sha256']==session.sha(qualified/'analysis.json') and
        report['C97_proof_sha256']==session.sha(session.proof('initial-boot-native')/'SHA256SUMS') and
        report['checks_analysis_sha256']==session.sha(checks/'analysis.json'),'Qualified boot and checks binding')
    for n in ['installed_core_used','installed_host_used','game_uses_installed_provider4','process_maps_confirmed',
        'store_byte_identical_to_C63','RAM_removed','root_ro','cleanup_passed','global_mountinfo_unchanged']:
        require(report[n] is True,'Incomplete installed cycle or cleanup')
    for n in ['core_ELF_transferred','host_ELF_transferred','store_ELF_transferred','new_save_requested','agent_requested_reboot']:
        require(report[n] is False,'Unexpected write or executable deployment')
    require(physical['session_analysis_sha256']==technical['session_analysis_sha256']==session.sha(stage/'analysis.json'),
        'Physical and technical evidence must refer to the same session')
    for n in ['image_and_navigation_confirmed','sound_clean_and_audible_confirmed',
        'restore_to_saved_position_confirmed','launcher_return_confirmed']:
        require(physical[n] is True,'Physical confirmation incomplete')
    for n,h in final['recorded_receipts_sha256'].items():require(session.sha(stage/n)==h,'Recorded cleanup receipt changed')
    sources={Path(__file__),session.REPO/'docs/analysis/phase4-c79-session.md'}
    for r in [report,tested,final,technical,native]:
        for n,h in r['source_sha256'].items():
            require(session.sha(session.REPO/n)==h,'C99 evidence source changed');sources.add(session.REPO/n)
    parents={n:session.sha(session.proof(n)/'SHA256SUMS') for n in ['installed-core-session','initial-boot-native','p2-initial-native']}
    public=Path(tempfile.mkdtemp(prefix='public.',dir=session.AREA))
    summary={'passed':True,'experiment':'C99_C79_INSTALLED_LAUNCH_GAME_RETURN','boot_sequence':report['boot_sequence'],
        'installed_host_provider4_and_core_used':True,'physical_image_input_audio_restore_and_return_confirmed':True,
        'core_frames':report['core_frames'],'new_binding_checks':tested['case_count'],'unchanged_C77_cases_reused':47,
        'root_readonly':True,'RAM_removed':True,'global_mountinfo_unchanged':True,'snapshot_byte_identical':True,
        'new_save_requested':False,'executable_install_or_image_write':False,'reboot_requested':False,
        'private_etc_and_mnt_native_isolation_qualified':True,
        'permanent_frontend_or_general_ROM_browser_qualified':False,'long_run_or_power_loss_qualified':False,
        'private_runtime_data_or_ROM_state_ELFs_included':False,'redistribute':False,'parent_proofs_sha256':parents}
    metrics={n:technical[n] for n in ['reported_recent_core_hz','frame_mean_ms','audio_underruns','audio_missing_frames']}
    write_new(public/'analysis.json',(json.dumps(summary,indent=2)+'\n').encode())
    write_new(public/'metrics.json',(json.dumps(metrics,indent=2)+'\n').encode())
    write_new(public/'checks.json',(json.dumps({n:tested[n] for n in ['passed','case_count','cases','unchanged_C77_cases_reused',
        'device_or_network_accessed','core_or_ROM_executed']},indent=2)+'\n').encode())
    for source in sources:
        target=public/'source'/source.relative_to(session.REPO);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
    forbidden={report[n] for n in ['private_identity','ROM_sha256','kernel_boot_id','C97_analysis_sha256']}
    for f in public.rglob('*'):
        require(not f.is_symlink(),'Public symlink')
        if f.is_file():
            data=f.read_bytes();require(f.suffix in {'.py','.sh','.md','.json'} and not data.startswith(b'\x7fELF'),
                'Unexpected public payload')
            require(not any(v.encode() in data for v in forbidden),'Private runtime data in proof')
    write_new(public/'SHA256SUMS',''.join(session.sha(f)+'  '+str(f.relative_to(public))+'\n'
        for f in sorted(public.rglob('*')) if f.is_file()).encode())
    for f in public.rglob('*'):
        if f.is_file():
            fd=os.open(f,os.O_RDONLY|os.O_NOFOLLOW)
            try:os.fsync(fd)
            finally:os.close(fd)
    for directory in sorted((p for p in public.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):sync_dir(directory)
    sync_dir(public);os.rename(public,out);sync_dir(out.parent)
    print('C99 C79 runtime proof:',out)


if __name__=='__main__':main()
