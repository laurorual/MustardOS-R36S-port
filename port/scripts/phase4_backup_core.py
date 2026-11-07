# SPDX-License-Identifier: MIT
"""C81 backup-only IO/metadata routines. Media descriptors are read only."""
from pathlib import Path
import fcntl, hashlib, io, json, os, re, stat, tarfile
from phase4_root_migration import PRIVATE_FILES, OPTIONAL_PRIVATE, private_manifest, require, digest

CHUNK=1024*1024

def validate_source_root_policy(value):
    require(type(value) is dict and set(value)=={'reason','p2_mode','p3_mode','automount_script_sha256','diagnostic_root_sha256'},'Source root policy schema')
    require(value['reason']=='SteamOS_automount_chmod777' and type(value['p2_mode']) is int and type(value['p3_mode']) is int and value['p2_mode']==value['p3_mode']==0o777,'Source root policy scope')
    digest(value['automount_script_sha256']);digest(value['diagnostic_root_sha256'])
    return value

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def sync_dir(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)

def write_new(path,data):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f:
        f.write(data);f.flush();os.fsync(f.fileno())
    sync_dir(path.parent)

def read_exact(fd,n,offset):
    data=bytearray()
    while len(data)<n:
        block=os.pread(fd,n-len(data),offset+len(data))
        require(bool(block),'Short source read');data.extend(block)
    return bytes(data)

def region_sha(fd,offset,size):
    h=hashlib.sha256()
    for i in range(0,size,CHUNK):h.update(read_exact(fd,min(CHUNK,size-i),offset+i))
    return h.hexdigest()

def copy_region(fd,offset,size,path):
    require(type(offset) is int and type(size) is int and offset>=0 and size>0,'Copy bounds')
    # O_EXCL means an existing host file, symlink or device cannot be a target.
    out=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    h=hashlib.sha256()
    try:
        for i in range(0,size,CHUNK):
            data=read_exact(fd,min(CHUNK,size-i),offset+i);h.update(data)
            view=memoryview(data)
            while view:
                count=os.write(out,view);require(count>0,'Short backup write');view=view[count:]
        os.fsync(out)
    finally:os.close(out)
    sync_dir(path.parent)
    require(path.stat().st_size==size and path.stat().st_nlink==1,'Backup size/link count')
    require(sha(path)==h.hexdigest()==region_sha(fd,offset,size),'Backup/source readback differs')
    return h.hexdigest()

def flush_block_aliases(aliases):
    # Read-only C20 primitive, kept separate from its historical write functions.
    flushed=[]
    for path,expected in aliases:
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:
            s=os.fstat(fd)
            if not stat.S_ISBLK(s.st_mode) or s.st_rdev!=expected:raise ValueError('Block alias identity mismatch')
            os.fsync(fd);fcntl.ioctl(fd,0x1261,0) # BLKFLSBUF, only identified idle aliases.
            flushed.append(str(path))
        finally:os.close(fd)
    return flushed

def parse_stat(text):
    match=re.search(r'Inode:\s+\d+\s+Type:\s+(\w+)\s+Mode:\s+([0-7]+)',text)
    owner=re.search(r'User:\s+(\d+)\s+Group:\s+(\d+)',text)
    size=re.search(r'\bSize:\s+(\d+)',text);links=re.search(r'\bLinks:\s+(\d+)',text)
    require(all([match,owner,size,links]),'Unreadable debugfs inode')
    return {'type':match[1],'mode':int(match[2],8),'uid':int(owner[1]),'gid':int(owner[2]),'links':int(links[1]),'bytes':int(size[1])}

def listing(text):
    names=[]
    for line in text.splitlines():
        if not line.strip():continue
        fields=line.split('/')
        require(len(fields)==8 and fields[0]==fields[-1]=='','Unreadable debugfs directory')
        if fields[1]=='0' and not fields[5]:continue
        name=fields[5]
        if name in ('.','..'):continue
        require(re.fullmatch('[A-Za-z0-9_.-]+',name) and name not in names,'Unexpected directory member')
        names.append(name)
    return names

