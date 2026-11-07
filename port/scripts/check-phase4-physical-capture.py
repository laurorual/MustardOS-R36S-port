#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C86 guard/RO/protocol tests without a physical device or SSH."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import ast,importlib.util,json,os,stat,struct,subprocess,tempfile,types
from phase4_backup_core import sha
from phase4_candidate import sums
import phase4_root_migration as policy
import phase4_root_recovery as recovery

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'physical-capture';area.mkdir(exist_ok=True)
os.umask(0o077);stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area));cases=[]
def reject(name,call):
    try:call()
    except (ValueError,RuntimeError,OSError):cases.append(name)
    else:raise AssertionError(name)
spec=importlib.util.spec_from_file_location('physical',repo/'port/scripts/phase4-physical-capture.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
rows={n:{'sha256':recovery.hashed(b'72\n' if n==recovery.COUNTER else b'F'*64),
    'bytes':3 if n==recovery.COUNTER else 64,'mode':0o400 if n.startswith('var/lib/muos-seedrng/') else 0o644 if n.startswith('etc/') else 0o600,
    'uid':0,'gid':0,'links':1} for n in policy.PRIVATE_FILES}
ctx={'schema':86,'operation':'reference','mbr_sha256':'1'*64,'boot_prefix_16MiB_sha256':'2'*64,
    'automount_guard_sha256':'3'*64,'backup_private_files':rows,'backup_counter':72,'backup_prefix_sha256':'4'*64,'reference_root_sha256':'5'*64}
helper.validate_context(ctx,'reference',policy,recovery);cases.append('strict-reference-context')
for key,value in [('schema',85),('operation','postboot'),('mbr_sha256','bad'),('backup_counter',True),('backup_counter',73)]:
    bad=deepcopy(ctx);bad[key]=value;reject('context-'+key,lambda bad=bad:helper.validate_context(bad,'reference',policy,recovery))
bad=deepcopy(ctx);bad['extra']=True;reject('extra-context-field',lambda:helper.validate_context(bad,'reference',policy,recovery))
reject('postboot-without-intent-binding',lambda:helper.validate_context(ctx,'postboot',policy,recovery))
reject('unknown-mode-no-media-IO',lambda:helper.validate_context({**ctx,'operation':'restore'},'restore',policy,recovery))
reject('internal-entry-refuses-user-directory',lambda:helper.operation('reference'))
sys=stage/'sys';sys.mkdir()
for i,n in enumerate(['mmcblk0p1','mmcblk0p2','mmcblk0p3','mmcblk0']):
    d=sys/n;d.mkdir();(d/'dev').write_text('179:'+str(i));(d/'ro').write_text('1')
events=[];opened={};nextfd=[100]
guard=types.SimpleNamespace(SYS=sys,identity=lambda:events.append(('identity',)))
def opened_alias(path,flags):
    nextfd[0]+=1;opened[nextfd[0]]=(path,flags);events.append(('open',str(path),flags));return nextfd[0]
def fstat_alias(fd):return types.SimpleNamespace(st_mode=stat.S_IFBLK,st_rdev=os.makedev(179,['mmcblk0p1','mmcblk0p2','mmcblk0p3','mmcblk0'].index(opened[fd][0].name)))
def ioctl(fd,request,value):
    events.append(('ioctl',request,value));assert request in (0x125d,0x125e)
    if request==0x125d:assert struct.unpack('i',value)[0]==1;return 0
    return struct.pack('i',1)
with patch.object(helper,'read_protection',side_effect=lambda g,c:g.identity()),patch.object(helper.os,'open',opened_alias),patch.object(helper.os,'close'),patch.object(helper.os,'fstat',fstat_alias),patch.object(helper.fcntl,'ioctl',ioctl):
    helper.protect_aliases(guard,policy,ctx)
assert len(opened)==4 and all(flags&os.O_ACCMODE==os.O_RDONLY for p,flags in opened.values())
assert [str(p) for p,f in opened.values()]==['/dev/mmcblk0p1','/dev/mmcblk0p2','/dev/mmcblk0p3','/dev/mmcblk0']
cases+=['RO-only-descriptors-on-four-aliases','SETRO1-never-SETRO0','partition-aliases-before-whole','identity-before-kernel-protection']
with patch.object(helper,'read_protection',side_effect=lambda *a:(_ for _ in ()).throw(ValueError('no rule'))),patch.object(helper.os,'open') as op:
    reject('missing-rule-aborts-before-alias-open',lambda:helper.protect_aliases(guard,policy,ctx));assert not op.called
with patch.object(helper,'read_protection',return_value=None),patch.object(helper.os,'open',opened_alias),patch.object(helper.os,'close'),patch.object(helper.os,'fstat',fstat_alias),patch.object(helper.fcntl,'ioctl',return_value=bytes(4)):
    reject('RO-get-failure',lambda:helper.protect_aliases(guard,policy,ctx))
with patch.object(helper.fcntl,'ioctl',return_value=bytes(4)):
    reject('whole-RO-loss',lambda:helper.verify_ro(guard,42))
(sys/'mmcblk0p2/ro').write_text('0')
with patch.object(helper.fcntl,'ioctl',return_value=struct.pack('i',1)):
    reject('partition-RO-loss',lambda:helper.verify_ro(guard,42))
(sys/'mmcblk0p2/ro').write_text('1')
fence=recovery.attempt_record(rows,72,'4'*64,'6'*64,72,'a'*32)
post={**ctx,'operation':'postboot','attempt_sha256':recovery.hashed(recovery.encoded(fence))}
with patch.object(helper,'protect_aliases') as protect:
    reject('postboot-missing-sealed-intent-no-IO',lambda:helper.capture(guard,None,policy,recovery,None,post,'postboot',stage));assert not protect.called
    reject('reference-cannot-carry-intent',lambda:helper.capture(guard,None,policy,recovery,None,ctx,'reference',stage,fence));assert not protect.called
    bad=deepcopy(fence);bad['counter_floor']=71
    reject('postboot-intent-tampered-no-IO',lambda:helper.capture(guard,None,policy,recovery,None,post,'postboot',stage,bad));assert not protect.called

collector=__import__('collect-phase4-physical-capture')
manifest={'files':{'source.py':'7'*64,'context.json':'8'*64}}
receipt={'passed':True,'schema':86,'operation':'reference','context_sha256':recovery.hashed(recovery.encoded(ctx)),
    'snapshot_source_sha256':manifest['files'],'root_fsck_exit':0,'root_bytes':512*1024*1024,'boot_sequence':72,
    'root_sha256':ctx['reference_root_sha256'],'physical_postboot_capture':False,'handoff_intent_checked':False,
    'artifacts':{'root.ext4':{'bytes':512*1024*1024,'sha256':ctx['reference_root_sha256']},
        'tree.json':{'bytes':100,'sha256':'a'*64},'private-files.json':{'bytes':100,'sha256':'b'*64}}}
for n in ['all_namespaces_unmounted','alias_cache_synchronized','all_four_aliases_kernel_readonly','source_p2_double_read_verified',
    'MBR_and_16MiB_boot_prefix_preserved','root_snapshot_matches_physical_p2']:receipt[n]=True
for n in ['device_payload_written','device_writer_available','seed_generated_or_loaded','reboot_requested','userdata_mounted_or_copied']:receipt[n]=False
collector.validate(receipt,manifest,ctx);cases.append('host-receipt-reference-accepted')
for key,value in [('context_sha256','0'*64),('snapshot_source_sha256',{}),('source_p2_double_read_verified',False),
    ('device_writer_available',True),('seed_generated_or_loaded',True),('physical_postboot_capture',True),
    ('root_fsck_exit',False),('root_bytes',True),('boot_sequence',73),('root_sha256','0'*64)]:
    bad=deepcopy(receipt);bad[key]=value;reject('host-receipt-'+key,lambda bad=bad:collector.validate(bad,manifest,ctx))
bad=deepcopy(receipt);bad['artifacts']['../unknown']={'bytes':1,'sha256':'a'*64}
reject('host-artifact-traversal-or-extra',lambda:collector.validate(bad,manifest,ctx))
bad=deepcopy(receipt);bad['artifacts']['root.ext4']['bytes']=1
reject('host-short-root-artifact',lambda:collector.validate(bad,manifest,ctx))

bundle=stage/'bootstrap-bundle';bundle.mkdir(mode=0o700)
for n in helper.SOURCES:(bundle/n).write_bytes(b'fixture-only')
package={'operation':'reference','files':{n:sha(bundle/n) for n in helper.SOURCES}}
(bundle/'package.json').write_text(json.dumps(package))
class FixtureExec(Exception):pass
execs=[];roots=[];original_read=Path.read_text
def read_text(path,*args,**kwargs):return 'Jupiter' if str(path)=='/sys/class/dmi/id/product_name' else original_read(path,*args,**kwargs)
def rootdir(**kwargs):p=Path(tempfile.mkdtemp(prefix='sealed.',dir=stage));roots.append(p);return str(p)
actual_mkdtemp=tempfile.mkdtemp
def rootdir(**kwargs):p=Path(actual_mkdtemp(prefix='sealed.',dir=stage));roots.append(p);return str(p)
def intercepted(*args):execs.append(args);raise FixtureExec()
with patch.object(helper,'__file__',str(bundle/'phase4-physical-capture.py')),patch.object(helper.os,'geteuid',return_value=0),patch.object(helper.platform,'machine',return_value='x86_64'),patch.object(Path,'read_text',read_text),patch.object(helper.tempfile,'mkdtemp',rootdir),patch.object(helper.os,'execve',intercepted):
    try:helper.bootstrap('reference')
    except FixtureExec:pass
    assert execs and execs[0][1][-1]=='_reference' and execs[0][2]['LC_ALL']=='C'
    assert {p.name for p in roots[-1].iterdir()}==helper.SOURCES and all((p.stat().st_mode&0o777)==0o400 for p in roots[-1].iterdir())
    cases.append('bootstrap-seals-exact-source-set-before-clean-env-exec')
    package['operation']='postboot';(bundle/'package.json').write_text(json.dumps(package))
    reject('bootstrap-wrong-operation',lambda:helper.bootstrap('reference'))
    package['operation']='reference';(bundle/'package.json').write_text(json.dumps(package))
    (bundle/'context.json').write_bytes(b'changed');reject('bootstrap-changed-leaf-hash',lambda:helper.bootstrap('reference'))

sources=[Path(__file__),repo/'port/scripts/phase4-physical-capture.py',repo/'port/diagnostics/phase4-physical-capture-fixture.py',
    *[repo/'port/scripts'/n for n in ['phase4_backup_core.py','phase4_root_migration.py','phase4-offline-backup.py','phase4_root_recovery.py','phase4_recovery_image.py']]]
sources.extend([repo/'port/scripts/prepare-phase4-physical-capture.py',repo/'port/scripts/collect-phase4-physical-capture.py'])
source_hashes={str(p.relative_to(repo)):sha(p) for p in sources}
for n in ['recovery-image','backup-native','root-permissions']:
    proof=repo/'dist/phase4'/n
    for p,h in sums(proof/'SHA256SUMS').items():assert sha(proof/p)==h
container=(work/'rootfs-container.iid').read_text().strip()
fixture=Path((work/'recovery-image/latest-checks').read_text().strip())
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
    '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=64m',
    '-v',str(work)+':/work:rw,z','-v',str(repo/'port')+':/port:ro,z',container,'python3',
    '/port/diagnostics/phase4-physical-capture-fixture.py','/work/'+str(stage.relative_to(work)),'/work/'+str(fixture.relative_to(work))]
p=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
for ext,data in [('stdout',p.stdout),('stderr',p.stderr),('exit',str(p.returncode)+'\n')]: (stage/('fixtures.'+ext)).write_text(data)
assert p.returncode==0,(stage,p.stdout[-1200:],p.stderr[-1600:])
cases.extend(line[9:] for line in p.stdout.splitlines() if line.startswith('C86_PASS_'))
for p in sources:ast.parse(p.read_text())
assert all(sha(repo/n)==h for n,h in source_hashes.items()),'Sources changed during tests'
(stage/'analysis.json').write_text(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,
    'physical_device_or_network_contacted':False,'synthetic_protocol_guard_stubs':True,
    'real_ext4_copy_scan_and_fsck_exercised':True,'source_sha256':source_hashes},indent=2)+'\n')
(area/'latest-checks').write_text(str(stage)+'\n');print('C86 checks:',len(cases),'passed:',stage)
