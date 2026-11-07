#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C84 meaningful recovery/fault fixtures, no SSH or physical devices."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import ast,errno,json,os,stat,subprocess,tempfile
import phase4_root_recovery as r
from phase4_backup_core import sha
from phase4_root_migration import ORIGINAL_CID

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'root-recovery';area.mkdir(exist_ok=True)
os.umask(0o077);stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area));cases=[]
def reject(name,call):
    try:call()
    except (ValueError,OSError):cases.append(name)
    else:raise AssertionError(name)

def row(data,mode=0o600):return dict(sha256=r.hashed(data),mode=mode,uid=0,gid=0,links=1,bytes=len(data))
stable={n:('fixture-'+n).encode() for n in sorted(r.STABLE)}
backup={n:row(v,0o644 if n.startswith('etc/') else 0o600) for n,v in stable.items()}
backup[r.CREDIT]=row(b'old-credit'*8,0o400);backup[r.NO_CREDIT]=row(b'old-no-credit'*8,0o400);backup[r.COUNTER]=row(b'72\n')
prefix=r.hashed(b'synthetic prefix');candidate=r.hashed(b'synthetic candidate')
fence=r.attempt_record(backup,72,prefix,candidate,72,'a'*32)
observed={'attempt_id':fence['attempt_id'],'offline':True,'cid_sha256':r.DECK_CID,'capacity_sectors':r.CAPACITY,
    'root_fsck_exit':0,'root_mode':0o755,'root_sha256':r.hashed(b'fresh synthetic capture'),
    'private_files':deepcopy(backup),'boot_sequence':75,'captured_after_handoff':True}
observed['private_files'][r.COUNTER]=row(b'75\n')
observed['private_files'][r.CREDIT]=row(b'post-attempt credit'*4,0o400)
def plan(obs=None,attempt=None,source=None):return r.recovery_plan(source or backup,72,prefix,attempt or fence,obs or observed)
p=plan();assert p['recovery_counter']==76 and p['next_C07_counter']==77 and p['byte_exact_p2_restore_allowed'] is False
cases.append('higher-observed-counter-reserved-plus-one')
for name,value in [('missing',None),('bool',True),('zero',0),('negative',-1),('exhausted',9999),('string','75')]:
    x=deepcopy(observed);x['boot_sequence']=value
    reject('counter-'+name,lambda x=x:plan(x))
for key,value in [('offline',False),('captured_after_handoff',False),('attempt_id','b'*32),
    ('cid_sha256',ORIGINAL_CID),('capacity_sectors',True),
    ('capacity_sectors',r.CAPACITY-1),('root_fsck_exit',1),('root_fsck_exit',False),
    ('root_mode',0o777),('root_sha256','bad')]:
    x=deepcopy(observed);x[key]=value;reject('observation-'+key+'-'+str(value),lambda x=x:plan(x))
x=deepcopy(observed);del x['root_sha256'];reject('incomplete-fresh-capture',lambda:plan(x))
x=deepcopy(observed);x['extra']=True;reject('unrecognized-observation-member',lambda:plan(x))
for key,value in [('boot_may_have_occurred',False),('execution_enabled',True),('automatic_rollback',True),
    ('backup_prefix_sha256','0'*64),('backup_private_manifest_sha256','0'*64),('counter_floor',71),('schema',83)]:
    x=deepcopy(fence);x[key]=value;reject('fence-'+key,lambda x=x:plan(attempt=x))
x=deepcopy(fence);x.pop('counter_floor');reject('incomplete-fence',lambda:plan(attempt=x))
x=deepcopy(observed);x['boot_sequence']=71;x['private_files'][r.COUNTER]=row(b'71\n')
reject('counter-rewind-below-fence',lambda:plan(x))
for value in (9997,9998):
    x=deepcopy(observed);x['boot_sequence']=value;x['private_files'][r.COUNTER]=row(f'{value}\n'.encode())
    if value==9998:reject('reservation-exhausted',lambda:plan(x))
    else:assert plan(x)['recovery_counter']==9998;cases.append('last-reservable-counter')
