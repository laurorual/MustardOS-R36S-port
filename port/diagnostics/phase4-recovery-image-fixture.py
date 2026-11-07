#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C85 synthetic regular-ext4 integration and filesystem fault cases."""
from pathlib import Path
from unittest.mock import patch
from copy import deepcopy
import importlib.util,json,os,shutil,stat,subprocess,sys
sys.path.insert(0,'/port/scripts')
import phase4_recovery_image as c
import phase4_root_recovery as r

os.umask(0o077)
stage=Path(sys.argv[1]);cases=[];size=32*1024*1024
def passed(name):cases.append(name);print('C85_PASS_'+name,flush=True)
def reject(name,fn):
    try:fn()
    except (ValueError,OSError):passed(name)
    else:raise AssertionError(name)
def run(args):
    p=subprocess.run(args,capture_output=True,text=True,timeout=40);assert p.returncode==0,(args,p.stdout[-500:],p.stderr[-600:]);return p
def folder(name):p=stage/name;p.mkdir(mode=0o700);return p

tree=folder('tree');tree.chmod(0o777)
for d in ['etc','var','var/lib','usr','usr/share']:(tree/d).mkdir(mode=0o755,exist_ok=True);(tree/d).chmod(0o755)
for d in ['muos-network','muos-seedrng','muos-diagnostic']:(tree/'var/lib'/d).mkdir(mode=0o700)
data={n:('fixture '+n).encode() for n in r.STABLE}
data.update({r.CREDIT:b'old credited seed'*4,r.NO_CREDIT:b'old no-credit seed'*4,r.COUNTER:b'72\n'})
data.update({'var/lib/muos-diagnostic/c12.used':b'MUOS-C12-ONCE\n',
    'var/lib/muos-diagnostic/c25.used.BOOT0064':b'MUOS-C25-ONCE\nBOOT=64\n'})
data.update({'usr/share/normal':b'public firmware bytes\n','usr/share/name with space':b'space-safe inode lookup\n'})
for n,v in data.items():
    p=tree/n;p.write_bytes(v);p.chmod(0o400 if n in (r.CREDIT,r.NO_CREDIT) else 0o644 if n.startswith(('etc/','usr/')) else 0o600)
(tree/'usr/share/absolute-link').symlink_to('/etc/shadow')
(tree/'usr/share/long-link').symlink_to('/'+'long-path/'*10+'nonexistent')
backup=stage/'backup.ext4'
with backup.open('xb') as f:f.truncate(size)
run(['mke2fs','-q','-t','ext4','-b','4096','-I','256','-d',str(tree),str(backup)])
def modify(image,request):run(['debugfs','-w','-R',request,str(image)])
modify(backup,'set_inode_field <2> mode 040777')
modify(backup,'ea_set /usr/share/normal user.public-guard unchanged')
modify(backup,'ea_rm /'+r.NO_CREDIT+' security.selinux')
modify(backup,'ea_set /'+r.NO_CREDIT+' user.seed-policy no-credit-required')
modify(backup,'mknod devnode c 1 3')
run(['e2fsck','-fn',str(backup)])
def hash_image(p):
    fd=os.open(p,os.O_RDONLY)
    try:return c.fd_sha(fd)
    finally:os.close(fd)
backup_hash=hash_image(backup)
with c.source_image(backup,backup_hash,size) as fd:base=c.scan(fd,folder('base-scan'),0o777)
assert base['payloads'][r.COUNTER]==b'72\n' and base['tree']['usr/share/normal']['xattrs']
assert base['tree']['usr/share/absolute-link']['target_hex']==b'/etc/shadow'.hex()
assert base['tree']['devnode']['type']=='character'
passed('inode-traversal-spaces-links-xattrs-special-files')
observed=stage/'observed.ext4';shutil.copyfile(backup,observed)
counter=stage/'counter75';counter.write_bytes(b'75\n')
for name in [r.CREDIT,r.NO_CREDIT,r.COUNTER]:
    for attr in base['attrs'].get(name,{}):modify(observed,'ea_rm /'+name+' '+attr)
