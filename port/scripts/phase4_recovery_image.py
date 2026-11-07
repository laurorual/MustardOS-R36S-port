# SPDX-License-Identifier: MIT
"""C85 regular-ext4 snapshot collector/composer. No mounts or device writer."""
from pathlib import Path
import fcntl,hashlib,json,os,re,stat,subprocess
from contextlib import contextmanager
from phase4_backup_core import parse_stat,sync_dir,write_new
from phase4_root_migration import require,digest,DECK_CID,CAPACITY
import phase4_root_recovery as recovery

PARENTS={'':0o755,'etc':0o755,'var':0o755,'var/lib':0o755,
    'var/lib/muos-network':0o700,'var/lib/muos-seedrng':0o700,'var/lib/muos-diagnostic':0o700}
CHANGED={recovery.CREDIT,recovery.NO_CREDIT,recovery.COUNTER}

def historical_marker(path):
    return path=='var/lib/muos-diagnostic/c12.used' or re.fullmatch(r'var/lib/muos-diagnostic/c25\.used\.BOOT[0-9]{4}',path) is not None

def fd_sha(fd):
    h=hashlib.sha256();offset=0
    while data:=os.pread(fd,1024*1024,offset):h.update(data);offset+=len(data)
    return h.hexdigest()

def signature(info):return (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns,info.st_nlink)

@contextmanager
def source_image(path,expected_sha256,expected_bytes):
    digest(expected_sha256)
    require(type(expected_bytes) is int and expected_bytes in (32*1024*1024,512*1024*1024),'Qualified regular image size')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK)
    try:
        before=os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and before.st_nlink==1
            and stat.S_IMODE(before.st_mode) in (0o400,0o600) and before.st_size==expected_bytes,'Private regular image required')
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        require(fd_sha(fd)==expected_sha256,'Source image hash')
        yield fd
        require(signature(os.fstat(fd))==signature(before) and fd_sha(fd)==expected_sha256,'Source changed during operation')
    finally:os.close(fd)

