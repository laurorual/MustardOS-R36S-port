#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C83 raw-sector/fault fixtures on regular synthetic ext4 images only."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,shutil,stat,subprocess,tempfile,types
from unittest.mock import patch
import phase4_root_metadata as m
from phase4_backup_core import sha

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'root-permissions';area.mkdir(exist_ok=True)
stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area));cases=[]
def reject(name,call):
    try:call()
    except (ValueError,OSError):cases.append(name)
    else:raise AssertionError(name)
assert m.crc32c(0xffffffff,b'123456789')^0xffffffff==0xe3069283;cases.append('Castagnoli-known-vector')
source=b'# fixture rule\nLABEL="holo_automount_end"\n';cid='a'*32;cid_hash=hashlib.sha256(cid.encode()).hexdigest()
rule=m.runtime_automount_rule(source,cid,cid_hash)
assert rule.endswith(source) and b'UDISKS_IGNORE' in rule and cid.encode() in rule and b'mmcblk0p[123]' in rule
cases.append('runtime-rule-exact-card-original-preserved')
reject('runtime-rule-wrong-CID',lambda:m.runtime_automount_rule(source,'b'*32,cid_hash))
reject('runtime-rule-injection',lambda:m.runtime_automount_rule(source,'a";bad',cid_hash))
reject('runtime-rule-missing-label',lambda:m.runtime_automount_rule(b'other',cid,cid_hash))
spec=importlib.util.spec_from_file_location('helper',repo/'port/scripts/phase4-root-permissions.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
reject('snapshot-refuses-user-directory',lambda:helper.operation('inspect'))
# Real helper constructor still refuses a regular-file substitute for /dev.
fixture_file=stage/'not-a-device';fixture_file.write_bytes(b'not a card');fd=os.open(fixture_file,os.O_RDONLY)
helper.guard=types.SimpleNamespace(identity=lambda:None);helper.core=types.SimpleNamespace(flush_block_aliases=lambda a:None)
with patch.object(helper,'aliases',return_value=[('fixture',123)]),patch.object(helper.os,'open',return_value=fd):
    reject('production-open-refuses-regular-file',helper.open_whole)
# Read-only aliases use only the two exact ioctls; production refuses other fds.
opened=[];events=[]
def fake_open(path,flags):opened.append((path,flags));return 10
helper.guard=types.SimpleNamespace(identity=lambda:None)
with patch.object(helper,'aliases',return_value=[('fixture',123)]),patch.object(helper.os,'open',fake_open),patch.object(helper.os,'close'),patch.object(helper.os,'fstat',return_value=types.SimpleNamespace(st_mode=stat.S_IFBLK,st_rdev=123)),patch.object(helper.fcntl,'ioctl',side_effect=lambda fd,request,value: events.append(request) or (__import__('struct').pack('i',1) if request==0x125e else 0)):
    helper.readonly_card()
assert opened[0][1]&os.O_ACCMODE==os.O_RDONLY and events==[0x125d,0x125e];cases.append('kernel-protection-set-readonly-never-clear')
fixture=r'''
from pathlib import Path
import hashlib,json,os,shutil,struct,subprocess,sys
sys.path.insert(0,'/port/scripts')
import phase4_root_metadata as m
stage=Path(sys.argv[1]);base=['has_journal','ext_attr','resize_inode','dir_index','filetype','extent','sparse_super','large_file','dir_nlink','extra_isize']
def run(args):
 r=subprocess.run(args,capture_output=True,text=True,timeout=60);assert r.returncode==0,(args,r.stdout[-1000:],r.stderr[-1000:]);return r
for kind,features in [('metadata-csum',base+['flex_bg','huge_file','metadata_csum']),('uninit-bg',base+['uninit_bg'])]:
 image=stage/(kind+'.ext4')
 with image.open('xb') as f:f.truncate(32*1024*1024)
 run(['mke2fs','-q','-t','ext4','-b','4096','-I','256','-O','none,'+','.join(features),str(image)])
 run(['debugfs','-w','-R','set_inode_field <2> mode 040777',str(image)]);run(['e2fsck','-fn',str(image)])
 before=image.read_bytes();sb=before[1024:2048];gd=before[4096:8192];g=m.geometry(sb,gd,0,len(before));offset=g['sector_offset'];sector=before[offset:offset+512]
 p=m.sector_patch(sb,gd,sector,0,len(before));assert p['checksummed']==(kind=='metadata-csum')
 print('C83_PASS_'+kind+'-valid-before-checksum-and-mode')
 def refuse(name,call):
  try:call()
  except (ValueError,OSError):print('C83_PASS_'+kind+'-'+name)
  else:raise AssertionError(name)
 for field,value in [(56,0),(58,2),(88,128),(254,64),(96,0x2c2)]:
  bad=bytearray(sb);struct.pack_into('<H' if field in [56,58,88,254] else '<I',bad,field,value)
  refuse('bad-superblock-'+str(field),lambda:m.geometry(bytes(bad),gd,0,len(before)))
 bad=bytearray(sector);bad[256+2]=1
 refuse('wrong-root-owner',lambda:m.sector_patch(sb,gd,bytes(bad),0,len(before)))
 refuse('wrong-partition-size',lambda:m.sector_patch(sb,gd,sector,0,len(before)+4096))
 bad=bytearray(gd);struct.pack_into('<I',bad,8,0)
 refuse('inode-table-out-of-range',lambda:m.sector_patch(sb,bytes(bad),sector,0,len(before)))
 if kind=='metadata-csum':
  bad=bytearray(sector);bad[380]^=1
  refuse('invalid-inode-checksum',lambda:m.sector_patch(sb,gd,bytes(bad),0,len(before)))
  bad=bytearray(sb);bad[1020]^=1
  refuse('invalid-superblock-checksum',lambda:m.geometry(bytes(bad),gd,0,len(before)))
 events=[]
 def denied_write(*args):events.append('write');raise AssertionError('must not write')
 refuse('changed-before-write',lambda:m.apply_sector(0,p,lambda *a:bytes(512),denied_write,lambda f:None));assert not events
 def short(*args):events.append('short');return 128
 refuse('short-write-no-retry',lambda:m.apply_sector(0,p,lambda *a:sector,short,lambda f:None));assert events==['short']
 def failed_sync(f):raise OSError('fixture sync error')
 refuse('fsync-failure',lambda:m.apply_sector(0,p,lambda *a:sector,lambda *a:512,failed_sync))
 refuse('readback-mismatch',lambda:m.apply_sector(0,p,lambda *a:sector,lambda *a:512,lambda f:None))
 bad=dict(p);a=bytearray.fromhex(p['after']);a[0]^=1;bad['after']=a.hex();bad['after_sha256']=hashlib.sha256(a).hexdigest()
 refuse('unbounded-payload',lambda:m.apply_sector(0,bad,lambda *a:sector,denied_write,lambda f:None))
 fd=os.open(image,os.O_RDWR)
 try:m.apply_sector(fd,p,os.pread,os.pwrite,os.fsync)
 finally:os.close(fd)
 after=image.read_bytes();assert after==before[:offset]+bytes.fromhex(p['after'])+before[offset+512:]
 m.sector_patch(sb,gd,after[offset:offset+512],0,len(after),0o40755)
 run(['e2fsck','-fn',str(image)]);assert 'Mode:  0755' in run(['debugfs','-R','stat <2>',str(image)]).stdout
 print('C83_PASS_'+kind+'-exact-sector-diff-and-fsck0')
 fd=os.open(image,os.O_RDWR)
 try:refuse('replay-refused',lambda:m.apply_sector(fd,p,os.pread,os.pwrite,os.fsync))
 finally:os.close(fd)
 print('C83_PASS_'+kind+'-superblock-GDT-all-other-bytes-identical')
'''
(stage/'fixtures.py').write_text(fixture);container=(work/'rootfs-container.iid').read_text().strip();rel=lambda p:'/work/'+str(p.relative_to(work))
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=64m','-v',str(work)+':/work:rw,z','-v',str(repo/'port')+':/port:ro,z',container,'python3',rel(stage/'fixtures.py'),rel(stage)]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
for ext,data in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:(stage/('fixtures.'+ext)).write_text(data)
assert r.returncode==0,(stage,r.stdout[-1000:],r.stderr[-2000:])
cases.extend(line[9:] for line in r.stdout.splitlines() if line.startswith('C83_PASS_'))
sources=[Path(__file__),*[repo/'port/scripts'/name for name in ['phase4_root_metadata.py','phase4-root-permissions.py','prepare-phase4-root-permissions.py','phase4_backup_core.py','phase4_root_migration.py','phase4-offline-backup.py']]]
for p in sources:ast.parse(p.read_text())
(stage/'analysis.json').write_text(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,'physical_media_opened':False,'existing_C82_guard_sources_pinned':True,
 'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}},indent=2)+'\n')
(area/'latest-checks').write_text(str(stage)+'\n');print('C83 metadata checks:',len(cases),'passed:',stage)
