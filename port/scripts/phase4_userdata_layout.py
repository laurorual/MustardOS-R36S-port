#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Pure C20 MBR planning. Reads regular survey files, never opens block devices."""
from pathlib import Path
import argparse,hashlib,json,stat,struct

SECTORS=249872384
P3_START=1310720
DISK_ID=0x4d554432
P1=(0x80,0x0c,32768,204800)
P2=(0,0x83,262144,1048576)
ENTRY=struct.Struct('<B3sB3sII')

def decode(mbr):
    if len(mbr)!=512 or mbr[510:]!=b'\x55\xaa':raise ValueError('Not a 512-byte DOS MBR')
    if struct.unpack_from('<I',mbr,440)[0]!=DISK_ID:raise ValueError('Unexpected disk signature')
    records=[]
    for n in range(4):
        flags,_,kind,_,start,size=ENTRY.unpack_from(mbr,446+16*n)
        records.append((flags,kind,start,size))
    if records[0]!=P1 or records[1]!=P2:raise ValueError('Existing FAT/root geometry or type changed')
    if mbr[478:510]!=bytes(32):raise ValueError('Third/fourth partition slot is not empty')
    return records

def propose(mbr,inventory):
    decode(mbr)
    expected={'mmcblk0_SIZE':str(SECTORS),'LOGICAL_SECTOR':'512',
              'mmcblk0p1_START':str(P1[2]),'mmcblk0p1_SIZE':str(P1[3]),
              'mmcblk0p2_START':str(P2[2]),'mmcblk0p2_SIZE':str(P2[3]),
              'ROOT_PARTUUID':'4d554432-02'}
    for key,value in expected.items():
        if inventory.get(key)!=value:raise ValueError('Survey disagrees with MBR: '+key)
    digest=inventory.get('PREFIX16M_SHA256','')
    if len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):raise ValueError('Missing boot-prefix identity')
    if P3_START!=P2[2]+P2[3] or P3_START%2048:raise ValueError('Unaligned or overlapping data start')
    end=(SECTORS//2048)*2048
    size=end-P3_START
    if size<=0 or size>=2**32:raise ValueError('Unsupported DOS data size')
    proposed=bytearray(mbr)
    ENTRY.pack_into(proposed,478,0,b'\xfe\xff\xff',0x83,b'\xfe\xff\xff',P3_START,size)
    if proposed[:478]!=mbr[:478] or proposed[494:]!=mbr[494:]:raise ValueError('Non-p3 MBR bytes changed')
    return bytes(proposed),{
        'schema':1,'status':'reviewable offline plan only; no block writer or formatter enabled',
        'execution_enabled':False,'capacity_sectors_512':SECTORS,'disk_id':'4d554432',
        'protected_original_card_cid_sha256':'9b4fc38015ae4a049ecd796ceceb2ef9473f4773c9b3a066ce59b567c516bbef',
        'test_card_cid_sha256':'12d2c78fbc14993fe2f8a00c413a5e3ef8d9659a3eba9a41a77b5c37029aa193',
        'boot_prefix_16MiB_sha256':digest,'existing_root_partuuid':'4d554432-02',
        'new_partition':{'index':3,'type':'83','start_sector':P3_START,'sectors':size,
                         'end_sector_inclusive':end-1,'partuuid':'4d554432-03',
                         'planned_filesystem':'ext4','planned_label':'MUOSDATA',
                         'planned_uuid':'6d756f73-c020-4000-8000-000000000001'},
        'mbr_change_range':{'first_byte_inclusive':478,'last_byte_inclusive':493},
        'preserved':'all other MBR bytes, disk-id, p1/p2 entries, boot prefix and both existing filesystems',
        'offline_prefix_backup_bytes':P3_START*512,
        'offline_prerequisites':[
            'controlled shutdown and test128 in a host reader; original32 remains stored away',
            'identify entire test device by capacity, complete MBR, 16MiB prefix and CID when reader exposes it',
            'refuse any mounted child, swap, holder or root/host device; exclusive block open required',
            'make verified private backup of the current first640MiB outside the test card; it contains secrets',
            'read-only offline filesystem checks before modifications; do not repair silently',
            'prepare and test a narrowly bounded writer, formatter and recovery against regular image fixtures',
            'MBR update only at approved p3 slot, fsync/readback and p1/p2/prefix preservation checks',
            'format only verified new p3 with kernel4.4-compatible features, then offline fsck and marker',
            'record final UUID, geometry, features and mount identity for an opt-in platform adapter'
        ],
        'recovery':'restore only saved MBR p3 slot before data use, or verified private prefix if necessary; never touch original32',
        'native_persistence_or_runtime_integration_approved':False
    }

def regular(path):
    if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):raise ValueError('Expected a regular survey file')
    return path.read_bytes()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('survey',type=Path);args=p.parse_args()
    repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/preferences';survey=args.survey.resolve()
    if not survey.is_relative_to(area):raise ValueError('Expected private survey under build/phase4/preferences')
    mbr=regular(survey/'mbr.before');inventory=json.loads(regular(survey/'inventory.json'))
    proposed,plan=propose(mbr,inventory)
    for name in ['mbr.proposed','userdata-plan.json']:
        if (survey/name).exists():raise ValueError('Do not overwrite an existing plan')
    sha=lambda data:hashlib.sha256(data).hexdigest()
    plan.update({'mbr_before_sha256':sha(mbr),'mbr_proposed_sha256':sha(proposed),
                 'planner_sha256':sha(Path(__file__).read_bytes()),'survey_boot_sequence':inventory['BOOT_SEQ']})
    (survey/'mbr.proposed').write_bytes(proposed)
    (survey/'userdata-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(plan['new_partition'],indent=2));print('Plan only; no card writes:',survey)

if __name__=='__main__':main()
