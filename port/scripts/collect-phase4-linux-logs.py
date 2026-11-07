#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Read diagnostic logs after returning to stock OS; never mount the test FAT rw."""
from pathlib import Path
import hashlib
import argparse
import json
import os
import platform
import re
import subprocess
import sys
import tempfile

def command(args):
    r=subprocess.run(args,text=True,capture_output=True)
    return {'exit_code':r.returncode,'stdout':r.stdout.strip(),'stderr':r.stderr.strip()}

def cid(card):
    return hashlib.sha256(Path('/sys/block',card,'device/cid').read_text().strip().lower().encode()).hexdigest()

assert os.geteuid()==0
parser=argparse.ArgumentParser()
parser.add_argument('--experiment',choices=['A01','B01','C01','C02','C03','C04','C05','C06','C07'],default='A01')
parser.add_argument('--private-mounts',action='store_true')
args=parser.parse_args()
if not args.private_mounts:
    os.execvp('unshare',['unshare','--mount','--propagation','private',sys.executable,__file__,*sys.argv[1:],'--private-mounts'])
assert Path('/proc/self/ns/mnt').stat().st_ino != Path('/proc/1/ns/mnt').stat().st_ino
assert platform.machine()=='aarch64' and platform.release()=='4.4.189'
assert command(['findmnt','-n','-o','SOURCE','/'])['stdout']=='/dev/mmcblk0p2'
assert command(['findmnt','-n','-o','SOURCE','/boot'])['stdout']=='/dev/mmcblk0p1'
assert cid('mmcblk0')=='9b4fc38015ae4a049ecd796ceceb2ef9473f4773c9b3a066ce59b567c516bbef'
assert cid('mmcblk1')=='12d2c78fbc14993fe2f8a00c413a5e3ef8d9659a3eba9a41a77b5c37029aa193'
assert int(Path('/sys/block/mmcblk1/size').read_text())*512==127934660608
numbers={p.read_text().strip() for p in Path('/sys/block/mmcblk1').glob('mmcblk1p*/dev')}
existing=[line.split() for line in Path('/proc/self/mountinfo').read_text().splitlines() if line.split()[2] in numbers]
assert {line[4] for line in existing} <= {'/roms2','/opt/system/Tools'}, 'unexpected test-card mount'
if existing:
    assert any(line[3]=='/' and line[4]=='/roms2' for line in existing)
result={'scope':'read-only diagnostic FAT log collection on returned stock OS',
        'kernel':platform.release(),'taint':Path('/proc/sys/kernel/tainted').read_text().strip(),
        'btrfs':command(['btrfs','device','stats','/']),
        'stock_image':command(['sha256sum','/boot/Image']),
        'services':command(['systemctl','is-active','emulationstation','ogage','fn-menu-watcher']),
        'files':{},'secondary_mounted_readonly':False,'secondary_unmounted_after_collection':False,
        'mount_namespace_private':True,'existing_stock_mounts':[' '.join(line) for line in existing]}
if args.experiment in ['B01','C01','C02','C03','C04','C05','C06','C07']:
    root_number=Path('/sys/class/block/mmcblk1p2/dev').read_text().strip()
    assert not [line for line in existing if line[2]==root_number], 'candidate root is mounted'
    result['candidate_ext4_fsck']=command(['/usr/sbin/e2fsck','-fn','/dev/mmcblk1p2'])
with tempfile.TemporaryDirectory(prefix='muos-linux-log-',dir='/tmp') as temporary:
    mounted=False
    try:
        if existing:
            subprocess.run(['mount','--bind','/roms2',temporary],check=True)
            mounted=True
            subprocess.run(['mount','-o','remount,bind,ro,nosuid,nodev,noexec,noatime',temporary],check=True)
        else:
            subprocess.run(['mount','-t','vfat','-o','ro,nosuid,nodev,noexec,noatime','/dev/mmcblk1p1',temporary],check=True)
        mounted=True
        result['secondary_mounted_readonly']=True
        result['mount_observed']=command(['findmnt','-n','-o','SOURCE,FSTYPE,OPTIONS','--target',temporary])
        assert result['mount_observed']['exit_code']==0
        assert 'ro' in result['mount_observed']['stdout'].rsplit(None,1)[1].split(',')
        root=Path(temporary)
        experiment={'A01':'MUOS-R35S-LINUX-P4-A01','B01':'MUOS-R35S-EXT4-P4-B01','C01':'MUOS-R35S-INIT-P4-C01','C02':'MUOS-R35S-INIT-P4-C02','C03':'MUOS-R35S-GRAPHICS-P4-C03','C04':'MUOS-R35S-FRONTEND-P4-C04','C05':'MUOS-R35S-AUDIO-P4-C05','C06':'MUOS-R35S-FRONTEND-AUDIO-P4-C06','C07':'MUOS-R35S-NETWORK-P4-C07'}[args.experiment]
        folder={'A01':'DIAG01','B01':'DIAG02','C01':'DIAG03','C02':'DIAG04','C03':'DIAG05','C04':'DIAG06','C05':'DIAG07','C06':'DIAG08','C07':'DIAG09'}[args.experiment]
        base_marker='MUOS-R35S-EXT4-P4-B01' if args.experiment in ['C01','C02','C03','C04','C05','C06','C07'] else experiment
        assert (root/'DIAG.ID').read_text().strip()==base_marker
        result['experiment']=experiment
        result['base_media_marker']=base_marker
        for name in ['REPORT.TXT','DMESG.TXT','RESULT.TXT']:
            path=root/folder/name
            if path.is_file():
                assert path.stat().st_size<=512*1024
                data=path.read_bytes()
                result['files'][name]={'sha256':hashlib.sha256(data).hexdigest(),'text':data.decode(errors='replace')}
            else:
                result['files'][name]={'missing':True}
        if args.experiment in ['C02','C03','C04','C05','C06','C07']:
            result['archived_logs']={}
            archives=sorted(p for p in (root/folder).iterdir() if re.fullmatch(r'BOOT[0-9]{4}',p.name) and p.is_dir()) if (root/folder).is_dir() else []
            for archive in archives[-8:]:
                files={}
                for name in ['REPORT.TXT','DMESG.TXT','RESULT.TXT'] + (['RECOVER.TXT','PREBOOT.TXT'] if args.experiment=='C07' else []):
                    path=archive/name
                    if path.is_file():
                        assert path.stat().st_size<=512*1024
                        data=path.read_bytes()
                        files[name]={'sha256':hashlib.sha256(data).hexdigest(),'text':data.decode(errors='replace')}
                    else:files[name]={'missing':True}
                result['archived_logs'][archive.name]=files
    finally:
        if mounted:
            subprocess.run(['umount',temporary],check=True)
            result['secondary_unmounted_after_collection']=True
print(json.dumps(result,indent=2))
