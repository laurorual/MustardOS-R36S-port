#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C94 finite transport, collector and observer failure paths; no SSH/media."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
from types import SimpleNamespace
import importlib,json,os,stat,subprocess,sys
sys.path.insert(0,'/port/scripts')
import phase4_backup_core as core
import phase4_root_recovery as recovery
import phase4_root_migration as policy
prep=importlib.import_module('prepare-phase4-p2-initial')
collector=importlib.import_module('collect-phase4-p2-initial')
watch=importlib.import_module('watch-phase4-p2-initial')
os.umask(0o077);stage=Path(sys.argv[1]);prior=Path(sys.argv[2]);cases=[]
def passed(name):cases.append(name);print('C94_TRANSPORT_PASS_'+name,flush=True)
def reject(name,call):
    try:call()
    except (ValueError,OSError,KeyError,TypeError):passed(name)
    else:raise AssertionError(name)
def folder(name):p=stage/name;p.mkdir(mode=0o700);return p
def put(path,value):path.write_bytes(recovery.encoded(value))
backup={}
for n in recovery.STABLE|{recovery.CREDIT,recovery.COUNTER}:
    p=prior/'observed-tree'/n
    if not p.is_file():continue
    raw=p.read_bytes() if n not in {recovery.CREDIT,recovery.COUNTER} else b'B'*256 if n==recovery.CREDIT else b'72\n'
    backup[n]={'sha256':recovery.hashed(raw),'bytes':len(raw),'mode':stat.S_IMODE(p.stat().st_mode),'uid':0,'gid':0,'links':1}
attempt=recovery.attempt_record(backup,72,'a'*64,'b'*64,74,'c'*32)
physical={'backup_private_files':backup,'backup_counter':72,'backup_prefix_sha256':'a'*64,
    'attempt_sha256':recovery.hashed(recovery.encoded(attempt)),'automount_guard_sha256':'4'*64}

# Positive completed-composition gate plus tampering. The small regular
# candidate exercises the guarded source reader; no factory/image composer is
# rerun here. Fixed production size is retained outside this isolated patch.
composition=folder('composition');capture=folder('capture');package=folder('capture-package');held=folder('held')
factory=stage/'factory.ext4';factory.write_bytes(b'factory fixture')
candidate=composition/'candidate.ext4'
with candidate.open('xb') as f:f.write(b'candidate fixture');f.truncate(32*1024*1024)
put(held/'host-copy.json',{'synthetic':True})
scanctx={'synthetic_capture_context':True}
value={'factory':factory,'capture':capture,'capture_package':package,'held':held,'known_boot':75,
    'attempt':attempt,'physical':physical,'held_ack':{'next_attempt_sha256':physical['attempt_sha256']},
    'native':{'root_sha256':'5'*64,'boot_sequence':75},'capture_context':scanctx}
request={'factory_image':'/work/factory.ext4','factory_sha256':prep.helper.C79_FACTORY_SHA256,
    'observed_image':'/work/capture/root.ext4','observed_sha256':'5'*64,'capture_context':scanctx,
    **{n:physical[n] for n in ['backup_private_files','backup_counter','backup_prefix_sha256']},
    'attempt_directory':'/work/held/handoff','attempt_id':attempt['attempt_id'],'attempt_sha256':physical['attempt_sha256']}
r={'passed':True,'schema':92,'operation':'compose-initial-migration-regular-image','root_bytes':candidate.stat().st_size,
    'root_fsck_exit':0,'observed_counter':75,'migration_counter':76,'expected_first_C07_counter':77,
    'candidate_sha256':core.sha(candidate)}
for n in ['factory_public_tree_and_stable_identity_preserved','historical_markers_preserved','fresh_no_credit_seed_verified','old_seeds_removed','source_images_unchanged']:r[n]=True
for n in ['seed_loaded_or_credited','physical_card_writer_available','boot_handoff_authorized','handoff_fence_created']:r[n]=False
host={'passed':True,'schema':93,'source_sha256':{},'capture':str(capture),'capture_package':str(package),'held_recovery':str(held),
    'held_recovery_ack_sha256':core.sha(held/'host-copy.json'),'known_boot_floor':75,'independent_host_backup_artifacts_reverified':True}
def composed(report=r,req=request,h=host):
    h=deepcopy(h);put(composition/'analysis.json',report);put(composition/'request.json',req)
    h.update(consumer_analysis_sha256=core.sha(composition/'analysis.json'),request_sha256=core.sha(composition/'request.json'))
    put(composition/'host-analysis.json',h)
    with patch.object(prep.initial,'latest',return_value=composition),patch.object(prep,'WORK',stage),patch.object(prep,'ROOT_BYTES',candidate.stat().st_size):
        return prep.composed(value)