x=deepcopy(observed);x['boot_sequence']=72;x['private_files'][r.COUNTER]=row(b'72\n')
assert plan(x)['recovery_counter']==73;cases.append('failed-boot-before-counter-update-still-reserved')
for field,value in [('sha256','0'*64),('mode',0o644),('uid',1),('gid',1),('links',2),('bytes',True)]:
    x=deepcopy(observed);x['private_files']['var/lib/muos-network/network.conf'][field]=value
    reject('network-identity-'+field,lambda x=x:plan(x))
x=deepcopy(observed);del x['private_files']['var/lib/muos-network/dropbear_ed25519_host_key.tmp.pub']
reject('optional-public-key-disappeared',lambda:plan(x))
x=deepcopy(observed);x['private_files']['var/lib/muos-network/.hidden']=row(b'unknown')
reject('unknown-private-member',lambda:plan(x))
x=deepcopy(observed);x['private_files'][r.COUNTER]['sha256']='0'*64
reject('counter-not-bound-to-bytes',lambda:plan(x))
x=deepcopy(backup);del x[r.CREDIT];reject('backup-without-credit-invalid-C82-binding',lambda:plan(source=x))
for members in [[],[r.NO_CREDIT],[r.CREDIT],[r.CREDIT,r.NO_CREDIT]]:
    x=deepcopy(observed)
    for n in (r.CREDIT,r.NO_CREDIT):
        if n not in members:x['private_files'].pop(n,None)
    assert plan(x)['remove_seed_paths']==[r.CREDIT,r.NO_CREDIT]
    cases.append('post-attempt-seed-set-'+str(len(members))+'-'+str(r.CREDIT in members))

events=[]
def rng(size,flags):events.append((size,flags));return bytes(range(256))
payload=r.compose_payload(p,stable,rng)
assert events==[(256,os.GRND_NONBLOCK)] and r.CREDIT not in payload and payload[r.COUNTER]==b'76\n'
assert payload[r.NO_CREDIT]==bytes(range(256)) and {n:payload[n] for n in stable}==stable
cases.append('fresh-nonblocking-no-credit-seed-network-preserved')
for name,call in [('unready',lambda *a:(_ for _ in ()).throw(BlockingIOError(errno.EAGAIN,'fixture'))),
    ('interrupted',lambda *a:(_ for _ in ()).throw(InterruptedError(errno.EINTR,'fixture'))),
    ('unsupported',lambda *a:(_ for _ in ()).throw(OSError(errno.ENOSYS,'fixture'))),('short',lambda *a:b'S'*32)]:
    count=[]
    def failed(*args,fn=call):count.append(1);return fn(*args)
    reject('rng-'+name+'-no-retry',lambda:r.compose_payload(p,stable,failed));assert count==[1]
x=deepcopy(p);x['old_seed_sha256'].append(r.hashed(bytes(range(256))))
reject('rng-old-seed-collision',lambda:r.compose_payload(x,stable,rng))
x=dict(stable);x[next(iter(x))]=b'changed';reject('stable-payload-changed',lambda:r.compose_payload(p,x,rng))
x=dict(stable);x[r.CREDIT]=b'old';reject('seed-in-stable-payload',lambda:r.compose_payload(p,x,rng))
for key,value in [('execution_enabled',True),('device_writer_available',True),('new_seed_entropy_credit_allowed',True),
    ('automatic_rollback',True),('byte_exact_p2_restore_allowed',True),('p1_mbr_p3_write_allowed',True),
    ('seed_loaded',True),('key_generation_allowed',True),('target_root_mode',0o777),('target_private_directory_mode',0o755),
    ('new_seed_path',r.CREDIT),('recovery_counter',75),('next_C07_counter',76),('old_seed_sha256',[])]:
    x=deepcopy(p);x[key]=value;reject('payload-policy-'+key,lambda x=x:r.compose_payload(x,stable,rng))

