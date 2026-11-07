#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Read-only dependency trace for the current C104/C105/C106 offline setup."""
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
