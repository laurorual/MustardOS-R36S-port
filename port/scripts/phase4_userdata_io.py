# SPDX-License-Identifier: MIT
"""Bounded I/O primitives for a future guarded offline adapter, no device discovery.

This module has no CLI. A caller must authenticate and exclusively open media,
check mount/swap/holders, and verify its independent backup before calling it.
An error after a write attempt means visibility/durability may be uncertain.
Recovery is a separate explicit operation, never an automatic default/reset.
"""
import fcntl,hashlib,os,stat

SLOT=slice(478,494)

def flush_block_aliases(aliases):
    """Caller has identified an idle card; partition aliases precede whole disk."""
    flushed=[]
    for path,expected in aliases:
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:
            s=os.fstat(fd)
            if not stat.S_ISBLK(s.st_mode) or s.st_rdev!=expected:raise ValueError('Block alias identity mismatch')
            os.fsync(fd);fcntl.ioctl(fd,0x1261,0) # BLKFLSBUF, sync/invalidate this alias.
            flushed.append(str(path))
        finally:os.close(fd)
    return flushed

class CommitError(OSError):
    def __init__(self,phase,cause):
        super().__init__('MBR commit failed at '+phase+'; readback and recovery required')
        self.phase=phase;self.may_have_changed=True;self.cause=cause

def validate_delta(before,after):
    if len(before)!=512 or len(after)!=512 or before[510:]!=b'\x55\xaa':
        raise ValueError('Expected complete DOS MBR sectors')
    if before[:478]!=after[:478] or before[494:]!=after[494:]:
        raise ValueError('Only the p3 slot may change')

def read_exact(fd,size,offset=0):
    result=bytearray()
    while len(result)<size:
        part=os.pread(fd,size-len(result),offset+len(result))
        if not part:raise OSError('Short media read')
        result.extend(part)
    return bytes(result)

def commit_mbr(fd,before,after):
    validate_delta(before,after)
    if read_exact(fd,512)!=before:raise ValueError('Media MBR changed before commit')
    phase='write'
    try:
        done=0
        while done<512:
            n=os.pwrite(fd,after[done:],done)
            if n<=0:raise OSError('Short media write')
            done+=n
        phase='fsync';os.fsync(fd)
        phase='readback'
        if read_exact(fd,512)!=after:raise OSError('MBR readback differs')
    except OSError as error:raise CommitError(phase,error) from error

def restore_mbr_slot(fd,backed_up_before,planned_after):
    validate_delta(backed_up_before,planned_after)
    current=read_exact(fd,512)
    # A partial p3 slot is recoverable only if every protected byte still agrees.
    validate_delta(backed_up_before,current)
    if current==backed_up_before:return
    commit_mbr(fd,current,backed_up_before)

def canonical_prefix_sha256(fd,size,before):
    if size<512 or len(before)!=512:raise ValueError('Expected full prefix and MBR')
    # Normalize only the planned slot; hash every protected byte from the media.
    current=bytearray(read_exact(fd,512));validate_delta(before,current)
    current[SLOT]=before[SLOT];digest=hashlib.sha256(current)
    for offset in range(512,size,1024*1024):
        digest.update(read_exact(fd,min(1024*1024,size-offset),offset))
    return digest.hexdigest()

def compare_metadata_change(fd,backup_fd,size,before,allowed_ranges):
    """Hash the entire canonical prefix, rejecting every unplanned changed byte.

    Used only for the separately approved root-directory permission correction.
    allowed_ranges are absolute, end-exclusive inode/superblock metadata fields;
    the p3 MBR slot is normalized independently. No filesystem data is exempted.
    """
    if size<512 or read_exact(backup_fd,512)!=before:raise ValueError('Wrong recovery prefix')
    if any(start<512 or end<=start or end>size for start,end in allowed_ranges):
        raise ValueError('Invalid metadata change bounds')
    digest=hashlib.sha256();changed=[]
    for offset in range(0,size,1024*1024):
        n=min(1024*1024,size-offset)
        current=bytearray(read_exact(fd,n,offset));original=read_exact(backup_fd,n,offset)
        if not offset:
            validate_delta(before,current[:512]);current[SLOT]=before[SLOT]
        digest.update(current)
        if current==original:continue
        for index,(left,right) in enumerate(zip(current,original)):
            if left==right:continue
            position=offset+index
            if not any(start<=position<end for start,end in allowed_ranges):
                raise ValueError('Unplanned protected byte changed at '+str(position))
            changed.append(position)
            if len(changed)>4096:raise ValueError('Too many metadata changes')
    return {'sha256':digest.hexdigest(),'changed_offsets':changed,'changed_bytes':len(changed)}