def command(args,fd,timeout=60):
    p=subprocess.run(args,pass_fds=(fd,),capture_output=True,timeout=timeout,
        env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LC_ALL':'C'},stdin=subprocess.DEVNULL)
    require(p.returncode==0,'Fixed filesystem command failed: '+Path(args[0]).name)
    return p.stdout.decode('utf-8',errors='strict')

def debug(fd,request,writable=False):
    return command(['debugfs',*(['-w'] if writable else []),'-R',request,'/proc/self/fd/'+str(fd)],fd)

def private_stage(path):
    s=path.lstat();require(stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700,'Private stage required')
    # Paths are passed to debugfs's own command parser. Restrict staging paths;
    # public filesystem names are never interpolated into debugfs commands.
    require(re.fullmatch(r'/[A-Za-z0-9_./-]+',str(path)) and '..' not in path.parts,'Unsafe tool path')

def dumped(fd,request,stage,size):
    require(type(size) is int and 0<=size<=512*1024*1024,'Dump size bound')
    leaf=stage/'scratch.dat';require(not leaf.exists() and not leaf.is_symlink(),'Dump target exists')
    debug(fd,request.replace('@OUTPUT@',str(leaf)))
    try:
        out=os.open(leaf,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        try:
            s=os.fstat(out);require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==size,'Incomplete dump')
            os.fchmod(out,0o600);data=os.pread(out,size+1,0);require(len(data)==size,'Short dump')
            return data
        finally:os.close(out)
    finally:
        if leaf.exists() and not leaf.is_symlink():leaf.unlink()

def entries(text):
    answer=[]
    for line in text.splitlines():
        if not line.strip():continue
        fields=line.split('/')
        require(len(fields)==8 and fields[0]==fields[-1]=='','Directory listing syntax')
        if fields[1]=='0' and not fields[5]:continue
        name=fields[5]
        if name in ('.','..'):continue
        require(name and not any(ord(c)<32 or ord(c)==127 for c in name),'Unsupported filesystem name')
        require(re.fullmatch('[0-9]+',fields[1]) and int(fields[1])>0,'Directory inode number')
        require(name not in {n for n,i in answer},'Duplicate directory member')
        answer.append((name,int(fields[1])))
    return answer

def scan(fd,stage,root_mode=0o755):
    private_stage(stage);require(type(root_mode) is int and root_mode in (0o755,0o777),'Root policy')
    command(['e2fsck','-fn','/proc/self/fd/'+str(fd)],fd,180)
    records={};payloads={};attrs={};history={};seen_dirs=set();cache={};budget=0;attribute_budget=0
    def inode(number,keep_data=False):
        nonlocal budget,attribute_budget
        if number in cache:return cache[number]
        text=debug(fd,'stat <'+str(number)+'>')
        info=parse_stat(text.replace('Type: character special','Type: character').replace('Type: block special','Type: block'))
        require(info['type'] in {'regular','directory','symlink','character','block','FIFO'},'Unsupported inode type')
        flags=re.search(r'Flags: (0x[0-9a-f]+)',text);require(flags is not None,'Inode flags')
        record={k:v for k,v in info.items() if k!='bytes'};record['flags']=flags[1]
        acl=re.search(r'^File ACL: ([0-9]+)$',text,re.M);require(acl is not None,'External xattr pointer')
        record['external_xattrs']=int(acl[1])!=0
        xattrs={}
        attr_lines=[]
        if 'Extended attributes:\n' in text:
            for line in text.split('Extended attributes:\n',1)[1].splitlines():
                if not line.startswith('  '):break
                match=re.match(r'^  ([A-Za-z][A-Za-z0-9_.-]*) \(([0-9]+)\)(?: =.*)?$',line)
                require(match is not None,'Unsupported xattr representation');attr_lines.append(match.groups())
        for name,size in attr_lines:
            require(name not in xattrs and int(size)<=65536,'Xattr name/size')
            attribute_budget+=int(size);require(attribute_budget<=16*1024*1024,'Xattr total bound')
            data=dumped(fd,'ea_get -f @OUTPUT@ <'+str(number)+'> '+name,stage,int(size))
            xattrs[name]=data
        require('Extended attributes:' not in text or bool(xattrs),'Unparsed xattrs')
        record['xattrs']={n:recovery.hashed(v) for n,v in xattrs.items()}
        data=None
        if info['type']=='regular':
            require(info['bytes']<=64*1024*1024,'Public file size bound')
            budget+=info['bytes'];require(budget<=768*1024*1024,'Filesystem payload bound')
            data=dumped(fd,'dump <'+str(number)+'> @OUTPUT@',stage,info['bytes'])
            record.update({'bytes':len(data),'sha256':recovery.hashed(data)})
        elif info['type']=='symlink':
            match=re.search(r'^Fast link dest: "(.*)"$',text,re.M)
            data=match[1].encode() if match else dumped(fd,'dump <'+str(number)+'> @OUTPUT@',stage,info['bytes'])
            require(len(data)==info['bytes'] and len(data)<=4096,'Symlink representation')
            record['target_hex']=data.hex()
        elif info['type'] in ('character','block'):
            match=re.search(r'^Device major/minor number: (.+)$',text,re.M)
            require(match is not None,'Special device metadata');record['device']=match[1]
        cache[number]=(record,data if keep_data else None,xattrs);return cache[number]
    def walk(number,path,depth=0):
        require(depth<=32 and len(records)<8192,'Filesystem traversal bound')
        row,data,xattrs=inode(number,path in recovery.PRIVATE_FILES|recovery.OPTIONAL_PRIVATE or historical_marker(path));records[path]=row
        if path in recovery.PRIVATE_FILES|recovery.OPTIONAL_PRIVATE:
            require(row['type']=='regular' and data is not None and len(data)<=65536,'Private leaf type/size')
            payloads[path]=data;attrs[path]=xattrs
        if historical_marker(path):
            require(row['type']=='regular' and row['uid']==row['gid']==0 and row['mode']==0o600 and row['links']==1
                and data is not None and len(data)<=64,'Consumed marker metadata')
            history[path]=data
        if row['type']=='directory':
            require(number not in seen_dirs,'Directory alias/cycle');seen_dirs.add(number)
            for name,child in entries(debug(fd,'ls -p <'+str(number)+'>')):
                target=(path+'/' if path else '')+name
                require(not name.endswith('.once'),'Active runtime token in image')
                if re.fullmatch(r'c(?:12|25)\.used(?:[.].*)?',name):require(historical_marker(target),'Unknown consumed marker location/format')
                walk(child,target,depth+1)
    walk(2,'')
    for name,mode in PARENTS.items():
        row=records.get(name,{})
        require(row.get('type')=='directory' and row['uid']==row['gid']==0 and row['mode']==(root_mode if name=='' else mode),'Private ancestor type/owner/mode')
    for directory in ['var/lib/muos-network','var/lib/muos-seedrng','var/lib/muos-diagnostic']:
        members={n for n in records if n.startswith(directory+'/')}
        require(members<=recovery.PRIVATE_FILES|recovery.OPTIONAL_PRIVATE|set(history),'Unknown private directory entry')
    rows={n:{k:records[n][k] for k in ['sha256','mode','uid','gid','links','bytes']} for n in payloads}
    value=payloads.get(recovery.COUNTER,b'')
    require(re.fullmatch(b'[1-9][0-9]{0,3}\n',value) is not None,'Counter encoding')
    counter=int(value);recovery.manifest(rows,counter)
    for path,data in history.items():
        if path.endswith('/c12.used'):require(data==b'MUOS-C12-ONCE\n','Consumed C12 marker content')
        else:
            boot=int(path[-4:]);require(1<=boot<=counter and data==f'MUOS-C25-ONCE\nBOOT={boot}\n'.encode(),'Consumed C25 marker content/counter')
    return {'private_files':rows,'payloads':payloads,'attrs':attrs,'boot_sequence':counter,
        'tree':records,'root_mode':root_mode,'fsck_exit':0}

def observation(capture,attempt,context,source_sha256,source_bytes):
    expected={'schema','attempt_id','attempt_sha256','root_sha256','root_bytes','cid_sha256',
        'capacity_sectors','offline','all_namespaces_unmounted','alias_cache_synchronized','captured_after_handoff'}
    require(type(context) is dict and set(context)==expected,'Capture context schema')
    require(context['schema']==85 and context['attempt_id']==attempt['attempt_id']
        and context['attempt_sha256']==recovery.hashed(recovery.encoded(attempt)),'Capture handoff binding')
    require(context['root_sha256']==source_sha256 and type(context['root_bytes']) is int and context['root_bytes']==source_bytes,'Capture image binding')
    require(all(context[n] is True for n in ['offline','all_namespaces_unmounted','alias_cache_synchronized','captured_after_handoff']),'Fresh guarded physical capture required')
    require(context['cid_sha256']==DECK_CID and type(context['capacity_sectors']) is int and context['capacity_sectors']==CAPACITY,'Capture card identity')
    return {'attempt_id':attempt['attempt_id'],'offline':True,'captured_after_handoff':True,
        'cid_sha256':DECK_CID,'capacity_sectors':CAPACITY,'root_fsck_exit':capture['fsck_exit'],
        'root_mode':capture['root_mode'],'root_sha256':source_sha256,
        'private_files':capture['private_files'],'boot_sequence':capture['boot_sequence']}

def collect_postboot(image,image_sha256,image_bytes,stage,attempt,context):
    with source_image(image,image_sha256,image_bytes) as fd:captured=scan(fd,stage)
    observed=observation(captured,attempt,context,image_sha256,image_bytes)
    return captured,observed

def public_tree(capture):
    records={n:dict(v) for n,v in capture['tree'].items() if n not in CHANGED}
    records['']['mode']=0o755 # the C82 backup's root0777 is deliberately normalized.
    return records

def sparse_clone(source,output,size):
    offset=0
    while offset<size:
        data=os.pread(source,min(1024*1024,size-offset),offset);require(bool(data),'Short image source')
        if data!=bytes(len(data)):
            require(os.pwrite(output,data,offset)==len(data),'Short regular clone write')
        offset+=len(data)
    os.ftruncate(output,size);os.fsync(output)

def compose(backup,backup_sha256,observed_image,observed_sha256,image_bytes,stage,
            backup_rows,backup_counter,backup_prefix_sha256,attempt,context,backup_root_mode=0o755,rng=os.getrandom):
    """One regular-image composition; context must come from a future IO helper.

    Receipt validation is not authentication. There is no RPC/device operation;
    future physical capture and p2-only writer remain separate prerequisites.
    """
    private_stage(stage)
    with source_image(backup,backup_sha256,image_bytes) as source:
        base=scan(source,stage,backup_root_mode)
        require(base['private_files']==backup_rows and base['boot_sequence']==backup_counter,'Backup private binding')
        require(not any(base['tree'][n]['external_xattrs'] for n in CHANGED if n in base['tree']),
            'External xattrs on replaced private inode are not qualified for debugfs unlink')
        captured,observed=collect_postboot(observed_image,observed_sha256,image_bytes,stage,attempt,context)
        plan=recovery.recovery_plan(backup_rows,backup_counter,backup_prefix_sha256,attempt,observed)
        payload=recovery.compose_payload(plan,{n:data for n,data in base['payloads'].items() if n in recovery.STABLE},rng)
        output=stage/'recovery.ext4'
        fd=os.open(output,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
        try:
            expected_attrs={}
            sparse_clone(source,fd,image_bytes);require(fd_sha(fd)==backup_sha256,'Clone differs')
            debug(fd,'set_inode_field <2> mode 040755',True)
            for name in sorted(CHANGED):
                if name in base['private_files']:
                    # External EA blocks are refused above; do not repair leaks.
                    for attr in base['attrs'].get(name,{}):debug(fd,'ea_rm /'+name+' '+attr,True)
                    debug(fd,'rm /'+name,True)
            for index,name in enumerate([recovery.COUNTER,recovery.NO_CREDIT]):
                leaf=stage/('payload-%02d.dat'%index);write_new(leaf,payload[name])
                debug(fd,'write '+str(leaf)+' /'+name,True)
                mode=0o400 if name==recovery.NO_CREDIT else 0o600
                debug(fd,'set_inode_field /'+name+' mode 0'+format(stat.S_IFREG|mode,'o'),True)
                template=name if name in base['attrs'] else recovery.CREDIT
                expected_attrs[name]=base['attrs'].get(template,{})
                for attr,data in expected_attrs[name].items():
                    asset=stage/'attribute.dat';write_new(asset,data)
                    debug(fd,'ea_set -f '+str(asset)+' /'+name+' '+attr,True);asset.unlink()
                leaf.unlink()
            os.fsync(fd);after=scan(fd,stage)
            require(public_tree(base)==public_tree(after),'Public tree/identity metadata changed')
            require(set(after['payloads'])==set(payload) and all(after['payloads'][n]==v for n,v in payload.items()),'Recovery private readback')
            require(all(after['attrs'][n]==v for n,v in expected_attrs.items()),'Replaced private xattrs changed')
            require(after['boot_sequence']==plan['recovery_counter'] and recovery.CREDIT not in after['private_files'],'Recovery counter/seed')
            image_sha256=fd_sha(fd)
            require(image_sha256!=backup_sha256,'Unchanged recovery image')
        finally:os.close(fd)
        sync_dir(stage)
    result={'passed':True,'schema':85,'root_image_sha256':image_sha256,'root_image_bytes':image_bytes,
        'source_images_unchanged':True,'public_tree_and_stable_identity_unchanged':True,'root_fsck_exit':0,
        'recovery_counter':plan['recovery_counter'],'new_seed_path':recovery.NO_CREDIT,
        'old_seeds_removed':True,'fresh_no_credit_seed_verified':True,'seed_loaded':False,
        'device_writer_available':False,'physical_capture_backend_available':False,'reboot_requested':False}
    write_new(stage/'plan.json',(json.dumps(plan,indent=2)+'\n').encode())
    write_new(stage/'analysis.json',(json.dumps(result,indent=2)+'\n').encode())
    return result