assert composed()[1]['migration_counter']==76;passed('completed-composition-role-capture-fence-and-counter-gate')
for name,change in [('old-candidate-counter',lambda x:x.update(migration_counter=75)),
    ('wrong-first-boot',lambda x:x.update(expected_first_C07_counter=78)),('bad-fsck',lambda x:x.update(root_fsck_exit=1)),
    ('missing-seed-replacement',lambda x:x.update(fresh_no_credit_seed_verified=False)),
    ('composer-claimed-card-write',lambda x:x.update(physical_card_writer_available=True)),
    ('composer-claimed-boot-handoff',lambda x:x.update(boot_handoff_authorized=True)),
    ('candidate-bytes-tampered',lambda x:x.update(candidate_sha256='0'*64))]:
    bad=deepcopy(r);change(bad);reject(name,lambda bad=bad:composed(report=bad))
bad=deepcopy(request);bad['factory_image']='/work/candidate.ext4';reject('swapped-factory-role',lambda:composed(req=bad))
bad=deepcopy(host);bad['held_recovery_ack_sha256']='0'*64;reject('changed-current-fence-host-copy',lambda:composed(h=bad))
with patch.object(prep.initial,'inputs',side_effect=ValueError('stale capture before SSH')) as gate,\
     patch.object(prep.initial.legacy.prep.prep,'transport',side_effect=AssertionError('SSH must not start')):
    reject('current-input-gate-precedes-transport',lambda:prep.main('not-contacted'))
assert gate.call_count==1;passed('stale-input-no-package-claim-or-transfer')

# Execute the actual receiver scripts against regular files. Substitute only
# off-card discovery and 512MiB -> 4MiB fixture size, preserving stream/readback
# implementation, sparse writes, exclusivity, fsync and finite leaf roles.
parent=folder('receiver-parent');blocks=folder('no-blocks');payload=b'C94 fixture\n'+bytes(4*1024*1024-12)
# Keep exact fixture length regardless of text length.
payload=payload[:4*1024*1024];wanted=recovery.hashed(payload)
def receive(role,data=payload,digest=wanted):
    script=prep.receiver(role).replace('size=512*1024*1024','size=4*1024*1024').replace("Path('/home/deck')",'Path('+repr(str(parent))+')')
    script=script.replace("Path('/sys/class/block')",'Path('+repr(str(blocks))+')')
    script=script.replace("subprocess.run(['findmnt','-rn','-T',str(parent),'-o','FSTYPE,MAJ:MIN'],capture_output=True,text=True,check=True).stdout.split()","['ext4','8:1']")
    return subprocess.run([sys.executable,'-c',script,digest,'76'],input=data,capture_output=True,timeout=30)
for role in ['factory','candidate']:
    result=receive(role);assert result.returncode==0,result.stderr
    receipt=json.loads(result.stdout);p=Path(receipt['stage'])/(role+'.ext4')
    assert receipt['role']==role and receipt['schema']==94 and receipt['image_sha256']==wanted
    assert receipt['migration_counter_binding']==76 and receipt['physical_media_opened_or_written'] is False
    assert core.sha(p)==wanted and stat.S_IMODE(p.stat().st_mode)==0o600 and p.stat().st_nlink==1
    assert p.parent.name.startswith('muos-r35s-c94-'+role+'.');passed('private-'+role+'-stream-and-full-readback')
for name,data,digest in [('short-transport',payload[:-1],wanted),('trailing-transport-byte',payload+b'x',wanted),('transport-hash-mismatch',payload,'0'*64)]:
    before=set(parent.glob('*/staged.json'));result=receive('candidate',data,digest)
    assert result.returncode!=0 and set(parent.glob('*/staged.json'))==before;passed(name+'-without-completion')
reject('no-arbitrary-receiver-role',lambda:prep.receiver('recovery'))

# Native report/journal/next fence validator; only the pure C89 validator is
# reused. It never reaches C89's writer or eligibility operation.
ctx={'factory_sha256':prep.helper.C79_FACTORY_SHA256,'candidate_sha256':'6'*64,'expected_observed_sha256':'5'*64,
    'expected_migration_counter':76,'next_attempt_id':'d'*32,'physical_capture':physical}
intent=recovery.attempt_record(backup,72,'a'*64,'6'*64,76,'d'*32)
manifest={'files':{'synthetic.py':'7'*64}}
report={'passed':True,'schema':94,'operation':'migrate-initial-p2-only','factory_sha256':prep.helper.C79_FACTORY_SHA256,
    'candidate_sha256':'6'*64,'migration_counter':76,'written_bytes':policy.ROOT_BYTES,'source_sha256':manifest['files'],
    'next_attempt_id':'d'*32,'next_attempt_sha256':recovery.hashed(recovery.encoded(intent)),
    'prior_attempt_sha256':physical['attempt_sha256'],'boot_handoff_authorized':False,'physical_boot_after_initial_migration_qualified':False}
for n in ['pinned_C79_factory_verified','recovery_and_first_boot_qualification_checked','physical_card_p2_written',
    'p1_MBR_p3_full_complement_preserved','all_four_aliases_kernel_readonly','fresh_capture_and_three_image_scans_verified',
    'new_no_credit_seed_verified_not_loaded','independent_host_copy_of_next_fence_required']:report[n]=True
