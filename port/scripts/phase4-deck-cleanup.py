#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C101 finite project cleanup on an empty Steam Deck reader. No media IO."""
from pathlib import Path
import hashlib,json,os,platform,pwd,re,shutil,stat,sys

BASES=('/home/deck','/var/tmp','/tmp','/run')
RULE=Path('/run/udev/rules.d/99-holo-automount.rules')
RULE_SHA='a30d6a856b4a5d3b67e907d44ddb7bf852811316117b65f7509204f011d4ff60'
RECEIPT=Path('/home/deck/.muos-r35s-c101-cleanup-result.json')
CLAIM=Path('/run/muos-r35s-c101-cleanup.claim')


def require(value,message):
    if not value:raise ValueError(message)


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_paths(rows,deck_uid):
    names=set()
    for row in rows:
        p=Path(row['path'])
        require(str(p)==row['path'] and str(p.parent) in BASES and
            re.fullmatch(r'muos-r35s-c[0-9]+(?:[-.][a-zA-Z0-9_.-]+)?',p.name), 'Outside finite project scope')
        require(str(p) not in names,'Duplicate project root');names.add(str(p))
        require(row['kind']=='directory' and row['uid'] in (0,deck_uid) and row['mode']==0o700,
            'Unexpected root type, owner or mode')
    require(0<len(rows)<=100,'Finite nonempty cleanup plan')
    return names


def card_absent():
    require(not list(Path('/sys/class/block').glob('mmcblk*')),'Remove cards before Deck cleanup')


def namespaces_clear(paths):
    def underneath(value):return any(value==p or value.startswith(p+'/') for p in paths)
    for file in Path('/proc').glob('[0-9]*/mountinfo'):
        try:lines=file.read_text().splitlines()
        except (FileNotFoundError,ProcessLookupError):continue
        for line in lines:
            fields=line.split();require(len(fields)>=6,'Mountinfo schema')
            target=fields[4]
            for escaped,char in [('\\040',' '),('\\011','\t'),('\\012','\n'),('\\134','\\')]:target=target.replace(escaped,char)
            require(not underneath(target),'Project root still mounted in a namespace')
    for file in Path('/sys/class/block').glob('loop*/loop/backing_file'):
        require(not underneath(file.read_text().strip()),'Project image still attached to a loop device')
    # Only reject executing task entrypoints, not shell history or text in an
    # inspection command. Include our sudo ancestors in the allowed chain.
    ancestors={os.getpid()};pid=os.getppid()
    while pid>1 and pid not in ancestors:
        ancestors.add(pid)
        try:pid=int((Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()[1])
        except (FileNotFoundError,ProcessLookupError):break
    for file in Path('/proc').glob('[0-9]*/cmdline'):
        if int(file.parent.name) in ancestors:continue
        try:args=file.read_bytes().split(b'\0')
        except (FileNotFoundError,ProcessLookupError):continue
        require(not any(underneath(os.fsdecode(arg)) for arg in args if arg.startswith(b'/')),
            'Another project command is running')


def discover(excluded):
    return {str(p) for base in BASES for p in Path(base).glob('muos-r35s-*') if str(p) not in excluded}


def check_roots(rows):
    identities={};allocated=0
    for row in rows:
        p=Path(row['path']);s=p.lstat()
        require(stat.S_ISDIR(s.st_mode) and s.st_uid==row['uid'] and stat.S_IMODE(s.st_mode)==row['mode'],
            'Project root changed before cleanup')
        identities[str(p)]=(s.st_dev,s.st_ino)
        for parent,dirs,files in os.walk(p,followlinks=False):
            for n in [*dirs,*files]:
                f=Path(parent)/n;t=f.lstat()
                require(stat.S_ISDIR(t.st_mode) or stat.S_ISREG(t.st_mode) or stat.S_ISLNK(t.st_mode),
                    'Special file inside cleanup root')
                allocated+=t.st_blocks*512
    return identities,allocated


def erase(rows,identities):
    require(shutil.rmtree.avoids_symlink_attacks,'FD-based directory removal required')
    for row in rows:
        p=Path(row['path']);s=p.lstat()
        require((s.st_dev,s.st_ino)==identities[str(p)] and stat.S_ISDIR(s.st_mode),'Root replaced during cleanup')
        shutil.rmtree(p)


def main():
    os.umask(0o077);require(os.geteuid()==0,'Run locally with sudo on the Deck')
    require(platform.machine()=='x86_64' and Path('/sys/class/dmi/id/product_name').read_text().strip() in ('Jupiter','Galileo'),
        'Steam Deck host required')
    me=Path(__file__).absolute();package=me.parent
    require(package.parent==Path('/home/deck') and re.fullmatch(r'muos-r35s-c101-cleanup-[0-9a-f]{12}',package.name),
        'Finite cleanup package')
    plan_path=package/'cleanup-plan.json';plan=json.loads(plan_path.read_text());plan_sha=digest(plan_path);deck=pwd.getpwnam('deck')
    require(plan['schema']==101 and plan['host_retention_verified'] is True and
        digest(me)==plan['helper_sha256'] and set(p.name for p in package.iterdir())=={me.name,plan_path.name},
        'Verified cleanup package and independent host retention required')
    names=validate_paths(plan['paths'],deck.pw_uid)
    require(not RECEIPT.exists() and not RECEIPT.is_symlink(),'Existing cleanup receipt needs inspection')
    fd=os.open(CLAIM,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600);os.close(fd)
    excluded={str(package),str(CLAIM)}
    card_absent();require(discover(excluded)==names,'Project roots changed since inspection')
    namespaces_clear([*names,str(package)])
    if RULE.exists() or RULE.is_symlink():
        require(RULE.is_file() and not RULE.is_symlink() and digest(RULE)==RULE_SHA,'Foreign automount rule; preserve it')
    rows=plan['paths']+[{'path':str(package),'uid':deck.pw_uid,'mode':0o700,'kind':'directory'}]
    identities,allocated=check_roots(rows)
    card_absent();namespaces_clear([*names,str(package)])
    erase(rows,identities)
    card_absent()
    removed_rule=False
    if RULE.exists():
        require(not RULE.is_symlink() and digest(RULE)==RULE_SHA,'Automount rule changed')
        RULE.unlink();removed_rule=True
    CLAIM.unlink()
    require(not discover(set()),'Project files remain after cleanup')
    receipt={'passed':True,'schema':101,'project_directories_removed':len(rows),'paths_removed':sorted([*names,str(package)]),
        'allocated_bytes_in_removed_files':allocated,'reader_empty_verified':True,'all_mount_namespaces_checked':True,
        'project_loop_devices_absent':True,'temporary_project_automount_rule_removed':removed_rule,
        'host_retention_verified':True,'host_retention_sha256':plan['host_retention_sha256'],'cleanup_plan_sha256':plan_sha,
        'key_removal_and_receipt_collection_pending':True,'sshd_service_changed':False,'card_opened_or_written':False}
    fd=os.open(RECEIPT,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as stream:
        json.dump(receipt,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
        os.fchown(stream.fileno(),deck.pw_uid,deck.pw_gid);os.fchmod(stream.fileno(),0o400)
    directory=os.open(RECEIPT.parent,os.O_RDONLY|os.O_DIRECTORY);os.fsync(directory);os.close(directory)
    print('C101 CLEANUP COMPLETE',flush=True)


if __name__=='__main__':
    try:main()
    except Exception as error:
        print('C101 FAILED ('+type(error).__name__+'): preserve receipt/claim and inspect; do not repeat',flush=True)
        raise