journal=stage/'journal';journal.mkdir(mode=0o700)
events=[];real_sync=os.fsync
def traced(fd):events.append('directory' if stat.S_ISDIR(os.fstat(fd).st_mode) else 'file');real_sync(fd)
with patch.object(r.os,'fsync',traced):sealed=r.seal_attempt(journal,fence)
assert events==['file','directory'] and sealed.read_bytes()==r.encoded(fence) and stat.S_IMODE(sealed.stat().st_mode)==0o400
cases.append('handoff-fence-file-then-directory-fsync')
assert r.load_attempt(journal,fence['attempt_id'],sha(sealed))==fence;cases.append('sealed-fence-readback-pinned')
reject('sealed-fence-wrong-hash',lambda:r.load_attempt(journal,fence['attempt_id'],'0'*64))
reject('sealed-fence-path-injection',lambda:r.load_attempt(journal,'../'+fence['attempt_id'],sha(sealed)))
sealed.chmod(0o600)
reject('sealed-fence-permissive-leaf',lambda:r.load_attempt(journal,fence['attempt_id'],sha(sealed)));sealed.chmod(0o400)
linked=journal/'hardlink';os.link(sealed,linked)
reject('sealed-fence-hardlink',lambda:r.load_attempt(journal,fence['attempt_id'],sha(sealed)));linked.unlink()
symlink=journal/('e'*32+'.json');symlink.symlink_to(sealed)
reject('sealed-fence-symlink',lambda:r.load_attempt(journal,'e'*32,sha(sealed)))
reject('fence-existing-never-overwritten',lambda:r.seal_attempt(journal,fence))
for step in ('file','directory'):
    f=deepcopy(fence);f['attempt_id']=('b' if step=='file' else 'c')*32
    def bad_sync(fd,when=step):
        if (stat.S_ISDIR(os.fstat(fd).st_mode))==(when=='directory'):raise OSError('fixture fsync failure')
        real_sync(fd)
    with patch.object(r.os,'fsync',bad_sync):reject('fence-'+step+'-sync-failure-no-handoff-success',lambda:r.seal_attempt(journal,f))
    assert (journal/(f['attempt_id']+'.json')).exists()
    reject('fence-'+step+'-partial-not-rearmed',lambda:r.seal_attempt(journal,f))
alias=stage/'journal-link';alias.symlink_to(journal,target_is_directory=True)
reject('fence-symlink-parent',lambda:r.seal_attempt(alias,fence))
bad=stage/'journal-open';bad.mkdir(mode=0o700);bad.chmod(0o755)
reject('fence-permissive-parent',lambda:r.seal_attempt(bad,fence))

container=(work/'rootfs-container.iid').read_text().strip();fixture=repo/'port/diagnostics/phase4-root-recovery-fixture.py'
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
    '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=64m',
    '-v',str(work)+':/work:rw,z','-v',str(repo/'port')+':/port:ro,z',container,'python3','/port/diagnostics/'+fixture.name,'/work/'+str(stage.relative_to(work))]
proc=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
for ext,data in [('stdout',proc.stdout),('stderr',proc.stderr),('exit',str(proc.returncode)+'\n')]: (stage/('fixtures.'+ext)).write_text(data)
assert proc.returncode==0,(stage,proc.stdout[-1000:],proc.stderr[-1600:])
cases.extend(line[9:] for line in proc.stdout.splitlines() if line.startswith('C84_PASS_'))
sources=[Path(__file__),repo/'port/scripts/phase4_root_recovery.py',fixture,repo/'port/scripts/phase4_root_migration.py',
    repo/'port/device/rk-r35s-p0/entropy-diagnostic/functions.sh',repo/'port/device/rk-r35s-p0/network-diagnostic/run.sh']
for path in sources:
    if path.suffix=='.py':ast.parse(path.read_text())
(stage/'analysis.json').write_text(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,
    'network_or_physical_device_contacted':False,'synthetic_data_only':True,
    'source_sha256':{str(s.relative_to(repo)):sha(s) for s in sources}},indent=2)+'\n')
(area/'latest-checks').write_text(str(stage)+'\n')
print('C84 recovery checks:',len(cases),'passed:',stage)
