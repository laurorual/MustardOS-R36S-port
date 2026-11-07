#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Collect only public C20 completion evidence; raw/private backups stay in place."""
from pathlib import Path
import argparse,hashlib,ipaddress,json,subprocess,tempfile

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'preferences'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True,type=ipaddress.IPv4Address)
a=p.parse_args();stage=Path((area/'latest-offline-package').read_text().strip());assert stage.is_relative_to(area)
ssh=['ssh','-i',str(work/'private/deck-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes',
 '-oHostKeyAlias=192.168.15.16','-oUserKnownHostsFile='+str(work/'private/deck-known-hosts'),
 '-oBatchMode=yes','-oConnectTimeout=8','deck@'+str(a.host)]
out=Path(tempfile.mkdtemp(prefix='offline-complete.',dir=area))
names=['data-format.txt','data-before-marker.txt','data-after-marker.txt',
       'fat-final.txt','root-final.txt','data-final.txt','result.json',
       'root-mode-before-fsck.txt','root-mode-correction.txt','root-mode-after-fsck.txt',
       'root-mode-repair.json','root-mode-repair-cache-confirmed.json',
       'fat-final-after-mode-repair.txt','root-final-after-mode-repair.txt',
       'data-final-after-mode-repair.txt','result-after-mode-repair.json']
for name in names:
    result=subprocess.run(ssh+['cat /home/deck/muos-r35s-c20-private/'+name],capture_output=True,timeout=20)
    assert result.returncode==0,(name,result.stderr.decode(errors='replace'))
    assert len(result.stdout)<131072,name
    (out/name).write_bytes(result.stdout)
before=json.loads((out/'result.json').read_text());after=json.loads((out/'result-after-mode-repair.json').read_text())
repair=json.loads((out/'root-mode-repair-cache-confirmed.json').read_text())
assert before['passed'] and not before['root_mode_repaired']
assert after['passed'] and after['root_mode_repaired'] and after['data_unmounted']
assert before['protected640MiB_current_canonical_sha256']==before['protected640MiB_before_permission_repair_sha256']
assert repair['root_mode']=='0755' and repair['no_file_data_or_boot_FAT_bytes_changed']
assert repair['supersedes_cached_whole_device_readback'] and repair['after']['changed_bytes']>0
assert after['protected640MiB_current_canonical_sha256']==repair['after']['sha256']
code='''set -eu
test ! -S /run/muos-r35s-c20.sock
test ! -e /run/muos-r35s-c20-root
for part in /dev/mmcblk0p1 /dev/mmcblk0p2 /dev/mmcblk0p3;do
 if findmnt -rn -S "$part" >/dev/null;then exit 1;fi
done
lsblk -J -b -o NAME,TYPE,SIZE,FSTYPE,LABEL,UUID,PARTUUID,MOUNTPOINTS /dev/mmcblk0
'''
(out/'final-idle-state.sh').write_text(code)
result=subprocess.run(ssh+['sh -s'],input=code,text=True,capture_output=True,timeout=20)
(out/'final-idle-state.stdout').write_text(result.stdout);(out/'final-idle-state.stderr').write_text(result.stderr)
assert result.returncode==0,(result.stdout,result.stderr)
tree=json.loads(result.stdout)['blockdevices'];assert len(tree)==1
part=next(item for item in tree[0]['children'] if item['name']=='mmcblk0p3')
assert part['fstype']=='ext4' and part['label']=='MUOSDATA' and part['uuid']=='6d756f73-c020-4000-8000-000000000001'
assert all(not any(item['mountpoints']) for item in tree[0]['children'])
meta={'passed':True,'offline_volume_and_markers_created':True,'offline_fsck_three_partitions_passed':True,
      'root_mode_0755_repaired':True,'protected_prefix_change_bounded_to_MBR_p3_and_approved_inode_metadata':True,
      'all_card_partitions_unmounted':True,'helper_stopped_snapshot_socket_removed':True,
      'private_backup_files_collected':False,'runtime_integration_enabled':False,
      'native_R35S_mount_or_reboot_not_tested_by_this_collector':True,
      'executed_package':str(stage),'collector_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(out/'analysis.json').write_text(json.dumps(meta,indent=2)+'\n')
(area/'latest-offline-complete').write_text(str(out)+'\n')
print('C20 offline completion collected; root0755, clean filesystems, helper off/card unmounted:',out)