journal={}
for n,kind in [('unlock-intent','P2_UNLOCK_MAY_HAVE_STARTED'),('write-intent','P2_WRITE_MAY_HAVE_STARTED'),('complete','P2_WRITE_VERIFIED')]:
    journal[n]={'kind':kind,'offset':policy.ROOT_OFFSET,'bytes':policy.ROOT_BYTES,'source_sha256':'6'*64,'previous_sha256':'5'*64}
journal['unlock-intent']['protected_sha256']=['8'*64,'9'*64]
journal['complete'].update(sha256='6'*64,boot_handoff_authorized=False,all_four_aliases_kernel_readonly=True,alias_cache_synchronized=True,protected_complement_verified=True)
collector.validate(report,ctx,manifest,journal,intent);passed('native-initial-receipt-extent-protection-and-fence-verified')
for name,change in [('recovery-operation-rejected',lambda r,j,i:r.update(operation='recover-p2-only')),
    ('native-unpinned-factory',lambda r,j,i:r.update(factory_sha256='0'*64)),
    ('native-boot-unqualified-required',lambda r,j,i:r.update(physical_boot_after_initial_migration_qualified=True)),
    ('native-p1-extent-rejected',lambda r,j,i:j['write-intent'].update(offset=32768*512)),
    ('native-full-complement-required',lambda r,j,i:j['unlock-intent'].update(protected_sha256=['8'*64])),
    ('native-cold-readback-required',lambda r,j,i:j['complete'].update(alias_cache_synchronized=False)),
    ('native-RO-required',lambda r,j,i:j['complete'].update(all_four_aliases_kernel_readonly=False)),
    ('native-fence-counter-binding',lambda r,j,i:i.update(counter_floor=75)),
    ('native-fence-hash-binding',lambda r,j,i:r.update(next_attempt_sha256='0'*64)),
    ('native-source-code-binding',lambda r,j,i:r.update(source_sha256={})),
    ('no-premature-handoff',lambda r,j,i:r.update(boot_handoff_authorized=True))]:
    bad,j,i=map(deepcopy,[report,journal,intent]);change(bad,j,i)
    reject(name,lambda bad=bad,j=j,i=i:collector.validate(bad,ctx,manifest,j,i))

base={'cid_sha256':policy.DECK_CID,'capacity_sectors':policy.CAPACITY,'kernel':'fixture-kernel',
    'guard_sha256':'4'*64,'ro':[1,1,1,1],'root_helpers':['muos-r35s-c94.12345678'],'owned_complete':False,
    'failures':[],'read_bytes':1024,'write_bytes':0}
context={'qualified_kernel':'fixture-kernel','physical_capture':physical};helper='muos-r35s-c94.12345678'
assert watch.monitor.state_action(base,helper,context)=='wait';passed('observer-waits-for-existing-initial-helper')
for name,change in [('observer-foreign-card',lambda x:x.update(cid_sha256='0'*64)),
    ('observer-changed-kernel',lambda x:x.update(kernel='other')),
    ('observer-failed-attempt',lambda x:x.update(failures=['failure'])),
    ('observer-missing-helper',lambda x:x.update(root_helpers=[])),
    ('observer-unexpected-writable-p3',lambda x:x.update(ro=[0,1,0,0]))]:
    bad=deepcopy(base);change(bad);reject(name,lambda bad=bad:watch.monitor.state_action(bad,helper,context))
complete=dict(base,owned_complete=True,root_helpers=[]);assert watch.monitor.state_action(complete,helper,context)=='collect'
passed('observer-collects-only-RO-completion-without-root-helper')
events=[];values=iter([base,complete]);clock=[0]
def sleep(n):clock[0]+=n
watch.monitor.observe(folder('observer-success'),lambda:next(values),lambda:events.append('collect'),lambda:events.append('proof'),helper,context,
    seconds=60,interval=1,now=lambda:clock[0],sleep=sleep)
assert events==['collect','proof'];passed('observer-collects-and-publishes-exactly-once')
where=folder('observer-failure');events.clear()
def failed_collect():events.append('collect');raise OSError('SSH interrupted')
reject('observer-no-collection-retry',lambda:watch.monitor.observe(where,lambda:complete,failed_collect,lambda:events.append('proof'),helper,context))
assert events==['collect'] and not (where/'complete.json').exists()
claims=folder('claims');watch.claim(claims);reject('exclusive-observer-claim',lambda:watch.claim(claims))
assert 'c89-recovery' not in watch.STATUS and 'c94-initial' in watch.STATUS and 'c94-failure' in watch.STATUS
assert 'c89-recovery' not in collector.FETCH and 'c94-initial' in collector.FETCH;passed('finite-initial-observer-and-fetch-paths')
for p in stage.rglob('*.ext4'):p.unlink()
put(stage/'fixture-results.json',{'passed':True,'case_count':len(cases),'cases':cases,
    'regular_file_receivers_and_collector_observer_executed':True,'physical_media_discovery_and_SSH_stubbed':True,
    'production_512MiB_candidate_or_native_writer_executed':False})