def extract_private(root_image,stage,plan,run,source_root_mode=0o755):
    require(type(source_root_mode) is int and source_root_mode in (0o755,0o777),'Source root mode')
    def debug(command):return run(['debugfs','-R',command,str(root_image)]).stdout
    for name,mode in [('/',source_root_mode),('/etc',0o755),('/var',0o755),('/var/lib',0o755),
        ('/var/lib/muos-network',0o700),('/var/lib/muos-seedrng',0o700),('/var/lib/muos-diagnostic',0o700)]:
        row=parse_stat(debug('stat '+name))
        require(row['type']=='directory' and row['uid']==row['gid']==0 and row['mode']==mode,'Private parent alias/owner/mode')
    members={'etc/muos-network-authorized_key','var/lib/muos-diagnostic/boot-seq'}
    for directory in ['var/lib/muos-network','var/lib/muos-seedrng']:
        members.update(directory+'/'+n for n in listing(debug('ls -p /'+directory)))
    require(PRIVATE_FILES<=members<=PRIVATE_FILES|OPTIONAL_PRIVATE,'Unknown/missing private file')
    rows={};paths={}
    for index,name in enumerate(sorted(members)):
        row=parse_stat(debug('stat /'+name));require(row.pop('type')=='regular','Private leaf alias')
        require(0<row['bytes']<=65536 and row['links']==1,'Private file size/link count')
        path=stage/('private-%02d.dat'%index)
        require(not path.exists() and not path.is_symlink(),'Private dump target already exists')
        run(['debugfs','-R',f'dump /{name} {path}',str(root_image)])
        require(not path.is_symlink() and path.is_file() and path.stat().st_nlink==1 and path.stat().st_size==row['bytes'],'Private dump')
        path.chmod(0o600)
        with path.open('rb') as f:os.fsync(f.fileno())
        row['sha256']=sha(path);rows[name]=row;paths[name]=path.name
    private_manifest(rows)
    stable=lambda r:{n:v for n,v in r.items() if not n.startswith('var/lib/muos-seedrng/') and n!='var/lib/muos-diagnostic/boot-seq'}
    require(stable(rows)==stable(plan['private_files_at_live_survey']),'Private network/key identity changed')
    counter='var/lib/muos-diagnostic/boot-seq'
    require((stage/paths[counter]).read_bytes()==f"{plan['survey_boot_sequence']}\n".encode(),'Boot changed; new survey required')
    require(rows[counter]==plan['private_files_at_live_survey'][counter],'Counter metadata changed')
    sync_dir(stage)
    return {'files':rows,'artifacts':paths,'fresh_offline_seed_used':True,'seed_loaded':False,'key_generated':False,'source_root_mode':source_root_mode}

MARKERS={'.muos-r35s-data-v1':b'MUOS-R35S-DATA-V1\n',
 'MUOS/preferences/.muos-preferences-v1':b'MUOS-R35S-PREFS-V1\n',
 'MUOS/port-saves-v1/.muos-save-root-v1':b'MUOS-R35S-SAVE-ROOT-V1\n'}

