# SPDX-License-Identifier: MIT
"""C98 offline two-pass transaction prototype, without media/device opener.

No native adapter or privileged CLI is provided. A future qualified adapter
must hold verified control FDs, keep p1/p3 RO throughout, and expose WRITABLE
p2 only (partition-relative offsets), never a writable whole-card payload FD.
Unchanged means full complement hashes before/after, not sampled/free-space
omission. The active C94/C87 implementation is intentionally untouched.
"""
import fcntl,os,stat
from phase4_root_migration import ROOT_BYTES,ROOT_OFFSET,require,digest
from phase4_p2_write_core import CHUNK,region_hash

def signature(s):return s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns

def apply(source,source_sha256,current_sha256,adapter,validate_source,*,
          pread=os.pread,pwrite=os.pwrite,fsync=os.fsync):
    """One pwrite/chunk to p2 at offset0; exactly two full complement scans.

    prepare_readonly: verify CID/geometry/guard/namespaces/RO/foreign FDs and
      retain controls + exclusive read-only whole-card claim.
    protected_hashes: derive both complete complement hashes from that claim.
    partition_writable: after durable unlock-intent, reverify identity/state,
      close read claim and return exclusive verified O_RDWR p2 alias, size512MiB.
    finish_readonly: restore controls on every exit, close p2 claim, flush
      identified aliases and retain a NEW exclusive read-only whole-card claim.
    close: best-effort RO via retained FDs and close everything, even on errors.

    Adapter booleans/receipts are not physical authentication. No production
    adapter is available; loop/MMC claim and boundary behavior need native
    qualification before a future separate finite writer can use this engine.
    """
    digest(source_sha256);digest(current_sha256)
    require(type(source) is int and source>=0,'Guarded source descriptor required')
    s=os.fstat(source)
    require(stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and
        stat.S_IMODE(s.st_mode) in (0o400,0o600) and s.st_size==ROOT_BYTES,'Private source metadata')
    fcntl.flock(source,fcntl.LOCK_EX|fcntl.LOCK_NB)
    def source_check():
        require(signature(os.fstat(source))==signature(s) and
            region_hash(source,0,ROOT_BYTES,pread)==source_sha256,'Source changed')
    try:
        adapter.prepare_readonly();source_check();validate_source(source);source_check()
        require(adapter.current_p2_sha256()==current_sha256,'Current p2 differs from captured source')
        baseline=adapter.protected_hashes()
        require(type(baseline) is list and len(baseline)==2,'Full complement inventory')
        for h in baseline:digest(h)
        adapter.state_readonly()
        adapter.record('unlock-intent',{'kind':'P2_PARTITION_UNLOCK_MAY_HAVE_STARTED','offset':ROOT_OFFSET,'bytes':ROOT_BYTES,
            'source_sha256':source_sha256,'previous_sha256':current_sha256,'protected_sha256':baseline,
            'payload_descriptor_role':'p2-partition','partition_relative_offset':0})
        target=adapter.partition_writable()
        require(type(target) is int and target>=0 and target!=source,'Distinct p2 partition FD')
        # Cheap compared with another 119GiB scan: recheck current p2 through
        # the actual writable partition alias after the claim/unlock gap.
        adapter.state_partition_writable();source_check()
        require(region_hash(target,0,ROOT_BYTES,pread)==current_sha256,'P2 changed before write')
        adapter.record('write-intent',{'kind':'P2_PARTITION_WRITE_MAY_HAVE_STARTED','offset':ROOT_OFFSET,'bytes':ROOT_BYTES,
            'source_sha256':source_sha256,'previous_sha256':current_sha256,
            'payload_descriptor_role':'p2-partition','partition_relative_offset':0})
        import hashlib
        streamed=hashlib.sha256()
        for offset in range(0,ROOT_BYTES,CHUNK):
            count=min(CHUNK,ROOT_BYTES-offset);data=pread(source,count,offset)
            require(type(data) is bytes and len(data)==count,'Short source read')
            streamed.update(data)
            require(pwrite(target,data,offset)==count,'Short partition write; preserve partial state, no retry')
        fsync(target);require(streamed.hexdigest()==source_sha256,'Streamed source changed');source_check()
        adapter.finish_readonly();adapter.state_readonly()
        require(adapter.current_p2_sha256()==source_sha256,'Cold p2 readback differs')
        final=adapter.protected_hashes();require(final==baseline,'Full protected complement changed')
        source_check();adapter.state_readonly()
    finally:adapter.close()
    adapter.record('complete',{'kind':'P2_PARTITION_WRITE_VERIFIED','offset':ROOT_OFFSET,'bytes':ROOT_BYTES,
        'sha256':source_sha256,'protected_complement_verified':True,'cold_p2_readback_verified':True,
        'full_complement_scan_count':2,'payload_descriptor_role':'p2-partition','partition_relative_offset':0,
        'boot_handoff_authorized':False})
    return {'passed':True,'written_bytes':ROOT_BYTES,'full_complement_scan_count':2,
        'automatic_retry_or_rollback':False,'boot_handoff_authorized':False}
