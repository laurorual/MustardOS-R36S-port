#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Read-only dependency trace for the current C104-C111 offline setup."""
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
os.stat=oldstat;os.lstat=oldlstat
# Failed open probes (including CPython cache and temporary-name probes)
# are not retained artifacts. Keep only existing inputs for a stable closure.
print(json.dumps({'read_paths':sorted(n for n in reads if (repo/n).is_file()),
                  'metadata_paths':sorted(n for n in metadata if (repo/n).exists())}))
