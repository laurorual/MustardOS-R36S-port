# SPDX-License-Identifier: MIT
"""C89 recovery eligibility from scans and a fixed test128 target adapter.

Neither JSON receipts nor flags authorize writing. The finite controller must
derive the scans from guarded descriptors and tie the observed image to p2.
"""
from pathlib import Path
import os
from phase4_root_migration import require,CAPACITY,ROOT_BYTES
import phase4_root_recovery as recovery
import phase4_recovery_image as image
from phase4_p2_controller import Controller,Journal

def eligibility(base,observed,candidate,backup_prefix_sha256,attempt,capture_context,observed_sha256,image_bytes):
    rows=base['private_files'];counter=base['boot_sequence']
    recovery.manifest(rows,counter,True)
    observation=image.observation(observed,attempt,capture_context,observed_sha256,image_bytes)
    plan=recovery.recovery_plan(rows,counter,backup_prefix_sha256,attempt,observation)
    require(image.public_tree(base)==image.public_tree(candidate),'Recovery public tree/metadata changed')
    expected=set(base['payloads'])-{recovery.CREDIT,recovery.NO_CREDIT}
    expected.add(recovery.NO_CREDIT)
    require(set(candidate['payloads'])==expected and recovery.CREDIT not in candidate['private_files'],'Recovery seed inventory')
    require(candidate['boot_sequence']==plan['recovery_counter']
        and candidate['payloads'][recovery.COUNTER]==f"{plan['recovery_counter']}\n".encode(),'Recovery counter differs from fresh capture')
    for name in recovery.STABLE&set(base['payloads']):
        require(candidate['payloads'].get(name)==base['payloads'][name]
            and candidate['private_files'].get(name)==rows[name],'Stable recovery identity changed')
    seed=candidate['payloads'][recovery.NO_CREDIT]
    require(type(seed) is bytes and len(seed)==256 and recovery.hashed(seed) not in plan['old_seed_sha256'],'Fresh 256-byte no-credit seed required')
    expected_attrs={n:v for n,v in base['attrs'].items() if n not in (recovery.CREDIT,recovery.NO_CREDIT)}
    expected_attrs[recovery.NO_CREDIT]=base['attrs'].get(recovery.NO_CREDIT,base['attrs'].get(recovery.CREDIT,{}))
    require(candidate['attrs']==expected_attrs,'Recovery private xattrs changed')
    recovery.manifest(candidate['private_files'],candidate['boot_sequence'])
    return plan

def validate_fd(source,backup,backup_sha256,current,current_sha256,image_bytes,stage,backup_rows,backup_counter,
                backup_prefix_sha256,attempt,capture_context,backup_root_mode=0o777):
    """Callback body for Controller.apply: all eligibility comes from FD scans."""
    image.private_stage(stage)
    with image.source_image(backup,backup_sha256,image_bytes) as fd:base=image.scan(fd,stage,backup_root_mode)
    require(base['private_files']==backup_rows and base['boot_sequence']==backup_counter,'Backup binding changed')
    with image.source_image(current,current_sha256,image_bytes) as fd:observed=image.scan(fd,stage)
    candidate=image.scan(source,stage)
    return eligibility(base,observed,candidate,backup_prefix_sha256,attempt,capture_context,current_sha256,image_bytes)

def card_target(guard,capture,context,journal):
    """Only the exact three-partition test128 guarded by C82/C86; no CLI path."""
    require(os.geteuid()==0,'Local Deck root required for card target')
    def identity():capture.read_protection(guard,context)
    identity()
    journal=Path(journal)
    row=guard.run(['findmnt','-rn','-T',str(journal),'-o','FSTYPE,MAJ:MIN']).stdout.split()
    require(len(row)==2 and row[0] in ('ext4','btrfs') and row[1] not in guard.numbers(),'Persistent off-card write journal required')
    aliases=[]
    for name,size in [('mmcblk0',CAPACITY*512),('mmcblk0p1',100*1024*1024),
        ('mmcblk0p2',ROOT_BYTES),('mmcblk0p3',248561664*512)]:
        node=guard.SYS/name
        require(int((node/'size').read_text())*512==size,'Fixed card alias dimensions')
        major,minor=map(int,(node/'dev').read_text().strip().split(':'))
        aliases.append((Path('/dev')/name,os.makedev(major,minor),size))
    return Controller(aliases,identity,CAPACITY*512,Journal(journal))
