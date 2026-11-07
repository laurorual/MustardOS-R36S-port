# SPDX-License-Identifier: MIT
"""C84 offline recovery policy/payloads. No media, mounts, network or init IO."""
from pathlib import Path
import hashlib,json,os,re,stat
from phase4_root_migration import CAPACITY,DECK_CID,PRIVATE_FILES,OPTIONAL_PRIVATE,require,digest

CREDIT='var/lib/muos-seedrng/seed.credit'
NO_CREDIT='var/lib/muos-seedrng/seed.no-credit'
COUNTER='var/lib/muos-diagnostic/boot-seq'
STABLE=(PRIVATE_FILES|OPTIONAL_PRIVATE)-{CREDIT,NO_CREDIT,COUNTER}

def hashed(data):return hashlib.sha256(data).hexdigest()
def encoded(value):return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()

def sequence(value):
    require(type(value) is int and 1<=value<=9998,'Counter out of qualified range')
    return value

def manifest(rows,counter,credit_required=False):
    sequence(counter)
    required=PRIVATE_FILES if credit_required else PRIVATE_FILES-{CREDIT}
    require(type(rows) is dict and required<=set(rows)<=PRIVATE_FILES|OPTIONAL_PRIVATE,'Private members missing/unknown')
    for name,row in rows.items():
        require(type(row) is dict and set(row)=={'sha256','mode','uid','gid','links','bytes'},'Private metadata schema')
        digest(row['sha256'])
        require(all(type(row[k]) is int for k in ['mode','uid','gid','links','bytes']),'Private metadata types')
        mode=0o400 if name in (CREDIT,NO_CREDIT) else 0o644 if name=='etc/muos-network-authorized_key' else 0o600
        require(row['mode']==mode and row['uid']==row['gid']==0 and row['links']==1,'Private metadata owner/mode/links')
        require(0<row['bytes']<=65536 and (name not in (CREDIT,NO_CREDIT) or 32<=row['bytes']<=256),'Private size')
    data=f'{counter}\n'.encode()
    require(rows[COUNTER]['sha256']==hashed(data) and rows[COUNTER]['bytes']==len(data),'Counter bytes/hash mismatch')
    return rows

def attempt_record(backup_rows,backup_counter,backup_prefix_sha256,candidate_sha256,candidate_counter,attempt_id):
    """Conservative handoff intent, persisted BEFORE media leaves offline custody.

    A controller must compute arguments from verified descriptors/copies. This
    dict is neither authentication nor permission to execute a device write.
    No API exists to clear the possible-boot flag after loss of network.
    """
    manifest(backup_rows,backup_counter,True);sequence(candidate_counter)
    require(candidate_counter>=backup_counter,'Candidate counter rewind')
    require(type(attempt_id) is str and re.fullmatch('[0-9a-f]{32}',attempt_id),'Attempt ID')
    digest(backup_prefix_sha256);digest(candidate_sha256)
    return {'schema':84,'kind':'BOOT_MAY_HAVE_OCCURRED','attempt_id':attempt_id,
        'backup_prefix_sha256':backup_prefix_sha256,'backup_counter':backup_counter,
        'candidate_root_sha256':candidate_sha256,'counter_floor':candidate_counter,
        'backup_private_manifest_sha256':hashed(encoded(backup_rows)),
        'boot_may_have_occurred':True,'automatic_rollback':False,'execution_enabled':False}

def checked_attempt(value,backup_rows,backup_counter,backup_prefix_sha256):
    require(type(value) is dict and set(value)=={'schema','kind','attempt_id','backup_prefix_sha256',
        'backup_counter','candidate_root_sha256','counter_floor','backup_private_manifest_sha256',
        'boot_may_have_occurred','automatic_rollback','execution_enabled'},'Attempt record schema')
    expected=attempt_record(backup_rows,backup_counter,backup_prefix_sha256,
        value['candidate_root_sha256'],value['counter_floor'],value['attempt_id'])
    require(value==expected,'Attempt record schema/binding changed')
    return expected

def recovery_plan(backup_rows,backup_counter,backup_prefix_sha256,attempt,observed):
    checked_attempt(attempt,backup_rows,backup_counter,backup_prefix_sha256)
    keys={'attempt_id','offline','cid_sha256','capacity_sectors','root_fsck_exit','root_mode',
          'root_sha256','private_files','boot_sequence','captured_after_handoff'}
    require(type(observed) is dict and set(observed)==keys,'Fresh observation schema')
    require(observed['offline'] is True and observed['captured_after_handoff'] is True,'Fresh offline capture after handoff required')
    require(observed['attempt_id']==attempt['attempt_id'] and observed['cid_sha256']==DECK_CID,'Attempt/card binding')
    require(type(observed['capacity_sectors']) is int and observed['capacity_sectors']==CAPACITY,'Card capacity')
    require(type(observed['root_fsck_exit']) is int and observed['root_fsck_exit']==0,'Dirty/unreadable source: no counter assumption')
    require(type(observed['root_mode']) is int and observed['root_mode']==0o755,'Unqualified source root mode')
    digest(observed['root_sha256']);rows=manifest(observed['private_files'],observed['boot_sequence'])
    require({n:r for n,r in rows.items() if n in STABLE}=={n:r for n,r in backup_rows.items() if n in STABLE},'Network/key identity changed')
    require(observed['boot_sequence']>=attempt['counter_floor'],'Counter below handoff floor')
    high=max(backup_counter,attempt['counter_floor'],observed['boot_sequence'])
    target=sequence(high+1) # reserve one unused value; C07 increments again at boot.
    return {'schema':84,'kind':'OFFLINE_POSTBOOT_RECOVERY_PAYLOAD_PLAN',
        'attempt_sha256':hashed(encoded(attempt)),'attempt_id':attempt['attempt_id'],
        'backup_prefix_sha256':backup_prefix_sha256,'observed_root_sha256':observed['root_sha256'],
        'observed_private_manifest_sha256':hashed(encoded(rows)),
        'confirmed_counter_high_water':high,'recovery_counter':target,'next_C07_counter':target+1,
        'target_root_mode':0o755,'target_private_directory_mode':0o700,
        'remove_seed_paths':[CREDIT,NO_CREDIT],'new_seed_path':NO_CREDIT,'new_seed_bytes':256,
        'new_seed_entropy_credit_allowed':False,'seed_loaded':False,'key_generation_allowed':False,
        'stable_private_files':{n:r for n,r in backup_rows.items() if n in STABLE},
        'old_seed_sha256':sorted({r['sha256'] for source in (backup_rows,rows) for n,r in source.items() if n in (CREDIT,NO_CREDIT)}),
        'execution_enabled':False,'device_writer_available':False,'automatic_rollback':False,
        'p1_mbr_p3_write_allowed':False,'byte_exact_p2_restore_allowed':False}

