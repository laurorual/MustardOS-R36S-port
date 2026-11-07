#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C84 container-only ext4 composition and entropy-policy fixture, synthetic."""
from pathlib import Path
import hashlib,json,os,shlex,shutil,stat,subprocess,sys
sys.path.insert(0,'/port/scripts')
import phase4_root_recovery as r

stage=Path(sys.argv[1]);tree=stage/'base-tree';tree.mkdir(mode=0o755);tree.chmod(0o777)
def run(args):
    proc=subprocess.run(args,capture_output=True,text=True,timeout=45)
    assert proc.returncode==0,(args,proc.stdout[-800:],proc.stderr[-800:])
    return proc
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def source(name,data,mode):
    p=tree/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(data);p.chmod(mode)
for name in sorted(r.STABLE):source(name,('synthetic '+name).encode(),0o644 if name.startswith('etc/') else 0o600)
source(r.CREDIT,b'backup credit'*8,0o400);source(r.NO_CREDIT,b'backup no-credit'*8,0o400);source(r.COUNTER,b'72\n',0o600)
source('usr/share/public-sentinel',b'firmware public bytes unchanged\n',0o644)
source('usr/bin/tool',b'#!/bin/sh\nexit 0\n',0o755)
(tree/'usr/bin/tool-link').symlink_to('tool')
for n in ['etc','var','var/lib','usr','usr/share','usr/bin']:(tree/n).chmod(0o755)
for n in ['muos-network','muos-seedrng','muos-diagnostic']:(tree/'var/lib'/n).chmod(0o700)
backup=stage/'backup.ext4'
with backup.open('xb') as f:f.truncate(32*1024*1024)
run(['mke2fs','-q','-t','ext4','-b','4096','-I','256','-d',str(tree),str(backup)])
run(['e2fsck','-fn',str(backup)]);backup_sha=sha(backup)

def edit(image,commands,label):
    f=stage/(label+'.commands');f.write_text('\n'.join(commands)+'\n')
    proc=run(['debugfs','-w','-f',str(f),str(image)])
    assert 'File not found' not in proc.stdout+proc.stderr and 'already exists' not in proc.stdout+proc.stderr
    run(['e2fsck','-fn',str(image)])
def extract(image,label):
    root=stage/label;root.mkdir(mode=0o700)
    run(['debugfs','-R','rdump / '+str(root),str(image)])
    return root
def manifest(root):
    rows={}
    for name in sorted(r.PRIVATE_FILES|r.OPTIONAL_PRIVATE):
        p=root/name
        if not p.exists():continue
        s=p.lstat();assert stat.S_ISREG(s.st_mode)
        rows[name]={'sha256':sha(p),'mode':stat.S_IMODE(s.st_mode),'uid':s.st_uid,'gid':s.st_gid,'links':s.st_nlink,'bytes':s.st_size}
    return rows
def inventory(root):
    result={}
    for p in sorted(root.rglob('*')):
        s=p.lstat();name=str(p.relative_to(root))
        data=os.readlink(p) if stat.S_ISLNK(s.st_mode) else sha(p) if stat.S_ISREG(s.st_mode) else None
        result[name]=(stat.S_IFMT(s.st_mode),stat.S_IMODE(s.st_mode),s.st_uid,s.st_gid,data)
    return result

# A new offline observation comes from a separate real regular ext4 image.
observed_image=stage/'observed.ext4';shutil.copyfile(backup,observed_image)
counter75=stage/'counter75';counter75.write_bytes(b'75\n')
edit(observed_image,['set_inode_field <2> mode 040755','rm /'+r.COUNTER,
    'write '+str(counter75)+' /'+r.COUNTER,'set_inode_field /'+r.COUNTER+' mode 0100600',
    'rm /'+r.CREDIT,'rm /'+r.NO_CREDIT],'observed')
old=extract(backup,'backup-extracted');current=extract(observed_image,'observed-extracted')
assert stat.S_IMODE(current.stat().st_mode)==0o755
rows=manifest(old);fresh=manifest(current)
fence=r.attempt_record(rows,72,backup_sha,r.hashed(b'synthetic candidate before boot'),72,'d'*32)
observation={'attempt_id':fence['attempt_id'],'offline':True,'cid_sha256':r.DECK_CID,'capacity_sectors':r.CAPACITY,
    'root_fsck_exit':0,'root_mode':0o755,'root_sha256':sha(observed_image),'private_files':fresh,
    'boot_sequence':75,'captured_after_handoff':True}
