#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Read-only Steam Deck card preflight. No writes, unmounts, or formatting."""
from pathlib import Path
import argparse,hashlib,json,os,platform,shutil,stat,struct,subprocess

TEST_CID='12d2c78fbc14993fe2f8a00c413a5e3ef8d9659a3eba9a41a77b5c37029aa193'
DECK_TEST_CID='ddf407810b45ae7713ff682a9bb08985a725defe1d007455cd44b4187c39ee04'
ORIGINAL_CID='9b4fc38015ae4a049ecd796ceceb2ef9473f4773c9b3a066ce59b567c516bbef'
CAPACITY=249872384

def text(path):return path.read_text().strip()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan-directory',type=Path)
    a=p.parse_args()
    report={'read_only':True,'euid':os.geteuid(),'architecture':platform.machine(),
            'kernel':platform.release(),'dmi_product':None,'tools':{},'cards':[]}
    dmi=Path('/sys/class/dmi/id/product_name')
    if dmi.is_file():report['dmi_product']=text(dmi)
    for tool in ['python3','findmnt','lsblk','blockdev','sfdisk','mke2fs','e2fsck','blkid','unshare','mount','umount','udevadm']:
        report['tools'][tool]=shutil.which(tool)
    report['global_mount_namespace']=os.readlink('/proc/1/ns/mnt') if os.geteuid()==0 else None
    report['mounts']=subprocess.check_output(['findmnt','-J','-o','SOURCE,TARGET,FSTYPE,OPTIONS,MAJ:MIN'],text=True)
    report['blocks']=subprocess.check_output(['lsblk','-J','-b','-o','NAME,TYPE,SIZE,FSTYPE,LABEL,UUID,PARTUUID,MOUNTPOINTS,RO,MAJ:MIN'],text=True)
    for path in sorted(Path('/sys/class/block').glob('mmcblk*')):
        if not (path/'device/cid').is_file():continue
        cid_hash=hashlib.sha256(text(path/'device/cid').lower().encode()).hexdigest()
        card={'name':path.name,'cid_sha256':cid_hash,'sectors':text(path/'size'),
              'protected_original':cid_hash==ORIGINAL_CID,'test_card':cid_hash in (TEST_CID,DECK_TEST_CID)}
        report['cards'].append(card)
    if a.plan_directory:
        assert os.geteuid()==0,'Root required to compare raw card identity'
        directory=a.plan_directory
        plan=json.loads((directory/'userdata-plan.json').read_text())
        before=(directory/'mbr.before').read_bytes()
        assert len(before)==512 and hashlib.sha256(before).hexdigest()==plan['mbr_before_sha256']
        assert not any(c['protected_original'] for c in report['cards']),'Original32 must stay stored away'
        selected=[c for c in report['cards'] if c['test_card']]
        assert len(selected)==1 and int(selected[0]['sectors'])==CAPACITY,'Test128 identity missing'
        name=selected[0]['name'];sys=Path('/sys/class/block')/name;device=Path('/dev')/name
        assert platform.machine()=='x86_64' and report['dmi_product'] in ('Jupiter','Galileo'),'Expected Steam Deck offline station'
        assert text(sys/'queue/logical_block_size')=='512'
        assert not device.is_symlink()
        fd=os.open(device,os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW)
        try:
            s=os.fstat(fd);assert stat.S_ISBLK(s.st_mode)
            assert f'{os.major(s.st_rdev)}:{os.minor(s.st_rdev)}'==text(sys/'dev')
            assert os.pread(fd,512,0)==before,'MBR changed since live survey'
            digest=hashlib.sha256()
            for offset in range(0,16*1024*1024,1024*1024):
                block=os.pread(fd,1024*1024,offset);assert len(block)==1024*1024
                digest.update(block)
            assert digest.hexdigest()==plan['boot_prefix_16MiB_sha256'],'Boot prefix changed'
        finally:os.close(fd)
        report['test_card_raw_identity_matches_plan']=True
        report['device']=str(device)
        report['holders']={p.name:[v.name for v in (p/'holders').iterdir()]
                           for p in [sys,*sys.glob(name+'p*')] if (p/'holders').is_dir()}
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