for cmd in ['set_inode_field <2> mode 040755','rm /'+r.CREDIT,'rm /'+r.NO_CREDIT,'rm /'+r.COUNTER,
    'write '+str(counter)+' /'+r.COUNTER,'set_inode_field /'+r.COUNTER+' mode 0100600']:modify(observed,cmd)
run(['e2fsck','-fn',str(observed)]);observed_hash=hash_image(observed)
fence=r.attempt_record(base['private_files'],72,backup_hash,r.hashed(b'candidate fixture'),72,'f'*32)
context={'schema':85,'attempt_id':fence['attempt_id'],'attempt_sha256':r.hashed(r.encoded(fence)),
    'root_sha256':observed_hash,'root_bytes':size,'cid_sha256':r.DECK_CID,'capacity_sectors':r.CAPACITY,
    'offline':True,'all_namespaces_unmounted':True,'alias_cache_synchronized':True,'captured_after_handoff':True}
captured,obs=c.collect_postboot(observed,observed_hash,size,folder('observation'),fence,context)
assert obs['boot_sequence']==75 and not any(n in obs['private_files'] for n in (r.CREDIT,r.NO_CREDIT))
passed('counter75-and-missing-seeds-derived-from-actual-image')
for key,value in [('cid_sha256','0'*64),('attempt_sha256','0'*64),('root_sha256','0'*64),('root_bytes',True),
    ('offline',False),('all_namespaces_unmounted',False),('alias_cache_synchronized',False),('captured_after_handoff',False)]:
    x=dict(context);x[key]=value
    reject('capture-binding-'+key,lambda x=x:c.observation(captured,fence,x,observed_hash,size))

def compose(dest,ctx=context):
    return c.compose(backup,backup_hash,observed,observed_hash,size,dest,base['private_files'],72,backup_hash,
        fence,ctx,backup_root_mode=0o777,rng=lambda n,f:bytes(range(256)))
output=folder('composition');result=compose(output)
assert result['recovery_counter']==76 and result['root_fsck_exit']==0 and hash_image(backup)==backup_hash and hash_image(observed)==observed_hash
with c.source_image(output/'recovery.ext4',result['root_image_sha256'],size) as fd:after=c.scan(fd,folder('post-readback'))
assert c.public_tree(base)==c.public_tree(after) and after['payloads'][r.COUNTER]==b'76\n'
assert after['private_files'][r.NO_CREDIT]['mode']==0o400 and after['payloads'][r.NO_CREDIT]==bytes(range(256)) and r.CREDIT not in after['private_files']
assert after['attrs'][r.NO_CREDIT].get('user.seed-policy')==b'no-credit-required'
assert after['tree']['var/lib/muos-diagnostic/c12.used']==base['tree']['var/lib/muos-diagnostic/c12.used']
passed('consumed-C12-and-C25-markers-preserved-never-rearmed')
passed('regular-clone-recovery-fsck0-public-metadata-and-identity-unchanged')
passed('old-seeds-removed-new-no-credit0400-counter76-xattrs-preserved')
assert not (output/'scratch.dat').exists() and not list(output.glob('payload-*.dat')) and not (output/'attribute.dat').exists()
passed('successful-composition-removes-temporary-private-payloads')
external=stage/'external-private-ea.ext4';shutil.copyfile(backup,external)
modify(external,'ea_set /'+r.CREDIT+' user.large '+'x'*1024)
external_hash=hash_image(external);dest=folder('external-private-ea-refused')
reject('external-EA-on-replaced-private-inode-refused-before-clone',lambda:c.compose(external,external_hash,observed,
    observed_hash,size,dest,base['private_files'],72,backup_hash,fence,context,backup_root_mode=0o777))
assert not (dest/'recovery.ext4').exists() and hash_image(external)==external_hash

