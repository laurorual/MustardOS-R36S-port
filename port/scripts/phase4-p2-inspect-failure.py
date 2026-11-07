#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Finite C87 partial-fixture audit. No media open, ioctl or fixture restart."""
from pathlib import Path
import errno,hashlib,json,os,platform,pwd,re,shutil,stat,sys,tempfile

def need(ok,message):
    if not ok:raise ValueError(message)

def inspect(request):
    need(os.geteuid()==0 and platform.machine()=='x86_64','Local Deck sudo required')
    need(Path('/sys/class/dmi/id/product_name').read_text().strip() in ('Jupiter','Galileo'),'Deck required')
    r=json.loads(Path(request).read_text());root=Path(r['snapshot']);partial=Path(r['partial'])
    need(re.fullmatch(r'/run/muos-r35s-c87\.[a-z0-9_]{8}',str(root)) and
        re.fullmatch(r'/var/tmp/muos-r35s-c87-qualify\.[a-z0-9_]{8}',str(partial)),'Bounded paths')
    for path in [root,partial]:
        s=path.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o700,'Partial owner/mode')
    need({p.name for p in root.iterdir()}==set(r['snapshot_files']),'Snapshot inventory')
    for n,h in r['snapshot_files'].items():
        need('/' not in n,'Snapshot leaf name');p=root/n;s=p.lstat()
        need(stat.S_ISREG(s.st_mode) and s.st_uid==0 and s.st_nlink==1 and s.st_size<=1024*1024
            and stat.S_IMODE(s.st_mode)==0o400 and hashlib.sha256(p.read_bytes()).hexdigest()==h,'Snapshot hash/identity')
    inventory=[]
    for p in partial.rglob('*'):
        rel=str(p.relative_to(partial));s=p.lstat()
        need(rel in {'loop.raw','source.ext4','success','short-write','success/unlock-intent.json',
            'success/write-intent.json','success/complete.json','short-write/unlock-intent.json',
            'short-write/write-intent.json','short-write/complete.json'},'Unknown partial artifact')
        need(s.st_uid==0 and (stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode) and s.st_nlink==1),'Partial type/owner')
        row={'name':rel,'bytes':s.st_size,'mode':stat.S_IMODE(s.st_mode),'directory':stat.S_ISDIR(s.st_mode)}
        if p.suffix=='.json':
            need(s.st_size<=65536,'Bounded journal');row['journal']=json.loads(p.read_text())
        inventory.append(row)
    loops=[]
    for p in Path('/sys/class/block').glob('loop*/loop/backing_file'):
        if str(partial) in p.read_text():loops.append(p.parent.parent.name)
    need(not loops,'Fixture loop still attached; do not cleanup')
    for proc in Path('/proc').glob('[0-9]*/mountinfo'):
        try:lines=proc.read_text().splitlines()
        except OSError as e:
            if e.errno in (errno.ENOENT,errno.ESRCH,errno.EINVAL):continue
            raise
        need(not any(line.split()[4].startswith(str(root)+'/') or line.split()[4].startswith(str(partial)+'/') for line in lines),'Partial mount remains')
    # Probe exactly the fd enumeration used by the controller. No contents,
    # cmdlines, environment or private process file names are copied.
    failures=[];inspected=0
    for process in Path('/proc').glob('[0-9]*'):
        try:
            for leaf in (process/'fd').iterdir():
                try:leaf.stat();inspected+=1
                except OSError as e:
                    if e.errno in (errno.ENOENT,errno.ESRCH):continue
                    failures.append({'proc_fd':str(leaf),'errno':e.errno,'error_type':type(e).__name__})
        except OSError as e:
            if e.errno in (errno.ENOENT,errno.ESRCH):continue
            failures.append({'proc_fd':str(process/'fd'),'errno':e.errno,'error_type':type(e).__name__})
    status={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in Path('/proc/self/status').read_text().splitlines() if line.startswith(('Cap','NoNewPrivs:','Seccomp:'))}
    out=Path(tempfile.mkdtemp(prefix='muos-r35s-c87-failure-audit.',dir='/var/tmp'));out.chmod(0o700)
    report={'passed':True,'partial_inventory':inventory,'proc_fd_inspected':inspected,'proc_fd_errors':failures,
        'process_capabilities':status,'loops_remaining':loops,'card_opened_or_written':False,
        'fixture_retried':False,'partial_retained':True,'sealed_snapshot_verified_and_removed':True}
    leaf=out/'analysis.json'
    with leaf.open('x') as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    # The verified old code snapshot is no longer running or mounted. Retain
    # the partial images/journals, never remove uncertain media/device data.
    for proc in Path('/proc').glob('[0-9]*/cmdline'):
        try:data=proc.read_bytes()
        except OSError as e:
            if e.errno in (errno.ENOENT,errno.ESRCH):continue
            raise
        need(str(root).encode() not in data,'Old helper still running')
    shutil.rmtree(root)
    account=pwd.getpwnam('deck')
    for p in partial.rglob('*'):
        p.chmod(0o700 if p.is_dir() else 0o400);os.chown(p,account.pw_uid,account.pw_gid)
    os.chown(partial,account.pw_uid,account.pw_gid)
    leaf.chmod(0o400);os.chown(leaf,account.pw_uid,account.pw_gid);os.chown(out,account.pw_uid,account.pw_gid)
    for p in [out,partial,Path('/var/tmp')]:
        fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:os.fsync(fd)
        finally:os.close(fd)
    print('C87 FAILURE AUDIT COMPLETE '+str(out),flush=True)

if __name__=='__main__':
    os.umask(0o077)
    need(len(sys.argv)==2,'One private inspection request required')
    inspect(sys.argv[1])
