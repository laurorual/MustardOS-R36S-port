#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Offline helper protocol and real-file sysfs refusal fixtures. No block opens."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import errno,hashlib,importlib.util,json,os,shutil,tempfile,types
from unittest.mock import patch

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/preferences'
stage=Path(tempfile.mkdtemp(prefix='offline-server.',dir=area))
source=Path(__file__).with_name('phase4-userdata-offline-server.py')
spec=importlib.util.spec_from_file_location('server',source)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.SYS_BLOCK=stage/'sys';server.SYS=server.SYS_BLOCK/'mmcblk0';server.PROC=stage/'proc';server.DMI=stage/'dmi'
server.SYS_BLOCK.mkdir();server.PROC.mkdir();server.DMI.write_text('Jupiter\n')
cases=[]
def passed(name):cases.append(name)
def refuse(call):
    try:call()
    except RuntimeError:return
    raise AssertionError('Unexpected request accepted')
for request in [None,{},[],{'action':'shell'},{'action':'partition','device':'/dev/nvme0n1'},
                {'action':'stop','command':'true'},{'action':'ack-backup','sha256':None}]:
    refuse(lambda:server.dispatch(request))
passed('protocol-whitelist-and-fields-before-actions')
refuse(server.format_data);refuse(server.partition);refuse(server.verify);refuse(server.repair_root_mode)
passed('format-partition-verify-require-owned-transaction-and-independent-backup')
test=hashlib.sha256(b'fake-test-cid').hexdigest();original=hashlib.sha256(b'fake-original-cid').hexdigest()
server.plan={'test_card_cid_sha256':test,'protected_original_card_cid_sha256':original,'capacity_sectors_512':249872384}
def card(cid='fake-test-cid',size='249872384',sector='512'):
    if server.SYS.exists():shutil.rmtree(server.SYS)
    for name in ['device','queue','holders']:(server.SYS/name).mkdir(parents=True,exist_ok=True)
    (server.SYS/'device/cid').write_text(cid);(server.SYS/'size').write_text(size)
    (server.SYS/'queue/logical_block_size').write_text(sector);(server.SYS/'dev').write_text('999:999')
    (server.PROC/'swaps').write_text('Filename Type Size Used Priority\n')
card('fake-original-cid');refuse(server.identity);passed('original32-present-refused')
card('wrong-cid');refuse(server.identity);passed('unknown-card-refused')
card(size='62521344');refuse(server.identity);passed('wrong-capacity-refused')
card(sector='4096');refuse(server.identity);passed('wrong-sector-size-refused')
card();(server.SYS/'holders/foreign').touch();refuse(server.identity)
passed('block-holder-refused')
card();(server.PROC/'100').mkdir();(server.PROC/'100/mountinfo').write_text('14 0 999:999 / /card rw - ext4 /dev/fixture rw\n')
refuse(server.identity);passed('mount-in-any-namespace-refused')
(server.PROC/'100/mountinfo').write_text('');server.identity()
passed('correct-fake-sysfs-passes-readonly-identity-without-opening-devices')
real_read_text=Path.read_text
def kernel_thread(path,*args,**kwargs):
    if path==server.PROC/'100/mountinfo':raise OSError(errno.EINVAL,'kernel thread has no mount namespace')
    return real_read_text(path,*args,**kwargs)
with patch.object(Path,'read_text',kernel_thread):server.identity()
passed('kernel-thread-EINVAL-has-no-mount-namespace')
def denied(path,*args,**kwargs):
    if path==server.PROC/'100/mountinfo':raise PermissionError(errno.EACCES,'unreadable live process')
    return real_read_text(path,*args,**kwargs)
with patch.object(Path,'read_text',denied):
    try:server.identity()
    except PermissionError:pass
    else:raise AssertionError('Live process permission error ignored')
passed('live-process-permission-error-still-fails-closed')
server.DECK_TEST_CID=hashlib.sha256(b'fake-deck-reader-cid').hexdigest()
card('fake-deck-reader-cid');server.identity()
passed('only-exact-pinned-reader-alias-accepted-with-remaining-guards')
with patch.object(server.platform,'machine',return_value='aarch64'):refuse(server.identity)
passed('live-console-and-wrong-host-architecture-refused')
server.DMI.write_text('Other computer');refuse(server.identity)
passed('wrong-offline-host-refused')
server.plan['new_partition']={'partuuid':'4d554432-03','start_sector':1310720,'sectors':248561664}
entries={'DEVNAME':'/dev/mmcblk0p3','PART_ENTRY_SCHEME':'dos','PART_ENTRY_UUID':'4d554432-03',
         'PART_ENTRY_TYPE':'0x83','PART_ENTRY_NUMBER':'3','PART_ENTRY_OFFSET':'1310720',
         'PART_ENTRY_SIZE':'248561664','PART_ENTRY_DISK':'179:0'}