def userdata_snapshot(root,source_root_mode=0o755):
    """Capture only markers/preferences/saves, through no-follow directory FDs."""
    require(type(source_root_mode) is int and source_root_mode in (0o755,0o777),'Source data root mode')
    records={};contents={};total=0
    rootfd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    device=os.fstat(rootfd).st_dev
    def capture(parent,name,relative,depth=0):
        nonlocal total
        require(depth<=12 and len(records)<2048 and re.fullmatch('[A-Za-z0-9_.-]+',name) and name not in ('.','..'),'Userdata bounds/name')
        info=os.stat(name,dir_fd=parent,follow_symlinks=False)
        require(info.st_dev==device and info.st_uid==info.st_gid==0,'Userdata owner/device')
        if stat.S_ISDIR(info.st_mode):
            require(stat.S_IMODE(info.st_mode)==0o700,'Userdata directory mode')
            fd=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent)
            try:
                opened=os.fstat(fd);require((opened.st_dev,opened.st_ino)==(info.st_dev,info.st_ino),'Userdata directory changed')
                records[relative]={'type':'directory','mode':0o700}
                for child in sorted(os.listdir(fd)):capture(fd,child,relative+'/'+child,depth+1)
            finally:os.close(fd)
        else:
            require(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and stat.S_IMODE(info.st_mode)==0o600,'Userdata leaf link/type/mode')
            require(0<=info.st_size<=32*1024*1024 and total+info.st_size<=64*1024*1024,'Userdata size bound')
            fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=parent)
            try:
                before=os.fstat(fd);require((before.st_dev,before.st_ino,before.st_size)==(info.st_dev,info.st_ino,info.st_size),'Userdata changed before open')
                data=read_exact(fd,info.st_size,0)
                require(os.pread(fd,1,info.st_size)==b'','Userdata grew')
                after=os.fstat(fd)
                require((before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'Userdata changed during read')
            finally:os.close(fd)
            total+=len(data);contents[relative]=data
            records[relative]={'type':'file','mode':0o600,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    try:
        info=os.fstat(rootfd);require(info.st_uid==info.st_gid==0 and stat.S_IMODE(info.st_mode)==source_root_mode,'Data root ownership/mode')
        capture(rootfd,'.muos-r35s-data-v1','.muos-r35s-data-v1')
        muos=os.open('MUOS',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=rootfd)
        try:
            info=os.fstat(muos);require(info.st_uid==info.st_gid==0 and info.st_dev==device and stat.S_IMODE(info.st_mode) in (0o700,0o755),'MUOS parent')
            for name in ['preferences','port-saves-v1']:capture(muos,name,'MUOS/'+name)
        finally:os.close(muos)
    finally:os.close(rootfd)
    for name,data in MARKERS.items():require(contents.get(name)==data,'Missing/invalid userdata marker')
    return records,contents

def verify_userdata_archive(archive,records):
    actual={};markers={};total=0
    require(archive.stat().st_size<=68*1024*1024,'Archive size bound')
    with tarfile.open(archive,'r:') as tar:
        for member in tar:
            name=member.name
            require(len(actual)<2048 and name not in actual and member.uid==member.gid==0,'Duplicate archive/owner/count')
            require(all(re.fullmatch('[A-Za-z0-9_.-]+',v) and v not in ('.','..') for v in name.split('/')),'Archive path')
            require(name=='.muos-r35s-data-v1' or any(name==p or name.startswith(p+'/') for p in ['MUOS/preferences','MUOS/port-saves-v1']),'Archive scope')
            if member.isdir():
                require(member.mode==0o700,'Archive directory mode');row={'type':'directory','mode':member.mode}
            else:
                require(member.isfile() and member.mode==0o600 and member.size<=32*1024*1024,'Archive leaf type/mode/size')
                total+=member.size;require(total<=64*1024*1024,'Archive payload bound')
                stream=tar.extractfile(member);h=hashlib.sha256();data=b''
                while True:
                    block=stream.read(CHUNK)
                    if not block:break
                    h.update(block)
                    if name in MARKERS:data+=block;require(len(data)<=256,'Archive marker size')
                if name in MARKERS:markers[name]=data
                row={'type':'file','mode':member.mode,'bytes':member.size,'sha256':h.hexdigest()}
            actual[name]=row
    require(actual==records and markers==MARKERS,'Archive readback/markers differ')

def backup_userdata(root,archive,source_root_mode=0o755):
    records,contents=userdata_snapshot(root,source_root_mode)
    with archive.open('xb') as stream:
        with tarfile.open(fileobj=stream,mode='w',format=tarfile.USTAR_FORMAT) as tar:
            for name,row in sorted(records.items()):
                entry=tarfile.TarInfo(name);entry.mode=row['mode'];entry.uid=entry.gid=0;entry.mtime=0
                if row['type']=='directory':entry.type=tarfile.DIRTYPE;tar.addfile(entry)
                else:entry.size=row['bytes'];tar.addfile(entry,io.BytesIO(contents[name]))
        stream.flush();os.fsync(stream.fileno())
    require(userdata_snapshot(root,source_root_mode)[0]==records,'Userdata changed across backup')
    verify_userdata_archive(archive,records)
    sync_dir(archive.parent)
    return {'records':records,'sha256':sha(archive),'file_count':sum(v['type']=='file' for v in records.values()),'archive_verified':True,'source_root_mode':source_root_mode}
