#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze only public C105 payload/source and sanitized native evidence."""
import json,os,shutil,tempfile
from phase4_manual_caller import *
from phase4_backup_core import write_new,sync_dir

def main():
    os.umask(0o077);out=REPO/'dist/phase4/manual-caller-installed'
    require(not out.exists(),'Never replace a frozen proof')
    stage=Path((AREA/'latest-complete').read_text().strip())
    package=Path((AREA/'latest-package').read_text().strip())
    checks=Path((AREA/'latest-checks').read_text().strip())
    require(all(p.resolve().is_relative_to(AREA) for p in [stage,package,checks]),'Known C105 stages')
    report=json.loads((stage/'analysis.json').read_text());plan=json.loads((stage/'plan.json').read_text())
    built=json.loads((package/'analysis.json').read_text());tested=json.loads((checks/'analysis.json').read_text())
    require(report['passed'] is built['passed'] is tested['passed'] is True,'Complete C105 installation required')
    require(report['schema']==105 and report['files_added']==17 and report['directories_added']==1 and
        report['existing_files_replaced']==0 and report['root_read_only'] is True and report['RAM_removed'] is True and
        report['native_stage_and_repeat_incomplete_run_refusal_passed'] is True and
        report['private_state_fingerprint_matched'] is True and
        report['infrastructure_and_global_mounts_preserved'] is True and
        report['full_graphical_installed_caller_qualified'] is False,'Exact manual-only C105 scope')
    require(report['plan_sha256']==sha(stage/'plan.json') and
        plan['package_analysis_sha256']==sha(package/'analysis.json') and
        report['checks_sha256']==plan['checks_sha256']==sha(checks/'analysis.json') and
        report['source_sha256']==built['source_sha256']==tested['source_sha256'],'Bound plan, payload and tests')
    require(tested['case_count']==43 and tested['binding_test_groups']==4 and tested['binding_negative_variants']==12 and
        tested['fresh_generated_guard_same_foundation_and_ready_gate'] is True,'Caller and boot binding checks')
    for n,h in report['source_sha256'].items():require(sha(REPO/n)==h,'Qualified source changed')
    for n,h in report['parent_proofs_sha256'].items():require(sha(parent.proof(n)/'SHA256SUMS')==h,'Parent proof changed')
    for label in ['survey','before','inspect','dispatch','result','after','mounts-private','caller-check',
                  'native-stage','cleanup-stage','cleanup','post-cleanup-health']:
        require((stage/(label+'.exit')).read_text()=='0\n','Successful native receipt required')
    require((stage/'before.stdout').read_bytes()==(stage/'after.stdout').read_bytes()==
        (stage/'post-cleanup-health.stdout').read_bytes(),'Stable infrastructure')
    require((stage/'caller-check.stdout').read_text()=='C105_CALLER_CHECK_OK_NO_UI\n' and
        (stage/'native-stage.stdout').read_text()=='C105_CALLER_STAGE_OK_RAM_ONLY\nC105_NATIVE_STAGE_AND_INCOMPLETE_RUN_REFUSAL_OK\n' and
        (stage/'cleanup.stdout').read_text()=='C105_RAM_REMOVED_ROOT_RO\n','Authentic native caller/staging/cleanup receipts')
    result=(stage/'collected-result.txt').read_text()
    require(result.startswith('0\n') and result.count('C105_INSTALLED_ROOT_RO_NO_SERVICE_NO_TOKEN_NO_REBOOT')==1,
        'Authentic installation completion')
    observed=Path(plan['observation_stage']);obs=json.loads((observed/'observation.json').read_text())
    prior,previous=qualified()
    observation_binding(obs,previous,sha(prior/'analysis.json'),sha(REPO/'port/scripts/phase4_manual_caller.py'))
    require(sha(observed/'observation.json')==plan['observation_sha256'] and
        obs['boot_sequence']==report['boot_sequence'] and (observed/'ready.exit').read_text()=='0\n','New ready boot binding')
    public=Path(tempfile.mkdtemp(prefix='public.',dir=AREA))
    summary={**report,'caller_checks':43,'boot_binding_test_groups':4,'boot_binding_negative_variants':12,
        'prior_failed_C07_report_relabelled_as_success':False,'private_runtime_identity_included':False,
        'private_guard_or_ROM_ELF_seed_state_included':False,'redistribution_approved':False}
    write_new(public/'analysis.json',(json.dumps(summary,indent=2)+'\n').encode())
    keys=['passed','case_count','cases','binding_test_groups','binding_negative_variants',
          'fresh_generated_guard_same_foundation_and_ready_gate','actual_device_accessed',
          'platform_tmpfs_and_run_callbacks_mocked','core_ROM_namespace_or_reboot_executed']
    write_new(public/'checks.json',(json.dumps({k:tested[k] for k in keys},indent=2)+'\n').encode())
    for n,h in built['package_files'].items():
        source=package/'target'/PREFIX/n;require(sha(source)==h,'Public installed payload changed')
        target=public/'payload'/n;target.parent.mkdir(exist_ok=True);shutil.copyfile(source,target)
    for n,h in built['adapter_sha256'].items():
        require(sha(package/n)==h,'Derived installer changed')
        target=public/'adapter'/n;target.parent.mkdir(exist_ok=True);shutil.copyfile(package/n,target)
    sources=[REPO/n for n in report['source_sha256']]+[Path(__file__),REPO/'docs/archive/phase4/phase4-manual-caller.md']
    for source in sources:
        target=public/'source'/source.relative_to(REPO);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    forbidden=[obs['kernel_boot_id'].encode(),previous['kernel_boot_id'].encode()]
    for f in public.rglob('*'):
        require(not f.is_symlink(),'No public symlinks')
        if f.is_file():
            data=f.read_bytes()
            private_key=any(line.startswith(b'-----BEGIN ') and line.endswith(b'PRIVATE KEY-----') for line in data.splitlines())
            require(not data.startswith(b'\x7fELF') and not private_key and not any(x in data for x in forbidden),'Private/binary public content')
    write_new(public/'SHA256SUMS',''.join(sha(p)+'  '+str(p.relative_to(public))+'\n'
        for p in sorted(public.rglob('*')) if p.is_file()).encode())
    for p in public.rglob('*'):
        if p.is_file():
            with p.open('rb') as stream:os.fsync(stream.fileno())
    for p in sorted((p for p in public.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):sync_dir(p)
    sync_dir(public);os.rename(public,out);sync_dir(out.parent)
    print('C105 sanitized installed caller proof:',out)

if __name__=='__main__':main()
