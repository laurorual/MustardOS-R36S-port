# SPDX-License-Identifier: MIT
"""C87 bounded write primitive. No device open, RO unlock or physical entrypoint.

The future controller must supply guarded descriptors, real backup/image
validation and durable journal/protection callbacks. This primitive alone
does not authenticate receipts or qualify a candidate for physical writing.
"""
import hashlib,os
from phase4_root_migration import ROOT_OFFSET,ROOT_BYTES,require,digest

CHUNK=1024*1024

def region_hash(fd,start,size,pread):
    h=hashlib.sha256()
    for position in range(0,size,CHUNK):
        count=min(CHUNK,size-position);data=pread(fd,count,start+position)
        require(type(data) is bytes and len(data)==count,'Short bounded source read')
        h.update(data)
    return h.hexdigest()

def write_p2(source,target,source_sha256,current_sha256,*,pread=os.pread,pwrite=os.pwrite,
             fsync=os.fsync,preflight,record_intent,record_complete,restore_readonly,verify_protected):
    """Exact p2 only, one pwrite per chunk, never retry a short/failed write.

    record_intent must durably mark possible partial write BEFORE the first
    pwrite, and reject reuse. restore_readonly must fail closed on every exit,
    including intent/sync/readback failure. No rollback or seed handling here.
    No operation is allowed outside [128MiB,640MiB) on target.
    """
    digest(source_sha256);digest(current_sha256)
    require(type(source) is int and type(target) is int and source>=0 and target>=0 and source!=target,'Distinct guarded descriptors')
    try:
        preflight() # future controller: CID, geometry, size/type, RO transition, backups.
        require(region_hash(source,0,ROOT_BYTES,pread)==source_sha256,'Candidate source hash')
        require(region_hash(target,ROOT_OFFSET,ROOT_BYTES,pread)==current_sha256,'Current p2 hash changed')
        verify_protected()
        record_intent({'kind':'P2_WRITE_MAY_HAVE_STARTED','offset':ROOT_OFFSET,'bytes':ROOT_BYTES,
            'source_sha256':source_sha256,'previous_sha256':current_sha256})
        streamed=hashlib.sha256()
        for position in range(0,ROOT_BYTES,CHUNK):
            count=min(CHUNK,ROOT_BYTES-position)
            data=pread(source,count,position)
            require(type(data) is bytes and len(data)==count,'Source changed/short during write')
            streamed.update(data)
            # Never loop to complete a short write: the target may be partial.
            require(pwrite(target,data,ROOT_OFFSET+position)==count,'Short p2 write; keep partial state')
        fsync(target)
        require(streamed.hexdigest()==source_sha256 and region_hash(source,0,ROOT_BYTES,pread)==source_sha256,'Source changed during write')
        require(region_hash(target,ROOT_OFFSET,ROOT_BYTES,pread)==source_sha256,'P2 readback differs')
        verify_protected()
    finally:
        restore_readonly()
    # An error restoring protection cannot produce a completed receipt.
    record_complete({'kind':'P2_WRITE_VERIFIED','offset':ROOT_OFFSET,'bytes':ROOT_BYTES,'sha256':source_sha256})
    return {'passed':True,'written_bytes':ROOT_BYTES,'offset':ROOT_OFFSET,'readonly_restore_completed':True,
        'automatic_rollback':False,'boot_handoff_authorized':False}
