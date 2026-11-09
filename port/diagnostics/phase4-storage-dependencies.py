#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Read-only dependency trace for the current C104-C118 setup."""
import os,sys,json
from pathlib import Path
sys.dont_write_bytecode=True
repo=Path(__file__).resolve().parents[2]; reads=set();metadata=set()
sys.path.insert(0,str(repo/'port/scripts'))
def audit(event,args):
    if event=='open':
        p,mode,flags=args
        if isinstance(p,(str,bytes)):
            q=Path(os.fsdecode(p)).absolute()
            if flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):raise RuntimeError('Offline trace attempted write '+str(q))
            if q.is_relative_to(repo):reads.add(str(q.relative_to(repo)))
    if event=='subprocess.Popen' and args[1][:3]==['git','check-ignore','--quiet']:return
    if event in ('subprocess.Popen','os.system','socket.connect','os.remove','os.rename','os.mkdir','os.rmdir'):raise RuntimeError('Offline trace attempted '+event)
oldstat=os.stat
oldlstat=os.lstat
def stat(p,*args,**kw):
    if isinstance(p,(str,bytes,os.PathLike)):
        q=Path(os.fsdecode(p)).absolute()
        if q.is_relative_to(repo):metadata.add(str(q.relative_to(repo)))
    return oldstat(p,*args,**kw)
def lstat(p,*args,**kw):
    if isinstance(p,(str,bytes,os.PathLike)):
        q=Path(os.fsdecode(p)).absolute()
        if q.is_relative_to(repo):metadata.add(str(q.relative_to(repo)))
    return oldlstat(p,*args,**kw)
os.stat=stat;os.lstat=lstat
sys.addaudithook(audit)
import phase4_manual_caller as m
m.qualified(); m.common();m.public_dependencies()
ctx,*rest=m.parent.legacy.historical()
# The installed component and the next runner add receipts and public assets,
# not another root image. Trace these before pruning any historical scaffolds.
import phase4_installed_caller_session as current
_,installed,_,_=current.qualified()
current.current_common('',0,installed['boot_sequence']);current.rendered_runner()
# Protect the installed preparer package, native receipts and current integration.
import phase4_prepared_capsule_session as prepared
_,prepared_report,_,_=prepared.qualified()
prepared.current_common('',0,prepared_report['boot_sequence']);prepared.rendered_runner()
prepared.prep.asset_model()
# The successful graphical cycle adds immutable receipts and its public proof.
prepared.proof('prepared-capsule-session')
session_stage=Path((prepared.AREA/'latest-load').read_text().strip())
assert session_stage.resolve().is_relative_to(prepared.AREA)
records={name:json.loads((session_stage/name).read_text()) for name in
    ['analysis.json','technical-analysis.json','physical-observation.json','final-audit.json']}
assert all(row['passed'] is True for row in records.values())
for name in ['technical-analysis.json','physical-observation.json']:
    assert records[name]['session_analysis_sha256']==prepared.sha(session_stage/'analysis.json')
for row in records.values():
    for name,digest in row.get('source_sha256',{}).items():assert prepared.sha(repo/name)==digest
for name,digest in records['final-audit.json']['recorded_receipts_sha256'].items():
    assert prepared.sha(session_stage/name)==digest
# Runtime inputs can be returned as Paths before first open.
def walk(v):
    if isinstance(v,Path):
        q=v.absolute()
        if q.is_relative_to(repo) and q.is_file():reads.add(str(q.relative_to(repo)))
    elif isinstance(v,dict):
        for x in v.values():walk(x)
    elif isinstance(v,(tuple,list)):
        for x in v:walk(x)
walk(ctx);walk(rest[:-1])
# Resident package, independent ROM backup, preparation receipts and future GUI.
import phase4_resident_session as resident
_,resident_report,_,_=resident.qualified()
resident.current_common('',0,resident_report['boot_sequence']);resident.rendered_runner()
resident_history=resident.historical();walk(resident_history[:-1])
for area,names in [(resident.assets.AREA,['latest-package','latest-complete']),
                   (resident.store.AREA,['latest-complete']),
                   (resident.resident.AREA,['latest-complete']),
                   (resident.AREA,['latest-checks'])]:
    for name in names:
        stage=Path((area/name).read_text().strip())
        assert stage.resolve().is_relative_to(area)
        row=json.loads((stage/'analysis.json').read_text());assert row['passed'] is True
        for source,digest in row.get('source_sha256',{}).items():assert resident.sha(repo/source)==digest
        for source,digest in row.get('package_files',{}).items():
            assert resident.sha(stage/'target'/resident.assets.PREFIX/source)==digest