plan=r.recovery_plan(rows,72,backup_sha,fence,observation)
payload=r.compose_payload(plan,{n:(old/n).read_bytes() for n in rows if n in r.STABLE},lambda n,flags:bytes(range(256)))
assert payload[r.COUNTER]==b'76\n' and r.CREDIT not in payload
print('C84_PASS_real-ext4-observed-counter-and-seedless-capture')

# Only a regular clone is changed. No block device or host mount is involved.
image=stage/'recovery.ext4';shutil.copyfile(backup,image)
commands=['set_inode_field <2> mode 040755','rm /'+r.CREDIT,'rm /'+r.NO_CREDIT,'rm /'+r.COUNTER]
for index,name in enumerate([r.COUNTER,r.NO_CREDIT]):
    p=stage/('payload-%02d.dat'%index);p.write_bytes(payload[name])
    mode=0o400 if name==r.NO_CREDIT else 0o600
    commands+=['write '+str(p)+' /'+name,'set_inode_field /'+name+' mode 0'+format(0o100000|mode,'o')]
edit(image,commands,'recovery')
recovered=extract(image,'recovery-extracted');actual=manifest(recovered)
assert stat.S_IMODE(recovered.stat().st_mode)==0o755 and actual[r.NO_CREDIT]['mode']==0o400 and r.CREDIT not in actual
assert (recovered/r.COUNTER).read_bytes()==b'76\n' and (recovered/r.NO_CREDIT).read_bytes()==bytes(range(256))
assert sha(backup)==backup_sha
print('C84_PASS_real-ext4-recovery-fsck0-modes-counter-new-no-credit-backup-unchanged')
before=inventory(old);after=inventory(recovered)
for name in {r.CREDIT,r.NO_CREDIT,r.COUNTER}:before.pop(name,None);after.pop(name,None)
assert before==after
print('C84_PASS_real-ext4-entire-public-tree-and-network-identity-preserved')

# Run the installed policy library. Native SeedRNG and readiness are stubs:
# absolutely no entropy is loaded/credited into the container/host kernel.
entropy=stage/'entropy-fixture';entropy.mkdir(mode=0o700)
seed=entropy/'seed';seed.mkdir(mode=0o700)
(seed/'seed.no-credit').write_bytes((recovered/r.NO_CREDIT).read_bytes());(seed/'seed.no-credit').chmod(0o400)
probe=entropy/'probe';probe.write_text('#!/bin/sh\necho "$1" >> '+shlex.quote(str(entropy/'probe-calls'))+'\necho rng_ready=1 wait_ms=0\n');probe.chmod(0o755)
native=entropy/'native';native.write_text('''#!/usr/bin/python3
from pathlib import Path
import os,sys
p=Path(__file__).parent/'seed'
assert sys.argv[1]=='start' and not (p/'seed.credit').exists()
assert (p/'seed.no-credit').read_bytes()==bytes(range(256))
print('Seeding 2048 bits without crediting')
(p/'seed.no-credit').unlink()
(p/'seed.credit').write_bytes(b'N'*64);(p/'seed.credit').chmod(0o400)
print('Saving 512 bits of creditable seed for next boot')
''');native.chmod(0o755)
script='\n'.join('export '+k+'='+shlex.quote(str(v)) for k,v in {
    'seed_dir':seed,'entropy_state':entropy/'state','seed_uid':0,'seed_gid':0,'rng_probe':probe,'native_seedrng':native}.items())
script+='\n. /port/device/rk-r35s-p0/entropy-diagnostic/functions.sh\nentropy_start\n'
run(['/bin/sh','-ec',script])
assert (entropy/'state/ready').is_file() and (entropy/'state/mode').read_text().strip()=='seedless'
assert (entropy/'probe-calls').read_text().splitlines()==['0','60']
assert (entropy/'state/start.log').read_text().splitlines()[0]=='Seeding 2048 bits without crediting'
print('C84_PASS_actual-entropy-policy-waits-ready-and-consumes-no-credit-with-stub-only')
