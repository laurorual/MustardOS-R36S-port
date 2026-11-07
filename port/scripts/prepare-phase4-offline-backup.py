#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C81 prepare a private, backup-only Deck bundle locally. No SSH/media IO."""
from pathlib import Path
import argparse, json, os, stat, tempfile
from phase4_candidate import sha, sums
from phase4_backup_core import write_new, sync_dir, validate_source_root_policy
from phase4_root_migration import require

REPO=Path(__file__).resolve().parents[2];WORK=REPO/'build/phase4';AREA=WORK/'offline-backup'
SOURCES=['phase4-offline-backup.py','phase4_backup_core.py','phase4_root_migration.py']

def verify_bundle(bundle):
    require(not bundle.is_symlink() and bundle.is_dir() and stat.S_IMODE(bundle.stat().st_mode)==0o700,'Private bundle directory')
    manifest=json.loads((bundle/'package.json').read_text())
    require(manifest['qualified_backup_only'] is True and manifest['native_qualified'] is False,'Backup-only bundle')
    require(set(manifest['files'])==set(SOURCES)|{'migration-plan.json'},'Bundle payload allowlist')
    require({p.name for p in bundle.iterdir()}==set(manifest['files'])|{'package.json'},'Bundle inventory')
    for name in set(manifest['files'])|{'package.json'}:
        p=bundle/name;s=p.lstat()
        require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600,'Bundle leaf type/links/mode')
        if name in manifest['files']:require(sha(p)==manifest['files'][name],'Bundle leaf hash')
    require(sha(bundle/'migration-plan.json')==manifest['plan_sha256'],'Bundle plan binding')
    if 'source_root_policy' in manifest:validate_source_root_policy(manifest['source_root_policy'])
    return manifest

def write_bundle(plan_path,target,checks_sha,source_root_policy=None):
    # Caller creates target exclusively, under the private build area.
    require(not list(target.iterdir()),'Bundle destination must be empty')
    for name in SOURCES:write_new(target/name,(REPO/'port/scripts'/name).read_bytes())
    write_new(target/'migration-plan.json',plan_path.read_bytes())
    plan=json.loads(plan_path.read_text())
    manifest={'schema':1,'experiment':'C81_PRIVATE_BACKUP_ONLY_BUNDLE','qualified_backup_only':True,
      'native_qualified':False,'plan_sha256':sha(plan_path),'checks_sha256':checks_sha,
      'survey_boot_sequence':plan['survey_boot_sequence'],'new_survey_required_after_another_boot':True,
      'device_writer_available':False,'candidate_provisioned':False,'execution_enabled':False,
      'files':{name:sha(target/name) for name in [*SOURCES,'migration-plan.json']}}
    if source_root_policy is not None:manifest['source_root_policy']=validate_source_root_policy(source_root_policy)
    write_new(target/'package.json',(json.dumps(manifest,indent=2)+'\n').encode())
    require(verify_bundle(target)==manifest,'Bundle reread differs');sync_dir(target)
    return manifest

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-root-policy',type=Path);args=parser.parse_args()
    os.umask(0o077);AREA.mkdir(exist_ok=True)
    parents={}
    for name in ['root-migration','gambatte-card-image']:
        proof=REPO/'dist/phase4'/name
        for leaf,h in sums(proof/'SHA256SUMS').items():require(sha(proof/leaf)==h,'Parent proof changed')
        parents[name]=sha(proof/'SHA256SUMS')
    planned=Path((WORK/'root-migration/latest-plan').read_text().strip())
    require(planned.resolve().is_relative_to(WORK/'root-migration'),'Private plan location')
    prior=json.loads((planned/'analysis.json').read_text());plan_path=planned/'migration-plan.json'
    require(prior['passed'] is True and prior['plan_sha256']==sha(plan_path),'C80 survey/plan binding')
    plan=json.loads(plan_path.read_text())
    require(plan['experiment']=='C80_ROOT_ONLY_MIGRATION_PLAN' and plan['execution_enabled'] is False and plan['device_writer_available'] is False,'C80 disabled writer')
    for name,h in prior['source_sha256'].items():require(sha(REPO/name)==h,'C80 source changed')
    checked=Path((AREA/'latest-checks').read_text().strip())
    require(checked.resolve().is_relative_to(AREA),'Checks location')
    checks=json.loads((checked/'analysis.json').read_text())
    require(checks['passed'] is True and checks['case_count']==len(checks['cases']) and checks['case_count']>=58,'Checks incomplete')
    for name,h in checks['source_sha256'].items():require(sha(REPO/name)==h,'Checks source changed')
    require(set(checks['source_sha256'])=={'port/scripts/'+name for name in [*SOURCES,'collect-phase4-offline-backup.py','check-phase4-offline-backup.py',Path(__file__).name]},'Checks source closure')
    stage=Path(tempfile.mkdtemp(prefix='package.',dir=AREA));bundle=stage/'bundle';bundle.mkdir(mode=0o700)
    source_policy=None
    if args.source_root_policy:
        require(args.source_root_policy.resolve().is_relative_to(AREA),'Private source-policy location')
        source_policy=validate_source_root_policy(json.loads(args.source_root_policy.read_text()))
    manifest=write_bundle(plan_path,bundle,sha(checked/'analysis.json'),source_policy)
    report={'passed':True,'experiment':'C81_OFFLINE_BUNDLE_PREPARED','checks_sha256':manifest['checks_sha256'],
      'checks_case_count':checks['case_count'],'bundle_manifest_sha256':sha(bundle/'package.json'),
      'survey_boot_sequence':plan['survey_boot_sequence'],'bundle_inventory_verified':True,
      'plan_sha256':sha(plan_path),'parent_proofs_sha256':parents,
      'source_sha256':checks['source_sha256'],'native_qualified':False,'SSH_requested':False,
      'real_backup_created':False,'device_written':False,'candidate_provisioned':False,
      'execution_enabled':False,'device_writer_available':False}
    if source_policy is not None:report['source_root_policy']=source_policy
    write_new(stage/'analysis.json',(json.dumps(report,indent=2)+'\n').encode())
    write_new(stage/'NEXT.txt',b'C81 prepared offline only. Do not run without a current C80 survey and an explicitly scheduled card transfer.\nNative Deck dependencies, mount isolation and device guards remain unqualified.\nFuture local command: sudo /usr/bin/python3 /home/deck/muos-r35s-c81/phase4-offline-backup.py backup\nNever reuse the C20 formatter/server for this operation. Never use the original32 card.\nIndependent host copy and post-boot recovery implementation remain required before any root write/boot.\n')
    sync_dir(stage);(AREA/'latest-package').write_text(str(stage)+'\n')
    print('C81 private bundle prepared offline; native backup NOT executed:',stage)

if __name__=='__main__':main()