def compose_payload(plan,stable_payloads,rng=os.getrandom):
    """Return private bytes for a future regular-image composer; never load RNG.

    The host RNG must ALREADY be ready. EAGAIN, ENOSYS, EINTR or short results
    abort without fallback/retry. Only fresh no-credit seed is staged.
    """
    require(plan['kind']=='OFFLINE_POSTBOOT_RECOVERY_PAYLOAD_PLAN' and all(plan[k] is False for k in
        ['execution_enabled','device_writer_available','new_seed_entropy_credit_allowed','seed_loaded',
         'key_generation_allowed','automatic_rollback','p1_mbr_p3_write_allowed','byte_exact_p2_restore_allowed']),'Offline plan required')
    require(plan['target_root_mode']==0o755 and plan['target_private_directory_mode']==0o700,'Target root/private modes')
    require(set(stable_payloads)==set(plan['stable_private_files'])<=STABLE,'Stable payload inventory')
    for n,data in stable_payloads.items():
        row=plan['stable_private_files'][n]
        require(type(data) is bytes and len(data)==row['bytes'] and hashed(data)==row['sha256'],'Stable payload hash/size')
    require(plan['new_seed_path']==NO_CREDIT and plan['new_seed_bytes']==256 and plan['remove_seed_paths']==[CREDIT,NO_CREDIT],'No-credit replacement policy')
    target=sequence(plan['recovery_counter'])
    require(type(plan['confirmed_counter_high_water']) is int and target==plan['confirmed_counter_high_water']+1 and plan['next_C07_counter']==target+1,'Counter reservation')
    old=plan['old_seed_sha256'];require(type(old) is list and bool(old) and old==sorted(set(old)),'Known old seed hashes')
    for h in old:digest(h)
    seed=rng(256,os.GRND_NONBLOCK)
    require(type(seed) is bytes and len(seed)==256,'Host RNG short response')
    require(hashed(seed) not in plan['old_seed_sha256'],'Host RNG returned old seed')
    return {**stable_payloads,COUNTER:f'{target}\n'.encode(),NO_CREDIT:seed}

def seal_attempt(parent,record):
    """Persist an immutable-by-convention off-card handoff fence, no media IO.

    Fixed exclusive leaf, fsync(file)+fsync(directory). Existing/partial fence
    is retained and rejected, never overwritten or interpreted as cancelled.
    Return is the only success signal for a future manual-handoff controller.
    """
    require(record['kind']=='BOOT_MAY_HAVE_OCCURRED' and record['boot_may_have_occurred'] is True
        and record['automatic_rollback'] is False and record['execution_enabled'] is False,'Conservative intent required')
    name=record['attempt_id'];require(type(name) is str and re.fullmatch('[0-9a-f]{32}',name),'Attempt ID')
    parent=Path(parent)
    fd=os.open(parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        s=os.fstat(fd);require(s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700,'Private journal directory')
        leaf=name+'.json';out=os.open(leaf,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o400,dir_fd=fd)
        with os.fdopen(out,'wb') as f:f.write(encoded(record));f.flush();os.fsync(f.fileno())
        os.fsync(fd)
    finally:os.close(fd)
    return parent/leaf

def load_attempt(parent,attempt_id,expected_sha256):
    """Read a pinned sealed fence; a receipt/hash is not device authorization."""
    require(type(attempt_id) is str and re.fullmatch('[0-9a-f]{32}',attempt_id),'Attempt ID')
    digest(expected_sha256);fd=os.open(parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        s=os.fstat(fd);require(s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700,'Private journal directory')
        source=os.open(attempt_id+'.json',os.O_RDONLY|os.O_NOFOLLOW,dir_fd=fd)
        try:
            before=os.fstat(source)
            require(stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and before.st_nlink==1
                and stat.S_IMODE(before.st_mode)==0o400 and 0<before.st_size<=65536,'Sealed fence file')
            data=os.read(source,before.st_size+1);after=os.fstat(source)
            require((before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==
                (after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'Fence changed during read')
            require(len(data)==before.st_size and hashed(data)==expected_sha256,'Fence hash/length')
            record=json.loads(data)
            require(record['attempt_id']==attempt_id and encoded(record)==data,'Fence ID/canonical encoding')
            return record
        finally:os.close(source)
    finally:os.close(fd)
