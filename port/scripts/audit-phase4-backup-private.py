#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C82 diagnose a regular-file partial backup. Never open or mount a device."""
from pathlib import Path
import hashlib,json,os,platform,pwd,re,shutil,stat,subprocess,sys,tempfile

ALLOWED={'audit-phase4-backup-private.py','phase4_backup_core.py','phase4_root_migration.py','migration-plan.json'}
SAFE_ERRORS={'Unreadable debugfs inode','Private parent alias/owner/mode','Unreadable debugfs directory',
 'Unexpected directory member','Unknown/missing private file','Private leaf alias','Private file size/link count',
 'Private dump target already exists','Private dump','Private network/key identity changed',
 'Boot changed; new survey required','Counter metadata changed','Missing or unexpected private path',
 'Private metadata schema','Private metadata types','Private file ownership/mode/link count','Private file size','Seed length'}

def need(ok,message):
    if not ok:raise ValueError(message)

def partial_path(value):
    need(re.fullmatch(r'/var/tmp/muos-r35s-c81-backup\.[a-z0-9_]{8}',str(value)) is not None,'Partial path')
    return Path(value)

def snapshot_package(source,destination):
    manifest=json.loads((source/'package.json').read_text())
    need(set(manifest['files'])==ALLOWED and manifest['diagnostic_only'] is True,'Audit package')
    for name,digest in manifest['files'].items():
        fd=os.open(source/name,os.O_RDONLY|os.O_NOFOLLOW)
        try:
            before=os.fstat(fd)
            need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=1024*1024 and not before.st_mode&0o022,'Unsafe audit source')
            data=os.read(fd,before.st_size+1);after=os.fstat(fd)
            need((before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'Audit source changed')
            need(len(data)==before.st_size and hashlib.sha256(data).hexdigest()==digest,'Audit source hash')
            fd2=os.open(destination/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o400)
            with os.fdopen(fd2,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        finally:os.close(fd)

def probe(partial,plan,core,run,temporary):
    result={'experiment':'C82_PARTIAL_BACKUP_DIAGNOSTIC','diagnostic_only':True,
            'device_opened':False,'backup_qualified':False,'seed_loaded':False,'plan_boot':plan['survey_boot_sequence']}
    result['partial_files']={}
    for p in sorted(partial.iterdir()):
        need(p.name in {'prefix.backup','boot.fat','root.ext4','private-files.json','userdata.tar','userdata-manifest.json','backup.json'} or re.fullmatch(r'private-[0-9]{2}\.dat',p.name),'Unexpected partial leaf')
        info=p.lstat();need(stat.S_ISREG(info.st_mode) and info.st_nlink==1,'Partial leaf type/link')
        result['partial_files'][p.name]={'bytes':info.st_size,'mode':stat.S_IMODE(info.st_mode)}
    root=partial/'root.ext4'
    need(root.is_file() and root.stat().st_size==512*1024*1024,'Incomplete root copy')
    result['parents']={}
    for name in ['/','/etc','/var','/var/lib','/var/lib/muos-network','/var/lib/muos-seedrng','/var/lib/muos-diagnostic']:
        result['parents'][name]=core.parse_stat(run(['debugfs','-R','stat '+name,str(root)]).stdout)
    row=core.parse_stat(run(['debugfs','-R','stat /var/lib/muos-diagnostic/boot-seq',str(root)]).stdout)
    need(row['type']=='regular' and row['links']==1 and 2<=row['bytes']<=5 and row['uid']==row['gid']==0 and row['mode']==0o600,'Unsafe counter inode')
    text=run(['debugfs','-R','cat /var/lib/muos-diagnostic/boot-seq',str(root)]).stdout
    need(re.fullmatch(r'[1-9][0-9]{0,3}\n',text),'Counter encoding')
    result['offline_boot']=int(text);result['same_boot']=int(text)==plan['survey_boot_sequence']
    try:
        core.extract_private(root,temporary,plan,run)
    except ValueError as error:
        result['private_extraction_passed']=False
        result['refusal']=str(error) if str(error) in SAFE_ERRORS else 'unclassified private validation error'
    else:
        result['private_extraction_passed']=True;result['refusal']=None
    return result

def main():
    need(os.geteuid()==0,'Local sudo required')
    need(platform.machine()=='x86_64' and Path('/sys/class/dmi/id/product_name').read_text().strip() in ('Jupiter','Galileo'),'Deck only')
    need(len(sys.argv)==2,'Expected partial backup path');partial=partial_path(sys.argv[1])
    info=partial.lstat();need(stat.S_ISDIR(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700,'Root-owned partial directory')
    source=Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix='muos-r35s-c82-audit.',dir='/run') as rootname:
        root=Path(rootname);root.chmod(0o700);snapshot_package(source,root)
        sys.dont_write_bytecode=True;sys.path.insert(0,str(root))
        import phase4_backup_core as core
        plan=json.loads((root/'migration-plan.json').read_text())
        need(plan['execution_enabled'] is False and plan['device_writer_available'] is False,'Disabled writer plan required')
        private=root/'probe';private.mkdir(mode=0o700)
        def run(args):
            need(args[0]=='debugfs' and args[1]=='-R' and args[-1]==str(partial/'root.ext4'),'Only backup-image debugfs allowed')
            need(not args[2].startswith(('write','set','rm','mkdir')),'Read-only debugfs command required')
            r=subprocess.run(args,capture_output=True,text=True,stdin=subprocess.DEVNULL,timeout=45,
                             env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LC_ALL':'C'})
            need(r.returncode==0,'Read-only debugfs failed');return r
        result=probe(partial,plan,core,run,private)
    account=pwd.getpwnam('deck');out=Path(tempfile.mkdtemp(prefix='muos-r35s-c82-audit-result.',dir='/var/tmp'));out.chmod(0o700)
    p=out/'analysis.json'
    fd=os.open(partial/'root.ext4',os.O_RDONLY|os.O_NOFOLLOW)
    try:
        info=os.fstat(fd);need(stat.S_ISREG(info.st_mode) and info.st_nlink==1,'Unsafe partial root')
        result['diagnostic_root_copy_sha256']=core.copy_region(fd,0,512*1024*1024,out/'root.ext4')
    finally:os.close(fd)
    copy=out/'root.ext4';copy.chmod(0o400);os.chown(copy,account.pw_uid,account.pw_gid)
    with p.open('xb') as f:f.write((json.dumps(result,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    p.chmod(0o400);os.chown(p,account.pw_uid,account.pw_gid);os.chown(out,account.pw_uid,account.pw_gid)
    print(json.dumps({'diagnostic_complete':True,'report':str(p),'refusal':result['refusal'],
        'plan_boot':result['plan_boot'],'offline_boot':result['offline_boot'],'diagnostic_root_copy':str(copy)},indent=2))

if __name__=='__main__':
    os.umask(0o077)
    try:main()
    except Exception as e:
        print('C82 audit failed ('+type(e).__name__+'); no device IO requested.',file=sys.stderr);sys.exit(1)