reject('source0777-rejected-as-postboot',lambda:c.collect_postboot(backup,backup_hash,size,folder('bad-root'),fence,context))
bad_context=dict(context);bad_context['captured_after_handoff']=False
dest=folder('no-handoff');reject('pre-handoff-source-never-recovery',lambda:compose(dest,bad_context));assert not (dest/'analysis.json').exists()
dest=folder('existing-output');(dest/'recovery.ext4').write_bytes(b'keep')
reject('existing-image-never-overwritten',lambda:compose(dest));assert (dest/'recovery.ext4').read_bytes()==b'keep'
alias=stage/'alias.ext4';alias.symlink_to(backup)
def opening(p,h=backup_hash,bytes_=size):
    with c.source_image(p,h,bytes_) as fd:pass
reject('source-symlink',lambda:opening(alias))
hard=stage/'hardlink.ext4';os.link(backup,hard);reject('source-hardlink',lambda:opening(backup));hard.unlink()
reject('source-wrong-hash',lambda:opening(backup,'0'*64))
reject('source-wrong-size',lambda:opening(backup,backup_hash,512*1024*1024))
backup.chmod(0o644);reject('source-world-readable',lambda:opening(backup));backup.chmod(0o600)
with patch.object(c.os,'fstat',return_value=type('S',(),{'st_mode':stat.S_IFBLK})()):
    reject('source-block-descriptor-refused',lambda:opening(backup))

# Failures must not publish a completion receipt; source images remain exact.
for name,request in [('unknown-private','write '+str(counter)+' /var/lib/muos-network/.unknown'),
                     ('runtime-token','write '+str(counter)+' /var/lib/muos-diagnostic/c12.once'),
                     ('bad-consumed-token','write '+str(counter)+' /var/lib/muos-diagnostic/c25.used.BOOT0070')]:
    image=stage/(name+'.ext4');shutil.copyfile(observed,image);modify(image,request)
    h=hash_image(image);ctx=dict(context);ctx['root_sha256']=h
    reject(name,lambda image=image,h=h,ctx=ctx:c.collect_postboot(image,h,size,folder(name+'-scan'),fence,ctx))
dest=folder('short-clone')
with patch.object(c.os,'pwrite',return_value=1):reject('short-clone-write-no-retry',lambda:compose(dest))
assert not (dest/'analysis.json').exists()
dest=folder('fsync-failure')
with patch.object(c.os,'fsync',side_effect=OSError('fixture sync error')):reject('clone-fsync-failure-no-completion',lambda:compose(dest))
assert not (dest/'analysis.json').exists()
original_debug=c.debug;injected=[]
def corrupting(fd,request,writable=False):
    text=original_debug(fd,request,writable)
    if writable and request.startswith('write ') and not injected:
        original_debug(fd,'set_inode_field /usr/share/normal mode 0100600',True);injected.append(1)
    return text
dest=folder('unintended-public-change')
with patch.object(c,'debug',corrupting):reject('unintended-public-change-detected-before-completion',lambda:compose(dest))
assert injected and not (dest/'analysis.json').exists()
assert hash_image(backup)==backup_hash and hash_image(observed)==observed_hash
passed('all-fault-cases-preserved-both-source-images')
spec=importlib.util.spec_from_file_location('consumer','/port/scripts/phase4-recovery-image.py')
consumer=importlib.util.module_from_spec(spec);spec.loader.exec_module(consumer)
reference={'operation':'reference','backup_image':str(backup),'backup_sha256':backup_hash,
    'backup_private_files':base['private_files'],'backup_counter':72,'backup_root_mode':0o777}
for name,change in [('rejects-32MiB-in-production',{}),('unknown-operation',{'operation':'restore'}),
    ('unknown-request-member',{'unknown':True}),('outside-work-path',{'backup_image':'/dev/mmcblk0p2'})]:
    dest=folder('entry-'+name);request=dest/'request.json';request.write_text(json.dumps({**reference,**change}));request.chmod(0o600)
    reject('entrypoint-'+name,lambda request=request,dest=dest:consumer.main(request,dest))
dest=folder('entry-permissive');request=dest/'request.json';request.write_text(json.dumps(reference));request.chmod(0o644)
reject('entrypoint-permissive-request',lambda:consumer.main(request,dest))
(stage/'fixture-results.json').write_text(json.dumps({'passed':True,'cases':cases,'case_count':len(cases)},indent=2)+'\n')
