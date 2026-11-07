#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C81 refusal/failure fixtures and real ext4/tar tests; no physical media."""
from pathlib import Path
import ast, errno, hashlib, importlib.util, io, json, os, shutil, stat, subprocess, sys, tarfile, tempfile, types
from unittest.mock import patch
import phase4_backup_core as core
import phase4_root_migration as policy
from phase4_candidate import sha

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'offline-backup';area.mkdir(exist_ok=True)
stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area));cases=[]
def reject(name,call):
    try:call()
    except (ValueError,RuntimeError,OSError):cases.append(name)
    else:raise AssertionError(name)
spec=importlib.util.spec_from_file_location('helper',repo/'port/scripts/phase4-offline-backup.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.policy=types.SimpleNamespace(**{k:getattr(policy,k) for k in ['CAPACITY','ORIGINAL_CID','DECK_CID']})
s.SYS=stage/'sys';s.PROC=stage/'proc';s.DMI=stage/'dmi';s.DEVICE=stage/'device-must-not-open'
s.SYS.mkdir();s.PROC.mkdir();s.DMI.write_text('Jupiter\n')
s.policy.DECK_CID=hashlib.sha256(b'fixture-reader-cid').hexdigest()
s.policy.ORIGINAL_CID=hashlib.sha256(b'fixture-original-cid').hexdigest()
def reset(cid='fixture-reader-cid'):
    for p in s.SYS.iterdir():shutil.rmtree(p)
    for name in ['device','queue','holders']:(s.SYS/'mmcblk0'/name).mkdir(parents=True,exist_ok=True)
    (s.SYS/'mmcblk0/device/cid').write_text(cid);(s.SYS/'mmcblk0/size').write_text(str(policy.CAPACITY))
    (s.SYS/'mmcblk0/queue/logical_block_size').write_text('512');(s.SYS/'mmcblk0/dev').write_text('999:0')
    for n,start,size in [(1,32768,204800),(2,262144,1048576),(3,1310720,248561664)]:
        p=s.SYS/f'mmcblk0p{n}';(p/'holders').mkdir(parents=True)
        for key,v in [('start',start),('size',size),('dev','999:'+str(n))]:(p/key).write_text(str(v))
    for p in s.PROC.iterdir():
        if p.is_dir():shutil.rmtree(p)
        else:p.unlink()
    (s.PROC/'swaps').write_text('Filename Type Size Used Priority\n')
with patch.object(s.platform,'machine',return_value='x86_64'):
    reset();s.identity();cases.append('exact-fake-offline-identity-no-device-open')
    for cid in ['fixture-original-cid','unknown']:
        reset(cid);reject('reject-card-'+cid,s.identity)
    reset();s.DMI.write_text('Other');reject('reject-host-DMI',s.identity);s.DMI.write_text('Jupiter')
    for file,value in [('size','1'),('queue/logical_block_size','4096')]:
        reset();(s.SYS/'mmcblk0'/file).write_text(value);reject('reject-'+file,s.identity)
    reset();(s.SYS/'mmcblk0p2/start').write_text('0');reject('reject-geometry',s.identity)
    reset();(s.SYS/'mmcblk0p4').mkdir();reject('reject-extra-partition',s.identity)
    reset();(s.SYS/'mmcblk0p3/holders/foreign').touch();reject('reject-holder',s.identity)
    reset();(s.PROC/'100').mkdir();(s.PROC/'100/mountinfo').write_text('14 0 999:2 / /card ro - ext4 /dev/fake ro\n')
    reject('reject-mount-other-namespace-even-readonly',s.identity)
    real=Path.read_text
    def badread(path,*a,**kw):
        if path==s.PROC/'100/mountinfo':raise PermissionError(errno.EACCES,'fixture denied')
        return real(path,*a,**kw)
    with patch.object(Path,'read_text',badread):reject('reject-unreadable-live-namespace',s.identity)
    for err in [errno.EINVAL,errno.ENOENT,errno.ESRCH]:
        def gone(path,*a,**kw):
            if path==s.PROC/'100/mountinfo':raise OSError(err,'gone/kernel thread')
            return real(path,*a,**kw)
        with patch.object(Path,'read_text',gone):s.identity()
        cases.append('ignore-only-gone-no-namespace-'+str(err))
    reset();(s.PROC/'100').mkdir();(s.PROC/'100/mountinfo').write_text('14 0 999:3 / /owned ro - ext4 /dev/fake ro\n')
    with patch.object(s.os,'readlink',return_value='mnt-owned'):s.identity(Path('/owned'))
    cases.append('allow-only-owned-private-p3-readonly')
    reject('reject-same-device-wrong-mountpoint',s.identity)
    reset();swap=stage/'swap';swap.touch();dev=os.stat(swap).st_dev
    (s.SYS/'mmcblk0/dev').write_text(f'{os.major(dev)}:{os.minor(dev)}')
    (s.PROC/'swaps').write_text('Filename Type Size Used Priority\n'+str(swap)+' file 1 0 -2\n')
    reject('reject-swap-file-on-card',s.identity)
with patch.object(s.platform,'machine',return_value='aarch64'):reject('reject-console-as-offline-host',s.identity)
# All host commands fail closed; no automatic repair or timeout fallback.
with patch.object(s.subprocess,'run',return_value=types.SimpleNamespace(returncode=4)):
    reject('host-fsck-nonzero-aborts',lambda:s.run(['e2fsck','-fn','fixture']))
with patch.object(s.subprocess,'run',side_effect=subprocess.TimeoutExpired('e2fsck',180)):
    try:s.run(['e2fsck','-fn','fixture'])
    except subprocess.TimeoutExpired:cases.append('host-tool-timeout-aborts')
    else:raise AssertionError('timeout swallowed')
s.ROOT=stage/'isolated-snapshot'
for options in ['ro,nosuid,nodev,noexec,noload','ro,nosuid,nodev,noexec,norecovery','rw,nosuid,nodev,noexec,noload','ro,nodev,noexec,noload','ro,nosuid,nodev,noexec']:
    with patch.object(s,'run',return_value=types.SimpleNamespace(stdout='/dev/mmcblk0p3 ext4 999:3 '+options)),patch.object(s,'identity'):
        if options in ['ro,nosuid,nodev,noexec,noload','ro,nosuid,nodev,noexec,norecovery']:
            s.mount_check();cases.append('owned-mount-accept-'+options.split(',')[-1])
        else:reject('owned-mount-reject-'+options, s.mount_check)
for arg in ['serve','format','partition','restore','shell']:
    with patch.object(s.sys,'argv',['helper',arg]),patch.object(s.os,'geteuid',return_value=0):reject('CLI-reject-'+arg,s.bootstrap)
reject('snapshot-entry-refuses-user-source-directory',s.snapshot)
media=stage/'regular-source';media.write_bytes(b'fixture source'*4096);initial=sha(media)
fd=os.open(media,os.O_RDONLY)
try:
    wanted=core.copy_region(fd,3,4096,stage/'copy');assert (stage/'copy').read_bytes()==media.read_bytes()[3:4099]
    assert wanted==sha(stage/'copy');cases.append('regular-file-copy-fsync-readback-source-unchanged')
    reject('refuse-existing-output',lambda:core.copy_region(fd,0,4096,stage/'copy'))
    link=stage/'link';link.symlink_to(media)
    reject('refuse-output-symlink',lambda:core.copy_region(fd,0,4096,link))
    reject('refuse-short-source',lambda:core.copy_region(fd,0,media.stat().st_size+1,stage/'short'))
    with patch.object(core.os,'write',return_value=0):reject('backup-short-write',lambda:core.copy_region(fd,0,4096,stage/'short-write'))
    with patch.object(core.os,'fsync',side_effect=OSError('fixture fsync failure')):reject('backup-fsync-failure',lambda:core.copy_region(fd,0,4096,stage/'bad-fsync'))
    original_pread=core.os.pread;calls=[0]
    def changed(f,n,off):
        data=original_pread(f,n,off);calls[0]+=1
        return b'X'+data[1:] if calls[0]>1 else data
    with patch.object(core.os,'pread',changed):reject('source-changed-second-read',lambda:core.copy_region(fd,0,4096,stage/'changed'))
finally:os.close(fd)
assert sha(media)==initial
# Fake block descriptors check read-only alias IO and exact partition-first order.
opened=[];events=[]
def fake_open(path,flags):opened.append((str(path),flags));return len(opened)
def fake_stat(fd):return types.SimpleNamespace(st_mode=stat.S_IFBLK,st_rdev=fd)
aliases=[('p1',1),('p2',2),('p3',3),('whole',4)]
with patch.object(core.os,'open',fake_open),patch.object(core.os,'fstat',fake_stat),patch.object(core.os,'close'),patch.object(core.os,'fsync',side_effect=lambda f:events.append(('sync',f))),patch.object(core.fcntl,'ioctl',side_effect=lambda f,c,v:events.append(('flush',f,c))):
    assert core.flush_block_aliases(aliases)==['p1','p2','p3','whole']
assert all(flags&os.O_ACCMODE==os.O_RDONLY for _,flags in opened)
assert events==[v for n in range(1,5) for v in [('sync',n),('flush',n,0x1261)]]
cases.append('alias-flush-readonly-partitions-before-whole-no-drop-caches')
with patch.object(core.os,'open',return_value=10),patch.object(core.os,'fstat',return_value=types.SimpleNamespace(st_mode=stat.S_IFREG,st_rdev=1)),patch.object(core.os,'close'):
    reject('alias-regular-file-not-block',lambda:core.flush_block_aliases([('fake',1)]))
# Production device open never accepts a regular-file substitute.
s.core=core;s.plan={'mbr_sha256':'0'*64,'boot_prefix_16MiB_sha256':'0'*64};s.DEVICE=media
with patch.object(s,'identity'),patch.object(core,'flush_block_aliases'):
    reject('production-open-refuses-regular-device-leaf',s.open_card)
# Independent host receipt fixture uses sparse regular files, never a real card.
from phase4_card_image import mbr_bytes
import struct
spec=importlib.util.spec_from_file_location('collector',repo/'port/scripts/collect-phase4-offline-backup.py')
collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)
download=stage/'download';download.mkdir(mode=0o700)
mbr=bytearray(mbr_bytes());struct.pack_into('<B3sB3sII',mbr,478,0,b'\xfe\xff\xff',0x83,b'\xfe\xff\xff',1310720,248561664)
for name,size in [('prefix.backup',policy.PREFIX_BYTES),('boot.fat',100*1024*1024),('root.ext4',policy.ROOT_BYTES)]:
    with (download/name).open('xb') as f:f.truncate(size)