# A fresh postboot session retains the original import and the new observation.
# This is source/receipt history, not another firmware tree.
import phase4_resident_boot_session as postboot
postboot.qualified();postboot.rendered_runner()
checks=Path((postboot.AREA/'latest-checks').read_text().strip())
assert checks.resolve().is_relative_to(postboot.AREA)
checked=json.loads((checks/'analysis.json').read_text());assert checked['passed'] is True
for source,digest in checked['source_sha256'].items():assert postboot.sha(repo/source)==digest
observed=Path((postboot.AREA/'latest-observation').read_text().strip())
assert observed.resolve().is_relative_to(postboot.AREA)
observation=json.loads((observed/'observation.json').read_text())
guard=postboot.current_common('',0,observation['boot_sequence'],observation['kernel_boot_id'])
assert (observed/'preflight.sh').read_text()==guard+resident_history[0]['infra']
assert (observed/'preflight.exit').read_text()=='0\n'
postboot.bind(resident_history[2],resident_history[4],observation,
              observation['boot_sequence'],observation['kernel_boot_id'])
for source,digest in observation['source_sha256'].items():assert postboot.sha(repo/source)==digest
for receipt in postboot.AREA.glob('load.*/closed-timeout.json'):
    attempt=receipt.parent
    assert attempt.resolve().is_relative_to(postboot.AREA)
    row=json.loads(receipt.read_text())
    assert row['passed'] is True and row['game_started'] is False
    assert row['session_analysis_sha256']==postboot.sha(attempt/'analysis.json')
    for name,digest in row['recorded_receipts_sha256'].items():assert postboot.sha(attempt/name)==digest
if (postboot.AREA/'latest-load').exists():
    stage=Path((postboot.AREA/'latest-load').read_text().strip())
    assert stage.resolve().is_relative_to(postboot.AREA)
    report=json.loads((stage/'analysis.json').read_text());assert report['passed'] is True
    assert report['observation_sha256']==postboot.sha(observed/'observation.json')
    for name in ['technical-analysis.json','physical-observation.json','final-audit.json']:
        row=json.loads((stage/name).read_text());assert row['passed'] is True
        if name!='final-audit.json':assert row['session_analysis_sha256']==postboot.sha(stage/'analysis.json')
        for source,digest in row.get('source_sha256',{}).items():assert postboot.sha(repo/source)==digest
    postboot.proof('resident-boot-session')
import phase4_launch_profile as profile
profile.qualified();profile.session.proof('launch-profile')
profile_stage=Path((profile.AREA/'latest-complete').read_text().strip())
assert profile_stage.resolve().is_relative_to(profile.AREA)
profile_report=json.loads((profile_stage/'analysis.json').read_text())
assert profile_report['passed'] is True and profile_report['schema']==117
assert profile_report['metrics']==profile.metrics((profile_stage/'profile.stdout').read_text())
for source,digest in profile_report['source_sha256'].items():assert profile.sha(repo/source)==digest
profile_checks=Path((profile.AREA/'latest-checks').read_text().strip())
assert profile_checks.resolve().is_relative_to(profile.AREA)
assert profile.sha(profile_checks/'analysis.json')==profile_report['checks_analysis_sha256']
for label in ['before','mounts-before','allocate','prepare','validate','profile','validate-after','after','mounts-after','cleanup','post-cleanup-health']:
    assert (profile_stage/(label+'.exit')).read_text()=='0\n'
    for ext in ['sh','stdout','stderr']:(profile_stage/(label+'.'+ext)).read_bytes()
import phase4_batch_validation as batch
batch.qualified();batch.session.proof('batch-validation')
batch_stage=Path((batch.AREA/'latest-complete').read_text().strip())
assert batch_stage.resolve().is_relative_to(batch.AREA)
batch_report=json.loads((batch_stage/'analysis.json').read_text())
assert batch_report['passed'] is True and batch_report['schema']==118
assert batch_report['metrics']==batch.metrics((batch_stage/'profile.stdout').read_text())
for source,digest in batch_report['source_sha256'].items():assert batch.sha(repo/source)==digest
batch_checks=Path((batch.AREA/'latest-checks').read_text().strip())
assert batch_checks.resolve().is_relative_to(batch.AREA)
assert batch.sha(batch_checks/'analysis.json')==batch_report['checks_analysis_sha256']
for kind,digest in batch_report['prototype_sha256'].items():
    assert batch.sha(batch_checks/(kind+'.sh'))==digest
    assert batch.hashlib.sha256(batch.rendered(kind).encode()).hexdigest()==digest
for label in ['before','mounts-before','allocate','prepare','prototype','validate','profile','validate-after','after','mounts-after','cleanup','post-cleanup-health']:
    assert (batch_stage/(label+'.exit')).read_text()=='0\n'
    for ext in ['sh','stdout','stderr']:(batch_stage/(label+'.'+ext)).read_bytes()
os.stat=oldstat;os.lstat=oldlstat
# Failed open probes (including CPython cache and temporary-name probes)
# are not retained artifacts. Keep only existing inputs for a stable closure.
print(json.dumps({'read_paths':sorted(n for n in reads if (repo/n).is_file()),
                  'metadata_paths':sorted(n for n in metadata if (repo/n).exists())}))
