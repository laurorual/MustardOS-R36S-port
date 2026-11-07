# SPDX-License-Identifier: MIT
"""C83 pure ext4 inode2 sector planner. No discovery, device opening or writer."""
import hashlib,re,struct
from phase4_root_migration import require

def crc32c(seed,data):
    """Raw reflected Castagnoli CRC; no final complement (ext4 convention)."""
    value=seed
    for byte in data:
        value^=byte
        for _ in range(8):value=(value>>1)^ (0x82f63b78 if value&1 else 0)
    return value&0xffffffff

def runtime_automount_rule(original,cid,expected_cid_hash):
    require(type(original) is bytes and b'LABEL="holo_automount_end"' in original,'Automount label required')
    require(type(cid) is str and re.fullmatch('[0-9a-f]{32}',cid) and hashlib.sha256(cid.encode()).hexdigest()==expected_cid_hash,'Exact guard CID')
    prefix=('# C83 temporary exact-card guard; remove after card transfer.\nKERNEL=="mmcblk0|mmcblk0p[123]", ATTRS{cid}=="'+cid+'", ENV{UDISKS_IGNORE}="1", GOTO="holo_automount_end"\n').encode()
    return prefix+original

def geometry(sb,gd,partition_start,partition_bytes):
    require(type(sb) is bytes and len(sb)==1024 and type(gd) is bytes and len(gd)==4096,'Metadata capsule dimensions')
    u16=lambda n:struct.unpack_from('<H',sb,n)[0]
    u32=lambda n:struct.unpack_from('<I',sb,n)[0]
    require(type(partition_start) is int and type(partition_bytes) is int and partition_start>=0 and partition_start%512==0 and partition_bytes>0,'Partition bounds')
    require(u16(56)==0xef53 and u16(58)==1 and u32(72)==0 and u32(76)==1,'Clean Linux ext4 required')
    require(u32(24)==2 and u32(20)==0 and u16(88)==256,'Only 4096-byte blocks/256-byte inodes qualified')
    require(u32(4)*4096==partition_bytes and u32(0)>=2,'Filesystem/partition dimensions')
    require(u32(92)==0x3c and u32(96) in (0x42,0x242) and u32(100) in (0x73,0x46b),'Unqualified ext4 feature set')
    require(u16(254) in (0,32),'Only 32-byte group descriptors qualified')
    checksummed=bool(u32(100)&0x400)
    if checksummed:
        require(sb[0x175]==1 and crc32c(0xffffffff,sb[:1020])==u32(1020),'Superblock checksum')
    table=struct.unpack_from('<I',gd,8)[0];relative=table*4096+256
    require(table>=2 and 8192<=relative and relative+256<=partition_bytes,'Inode table range')
    absolute=partition_start+relative;sector=absolute//512*512
    require(absolute-sector==256,'Inode2 must fit wholly in one sector')
    return {'inode_offset':absolute,'sector_offset':sector,'inode_in_sector':256,'checksummed':checksummed,
            'partition_start':partition_start,'partition_bytes':partition_bytes}

def inode_crc(sb,inode):
    require(len(inode)==256 and struct.unpack_from('<H',inode,128)[0]>=4,'Extended inode checksum fields')
    seed=crc32c(0xffffffff,sb[104:120]);seed=crc32c(seed,struct.pack('<I',2));seed=crc32c(seed,inode[100:104])
    data=bytearray(inode);data[124:126]=bytes(2);data[130:132]=bytes(2)
    return crc32c(seed,data)

def sector_patch(sb,gd,sector,partition_start,partition_bytes,expected_mode=0o40777):
    layout=geometry(sb,gd,partition_start,partition_bytes)
    require(type(sector) is bytes and len(sector)==512,'Exact inode sector required')
    inode=sector[256:512];get=lambda n:struct.unpack_from('<H',inode,n)[0]
    require(expected_mode in (0o40777,0o40755) and get(0)==expected_mode,'Unexpected root inode mode')
    require(get(2)==get(24)==get(120)==get(122)==0 and get(26)>=2,'Root inode owner/type/links')
    if layout['checksummed']:
        stored=get(124)|(get(130)<<16);require(stored==inode_crc(sb,inode),'Inode2 checksum')
    updated=bytearray(inode);struct.pack_into('<H',updated,0,0o40755)
    allowed={256,257}
    if layout['checksummed']:
        checksum=inode_crc(sb,updated);struct.pack_into('<H',updated,124,checksum&0xffff);struct.pack_into('<H',updated,130,checksum>>16)
        allowed.update({380,381,386,387})
    after=sector[:256]+bytes(updated)
    changes=[i for i,(old,new) in enumerate(zip(sector,after)) if old!=new]
    require(set(changes)<=allowed and (bool(changes) if expected_mode==0o40777 else not changes),'Sector difference outside mode/checksum')
    return {**layout,'before':sector.hex(),'after':after.hex(),'changed_offsets':changes,
            'before_sha256':hashlib.sha256(sector).hexdigest(),'after_sha256':hashlib.sha256(after).hexdigest()}

def apply_sector(fd,patch,pread,pwrite,fsync):
    """One fixed 512-byte write; callbacks make fault behavior testable."""
    before=bytes.fromhex(patch['before']);after=bytes.fromhex(patch['after']);offset=patch['sector_offset']
    require(type(offset) is int and offset>=0 and offset%512==0 and len(before)==len(after)==512,'Sector write dimensions')
    require(patch['partition_start']+8192<=offset and offset+512<=patch['partition_start']+patch['partition_bytes'],'Sector outside partition inode region')
    require(hashlib.sha256(before).hexdigest()==patch['before_sha256'] and hashlib.sha256(after).hexdigest()==patch['after_sha256'],'Sector patch hashes')
    changes=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b]
    require(changes==patch['changed_offsets'] and bool(changes) and set(changes)<={256,257,380,381,386,387},'Unbounded sector payload')
    require(struct.unpack_from('<H',before,256)[0]==0o40777 and struct.unpack_from('<H',after,256)[0]==0o40755,'Only mode0777 to0755 repair')
    require(pread(fd,512,offset)==before,'Sector changed before write')
    # A short sector write stops. Never loop or roll back automatically.
    require(pwrite(fd,after,offset)==512,'Short sector write; inspect before retry')
    fsync(fd);require(pread(fd,512,offset)==after,'Sector readback differs')