with (download/'prefix.backup').open('r+b') as f:f.write(mbr)
with (download/'prefix.backup').open('rb') as f:boot=f.read(16*1024*1024)
rows={};mapping={}
for i,name in enumerate(sorted(policy.PRIVATE_FILES)):
    leaf='private-%02d.dat'%i;data=b'72\n' if name.endswith('boot-seq') else b'F'*64
    (download/leaf).write_bytes(data);mapping[name]=leaf
    rows[name]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'uid':0,'gid':0,'links':1,
        'mode':0o400 if '/muos-seedrng/' in name else 0o644 if name.startswith('etc/') else 0o600}
fake_plan={'mbr_sha256':hashlib.sha256(mbr).hexdigest(),'boot_prefix_16MiB_sha256':hashlib.sha256(boot).hexdigest(),
           'private_files_at_live_survey':rows,'survey_boot_sequence':72}
planfile=stage/'host-copy-fixture-plan.json';planfile.write_text(json.dumps(fake_plan))
(download/'private-files.json').write_text(json.dumps({'files':rows,'artifacts':mapping}))
records={}
with tarfile.open(download/'userdata.tar','w',format=tarfile.USTAR_FORMAT) as tar:
    for name in ['MUOS/preferences','MUOS/port-saves-v1',*core.MARKERS]:
        member=tarfile.TarInfo(name);member.uid=member.gid=0
        if name in core.MARKERS:
            data=core.MARKERS[name];member.mode=0o600;member.size=len(data)
            tar.addfile(member,io.BytesIO(data))
            records[name]={'type':'file','mode':0o600,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
        else:
            member.type=tarfile.DIRTYPE;member.mode=0o700;tar.addfile(member)
            records[name]={'type':'directory','mode':0o700}
(download/'userdata-manifest.json').write_text(json.dumps({'sha256':sha(download/'userdata.tar'),'records':records,'file_count':3,'archive_verified':True}))
artifacts={p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in download.iterdir()}
receipt={'passed':True,'experiment':'C81_OFFLINE_BACKUP_ONLY','plan_sha256':sha(planfile),'boot_sequence':72,
 'artifacts':artifacts,'prefix_sha256':artifacts['prefix.backup']['sha256'],'fat_fsck_exit':0,'root_fsck_exit':0,'data_fsck_exit':0}
for key in ['all_namespaces_checked','alias_cache_synchronized','private_state_from_fresh_backup','userdata_archive_verified','p3_unmounted']:receipt[key]=True
for key in ['independent_host_copy_verified','device_payload_writer_available','device_format_or_restore_available','candidate_provisioned','seed_loaded','reboot_requested']:receipt[key]=False
receiptfile=download/'backup.json';receiptfile.write_text(json.dumps(receipt))
for p in download.iterdir():p.chmod(0o600)
ack=collector.verify_download(download,planfile)
assert ack['passed'] and ack['independent_host_copy_verified'] and not ack['execution_enabled']
cases.append('synthetic-host-copy-real-hash-fsync-no-writer')
(download/'unknown').touch();reject('host-copy-extra-file',lambda:collector.verify_download(download,planfile));(download/'unknown').unlink()
payload=download/mapping['etc/muos-network-authorized_key'];data=payload.read_bytes();payload.write_bytes(data+b'bad')
reject('host-copy-corrupted-private-payload',lambda:collector.verify_download(download,planfile));payload.write_bytes(data)
for key,value in [('plan_sha256','0'*64),('boot_sequence',73),('candidate_provisioned',True),('root_fsck_exit',False),('data_fsck_exit',1)]:
    altered={**receipt,key:value};receiptfile.write_text(json.dumps(altered))
    reject('host-copy-reject-'+key,lambda:collector.verify_download(download,planfile))
receiptfile.write_text(json.dumps(receipt))
with patch.object(collector.os,'fsync',side_effect=OSError('fixture host fsync failure')):
    reject('host-copy-fsync-failure',lambda:collector.verify_download(download,planfile))
# Tar parser refuses unsafe semantics even when supplied a matching transport hash.
for kind in ['duplicate','traversal','symlink','hardlink','scope','mode','marker']:
    archive=stage/('bad-'+kind+'.tar')
    with tarfile.open(archive,'w',format=tarfile.USTAR_FORMAT) as tar:
        member=tarfile.TarInfo('../escape' if kind=='traversal' else 'other' if kind=='scope' else '.muos-r35s-data-v1')
        member.mode=0o644 if kind=='mode' else 0o600;data=b'wrong' if kind=='marker' else core.MARKERS['.muos-r35s-data-v1']
        if kind in ['symlink','hardlink']:
            member.type=tarfile.SYMTYPE if kind=='symlink' else tarfile.LNKTYPE;member.linkname='/etc/passwd';tar.addfile(member)
        else:
            member.size=len(data);tar.addfile(member,io.BytesIO(data))
            if kind=='duplicate':tar.addfile(member,io.BytesIO(data))
    reject('reject-archive-'+kind,lambda:core.verify_userdata_archive(archive,records))
# C82 source drift is allowed only through an explicit backup-only policy.
source_policy={'reason':'SteamOS_automount_chmod777','p2_mode':0o777,'p3_mode':0o777,
 'automount_script_sha256':'a'*64,'diagnostic_root_sha256':artifacts['root.ext4']['sha256']}
for key,value in [('p2_mode',0o775),('p3_mode',True),('reason','ignore'),('automount_script_sha256','bad')]:
    reject('source-policy-reject-'+key,lambda:core.validate_source_root_policy({**source_policy,key:value}))
custom=json.loads(json.dumps(receipt));custom.update({'source_root_modes':{'p2':0o777,'p3':0o777},
 'metadata_repair_required_before_boot':True,'source_root_policy_sha256':hashlib.sha256((json.dumps(source_policy,sort_keys=True)+'\n').encode()).hexdigest()})
for name in ['private-files.json','userdata-manifest.json']:
    value=json.loads((download/name).read_text());value['source_root_mode']=0o777
    (download/name).write_text(json.dumps(value));custom['artifacts'][name]['sha256']=sha(download/name);custom['artifacts'][name]['bytes']=(download/name).stat().st_size
receiptfile.write_text(json.dumps(custom))
reject('host-source-drift-refused-without-policy',lambda:collector.verify_download(download,planfile))
ack=collector.verify_download(download,planfile,source_policy)
assert ack['metadata_repair_required_before_boot'] is True and ack['execution_enabled'] is False
cases.append('host-explicit-source-policy-requires-repair-and-no-writer')
reject('host-source-policy-hash-mismatch',lambda:collector.verify_download(download,planfile,{**source_policy,'automount_script_sha256':'b'*64}))
for p in download.iterdir():p.unlink()
download.rmdir()
# Exercise the private bundle and root-snapshot copy without privilege/device IO.
spec=importlib.util.spec_from_file_location('preparer',repo/'port/scripts/prepare-phase4-offline-backup.py')
preparer=importlib.util.module_from_spec(spec);spec.loader.exec_module(preparer)
bundle=stage/'bundle-fixture';bundle.mkdir(mode=0o700)
manifest=preparer.write_bundle(planfile,bundle,'0'*64)
assert preparer.verify_bundle(bundle)==manifest
cases.append('bundle-exact-inventory-source-plan-hashes-reread')
(bundle/'extra').touch();reject('bundle-refuses-extra-file',lambda:preparer.verify_bundle(bundle));(bundle/'extra').unlink()
leaf=bundle/'phase4_backup_core.py';data=leaf.read_bytes()
leaf.chmod(0o620);reject('bundle-refuses-group-writable',lambda:preparer.verify_bundle(bundle));leaf.chmod(0o600)
leaf.write_bytes(data+b'changed');reject('bundle-refuses-payload-hash-change',lambda:preparer.verify_bundle(bundle));leaf.write_bytes(data)
leaf.unlink();leaf.symlink_to(repo/'port/scripts/phase4_backup_core.py')
reject('bundle-refuses-source-symlink',lambda:preparer.verify_bundle(bundle));leaf.unlink();leaf.write_bytes(data);leaf.chmod(0o600)
counter=[0];executed=[]
def snapshot_dir(**kwargs):
    assert kwargs=={'prefix':'muos-r35s-c81.','dir':'/run'}
    counter[0]+=1;target=stage/('snapshot-fixture-'+str(counter[0]));target.mkdir(mode=0o700);return str(target)
with patch.object(s,'__file__',str(bundle/'phase4-offline-backup.py')),patch.object(s.os,'geteuid',return_value=0),patch.object(s.sys,'argv',['helper','backup']),patch.object(s.platform,'machine',return_value='x86_64'),patch.object(s.tempfile,'mkdtemp',snapshot_dir),patch.object(s.os,'execve',side_effect=lambda *a:executed.append(a)):
    s.bootstrap()
    assert len(executed)==1
    value={**manifest,'source_root_policy':source_policy};(bundle/'package.json').write_text(json.dumps(value))
    s.bootstrap();root=Path(executed[-1][1][1]).parent
    assert json.loads((root/'source-root-policy.json').read_text())==source_policy and stat.S_IMODE((root/'source-root-policy.json').stat().st_mode)==0o400
    cases.append('explicit-source-policy-sealed-in-root-snapshot')
    value['source_root_policy']={**source_policy,'p2_mode':0o775};(bundle/'package.json').write_text(json.dumps(value))
    reject('bootstrap-refuses-unscoped-source-policy',s.bootstrap)
    executable,args,env=executed[0];root=Path(args[1]).parent
    assert executable=='/usr/bin/python3' and args[-1]=='_snapshot' and env=={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'}
    assert stat.S_IMODE(root.stat().st_mode)==0o700 and {p.name for p in root.iterdir()}==s.ALLOWED
    assert all(stat.S_IMODE(p.stat().st_mode)==0o400 and sha(p)==manifest['files'][p.name] for p in root.iterdir())
    cases.append('bootstrap-protected-copy-clean-exec-no-snapshot-or-device-run')
    leaf.write_bytes(data+b'changed');reject('bootstrap-rejects-payload-before-exec',s.bootstrap);leaf.write_bytes(data)
    assert len(executed)==2
# A real, small synthetic ext4 exercises host debugfs parsing/extraction; no mounts.
fixture=r'''
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
sys.path.insert(0,'/port/scripts')
import phase4_backup_core as c
from phase4_root_migration import PRIVATE_FILES,OPTIONAL_PRIVATE
stage=Path(sys.argv[1]);tree=stage/'tree';tree.mkdir(mode=0o755)
for name in ['etc','var','var/lib','var/lib/muos-network','var/lib/muos-seedrng','var/lib/muos-diagnostic']:
 p=tree/name;p.mkdir(exist_ok=True);p.chmod(0o700 if name.split('/')[-1].startswith('muos-') else 0o755)
rows={}
for name in PRIVATE_FILES|OPTIONAL_PRIVATE:
 p=tree/name;p.write_bytes(b'72\n' if name.endswith('boot-seq') else b'S'*64)
 mode=0o400 if '/muos-seedrng/' in name else 0o644 if name.startswith('etc/') else 0o600
 p.chmod(mode);rows[name]={'mode':mode,'uid':0,'gid':0,'links':1,'bytes':p.stat().st_size,'sha256':c.sha(p)}
def run(args):
 r=subprocess.run(args,capture_output=True,text=True);assert r.returncode==0,(args,r.stdout,r.stderr);return r
image=stage/'fixture.ext4'
with image.open('xb') as f:f.truncate(16*1024*1024)
run(['mke2fs','-q','-t','ext4','-d',str(tree),str(image)])
run(['e2fsck','-fn',str(image)])
out=stage/'private';out.mkdir(mode=0o700)
plan={'private_files_at_live_survey':rows,'survey_boot_sequence':72}
r=c.extract_private(image,out,plan,run);assert r['files']==rows
print('C81_PASS_real-ext4-private-modes-hashes-counter')
try:c.extract_private(image,out,plan,run)
except ValueError:print('C81_PASS_existing-private-dump-refused')
else:raise AssertionError('dump overwrote existing output')
data=stage/'userdata';data.mkdir(mode=0o755)
(data/'MUOS').mkdir(mode=0o755)
for name in ['preferences','port-saves-v1']:(data/'MUOS'/name).mkdir(mode=0o700)
for name,value in c.MARKERS.items():p=data/name;p.write_bytes(value);p.chmod(0o600)
p=data/'MUOS/preferences/record';p.write_bytes(b'fixture preferences');p.chmod(0o600)
p=data/'MUOS/port-saves-v1/fixture.bundle';p.write_bytes(b'fixture saved state');p.chmod(0o600)
tar=stage/'userdata.tar';before=c.userdata_snapshot(data)[0];r=c.backup_userdata(data,tar)
assert r['archive_verified'] and r['records']==before==c.userdata_snapshot(data)[0]
print('C81_PASS_userdata-tar-readback-markers-source-unchanged')
for kind in ['symlink','hardlink','owner-mode','marker','size']:
 target=data/'MUOS/preferences/record';original=target.read_bytes()
 if kind=='symlink':target.unlink();target.symlink_to('/etc/passwd')
 if kind=='hardlink':os.link(target,data/'MUOS/preferences/extra')
 if kind=='owner-mode':target.chmod(0o644)
 if kind=='marker':(data/'.muos-r35s-data-v1').write_bytes(b'wrong')
 if kind=='size':
  with target.open('wb') as f:f.truncate(32*1024*1024+1)
 try:c.userdata_snapshot(data)
 except ValueError:print('C81_PASS_reject-userdata-'+kind)
 else:raise AssertionError(kind)
 if target.is_symlink():target.unlink()
 target.write_bytes(original);target.chmod(0o600)
 (data/'MUOS/preferences/extra').unlink(missing_ok=True)
 (data/'.muos-r35s-data-v1').write_bytes(c.MARKERS['.muos-r35s-data-v1'])
data.chmod(0o777)
try:c.userdata_snapshot(data)
except ValueError:print('C81_PASS_source-data-drift-default-refused')
else:raise AssertionError('default accepted777')
assert c.backup_userdata(data,stage/'userdata777.tar',source_root_mode=0o777)['source_root_mode']==0o777
print('C81_PASS_source-data-explicit777-copy')
data.chmod(0o755)
run(['debugfs','-w','-R','set_inode_field / mode 040777',str(image)])
out=stage/'drift';out.mkdir(mode=0o700)
try:c.extract_private(image,out,plan,run)
except ValueError:print('C81_PASS_source-root-drift-default-refused')
else:raise AssertionError('default root accepted777')
assert c.extract_private(image,out,plan,run,source_root_mode=0o777)['files']==rows
print('C81_PASS_source-root-explicit777-private-identity')
run(['debugfs','-w','-R','set_inode_field /etc mode 040777',str(image)])
out=stage/'drift-etc';out.mkdir(mode=0o700)
try:c.extract_private(image,out,plan,run,source_root_mode=0o777)
except ValueError:print('C81_PASS_other-parent-drift-still-refused')
else:raise AssertionError('permissive etc accepted')
'''
(stage/'filesystem-fixtures.py').write_text(fixture)
container=(work/'rootfs-container.iid').read_text().strip()
rel=lambda p:'/work/'+str(p.relative_to(work))
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id:uid=0,gid=0','--user=0',
 '--tmpfs','/tmp:rw,nosuid,nodev,size=128m','-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z',container,'python3',rel(stage/'filesystem-fixtures.py'),rel(stage)]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
for ext,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:(stage/('filesystem-fixtures.'+ext)).write_text(v)
assert r.returncode==0,(stage,r.stdout[-1200:],r.stderr[-2000:])
cases += [l.removeprefix('C81_PASS_') for l in r.stdout.splitlines() if l.startswith('C81_PASS_')]
assert len([l for l in r.stdout.splitlines() if l.startswith('C81_PASS_')])==13
sources=[Path(__file__),*[repo/'port/scripts'/name for name in ['phase4_backup_core.py','phase4-offline-backup.py','collect-phase4-offline-backup.py','prepare-phase4-offline-backup.py','phase4_root_migration.py']]]
for p in sources:ast.parse(p.read_text())
(stage/'analysis.json').write_text(json.dumps({'passed':True,'experiment':'C81_BACKUP_ONLY_CHECKS','case_count':len(cases),'cases':cases,
 'real_ext4_debugfs_fsck_and_tar_in_container':True,'physical_block_opened':False,'media_modified':False,
 'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}},indent=2)+'\n')
(area/'latest-checks').write_text(str(stage)+'\n')
print('C81 backup-only checks:',len(cases),'passed:',stage)