export=lambda values:''.join(key+'='+value+'\n' for key,value in values.items())
assert server.empty_partition_probe(export(entries),0,'179:0')==entries
assert server.empty_partition_probe('',2,'179:0')=={}
passed('blkid-success-with-only-correct-partition-entry-is-not-a-filesystem')
for key,value in [('TYPE','ext4'),('USAGE','filesystem'),('PTTYPE','dos'),('UUID','old-volume'),('UNKNOWN','x')]:
    refuse(lambda:server.empty_partition_probe(export({**entries,key:value}),0,'179:0'))
passed('real-FS-nested-table-and-unknown-probe-tags-still-refused')
for key in entries:
    changed=dict(entries);changed[key]='wrong';refuse(lambda:server.empty_partition_probe(export(changed),0,'179:0'))
passed('partition-probe-must-match-all-plan-and-device-values')
refuse(lambda:server.empty_partition_probe('PART_ENTRY_SCHEME=dos\n',0,'179:0'))
refuse(lambda:server.empty_partition_probe(export(entries)+'PART_ENTRY_SCHEME=dos\n',0,'179:0'))
refuse(lambda:server.empty_partition_probe(export(entries),8,'179:0'))
passed('short-duplicate-and-ambivalent-probe-metadata-refused')
# Exercise restart from a real regular recovery prefix, independently of the
# separately tested physical identity/mount guards. No block devices are opened.
spec_io=importlib.util.spec_from_file_location('io',Path(__file__).with_name('phase4_userdata_io.py'))
server.io=importlib.util.module_from_spec(spec_io);spec_io.loader.exec_module(server.io)
survey=Path((area/'latest-layout').read_text().strip())
server.before=(survey/'mbr.before').read_bytes();server.after=(survey/'mbr.proposed').read_bytes()
server.BACKUP=stage/'recovery';server.BACKUP.mkdir();server.deck_uid=os.getuid()
server.plan['offline_prefix_backup_bytes']=2048
baseline=server.before+b'Q'*1536;media=stage/'regular-media'
media.write_bytes(server.after+baseline[512:])
(server.BACKUP/'prefix.backup').write_bytes(baseline);(server.BACKUP/'prefix.backup').chmod(0o400)
description={'bytes':2048,'cid_sha256':server.plan['test_card_cid_sha256'],
             'mbr_sha256':hashlib.sha256(server.before).hexdigest(),'sha256':hashlib.sha256(baseline).hexdigest()}
(server.BACKUP/'backup.json').write_text(json.dumps(description));(server.BACKUP/'backup.json').chmod(0o400)
server.open_card=lambda **kwargs:os.open(media,os.O_RDONLY)
server.geometry=lambda:None
entries['PART_ENTRY_DISK']='999:999'
server.run=lambda *args,**kwargs:types.SimpleNamespace(returncode=0,stdout=export(entries))
server.state={'acked':False,'partitioned':False,'formatted':False,'mounted':False,'root_mode_repaired':False}
result=server.resume();assert result['partition_applied'] and not server.state['acked'] and not server.state['formatted']
passed('restart-revalidates-real-recovery-prefix-and-requires-fresh-host-ack')
refuse(server.resume);passed('resume-cannot-adopt-or-overwrite-active-transaction')
server.state={'acked':False,'partitioned':False,'formatted':False,'mounted':False,'root_mode_repaired':False}
media.write_bytes(server.after+b'X'+baseline[513:])
refuse(server.resume);assert 'backup_sha256' not in server.state
passed('restart-refuses-changed-protected-data-before-arming')
result={'passed':True,'case_count':len(cases),'cases':cases,'block_devices_opened':False,
        'server_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'check_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(stage/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
(area/'latest-offline-server').write_text(str(stage)+'\n')
for name in cases:print('PASS',name)
print(stage)
