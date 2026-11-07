# SPDX-License-Identifier: MIT
"""C92 fresh C79 migration image. Regular ext4 files only; no device writer.

Reuse the frozen C88 factory provisioner as an intermediate, then replace
seeds/counter under the C84 post-handoff policy. The intermediate is consumed
inside this private stage and must never be staged for a physical handoff.
"""
from pathlib import Path
import fcntl,os,stat
from phase4_backup_core import write_new,sync_dir
from phase4_root_migration import require
import phase4_initial_image as initial
import phase4_recovery_image as image
import phase4_root_recovery as recovery

def eligibility(factory,observed,candidate,backup_rows,backup_counter,prefix_sha256,
                attempt,context,observed_sha256,image_bytes):
    observation=image.observation(observed,attempt,context,observed_sha256,image_bytes)
    plan=recovery.recovery_plan(backup_rows,backup_counter,prefix_sha256,attempt,observation)
    # A migration source must be a completed, seed-rotated C07 installation.
    recovery.manifest(observed['private_files'],observed['boot_sequence'],True)
    history={n:r for n,r in observed['tree'].items() if image.historical_marker(n)}
    excluded=recovery.PRIVATE_FILES|recovery.OPTIONAL_PRIVATE|initial.NEW_DIRS|set(history)
    require({n:r for n,r in candidate['tree'].items() if n not in excluded}==
        initial.public_expected(factory,history),'Initial migration factory public tree/metadata changed')
    require({n:r for n,r in candidate['tree'].items() if image.historical_marker(n)}==history,
        'Initial migration historical markers changed')
    names=(set(observed['payloads'])-{recovery.CREDIT,recovery.NO_CREDIT})|{recovery.NO_CREDIT}
    require(set(candidate['payloads'])==names and recovery.CREDIT not in candidate['private_files'],
        'Initial migration requires only a fresh no-credit seed')
    require(candidate['boot_sequence']==plan['recovery_counter'] and
        candidate['payloads'][recovery.COUNTER]==f"{plan['recovery_counter']}\n".encode(),
        'Initial migration counter must reserve the next unused value')
    for n in recovery.STABLE&set(observed['payloads']):
        require(candidate['payloads'][n]==observed['payloads'][n] and
            candidate['private_files'][n]==observed['private_files'][n],'Initial migration stable identity changed')
    seed=candidate['payloads'][recovery.NO_CREDIT]
    require(type(seed) is bytes and len(seed)==256 and recovery.hashed(seed) not in plan['old_seed_sha256'],
        'Initial migration seed is old or not 256 bytes')
    attrs={n:v for n,v in observed['attrs'].items() if n not in (recovery.CREDIT,recovery.NO_CREDIT)}
    attrs[recovery.NO_CREDIT]=observed['attrs'].get(recovery.NO_CREDIT,observed['attrs'].get(recovery.CREDIT,{}))
    require(candidate['attrs']==attrs,'Initial migration private xattrs changed')
    for n in initial.NEW_DIRS:
        row=candidate['tree'][n]
        require(row['type']=='directory' and row['uid']==row['gid']==0 and row['mode']==0o700
            and row['links']==2 and not row['xattrs'] and not row['external_xattrs'],
            'Initial migration new private directory metadata')
    recovery.manifest(candidate['private_files'],candidate['boot_sequence'])
    return plan

def compose(factory,factory_sha256,observed_path,observed_sha256,image_bytes,stage,
            backup_rows,backup_counter,prefix_sha256,attempt,context,rng=os.getrandom):
    image.private_stage(stage)
    require(not any(stage.glob('candidate.ext4')) and not (stage/'analysis.json').exists(),
        'Initial migration stage already used; preserve partials, do not retry')
    write_new(stage/'composition-started.json',recovery.encoded({'schema':92,
        'stage_must_not_be_reused':True,'boot_handoff_record':False}))
    with image.source_image(factory,factory_sha256,image_bytes) as fd:baseline=initial.factory_scan(fd,stage)
    with image.source_image(observed_path,observed_sha256,image_bytes) as fd:observed=image.scan(fd,stage)
    observation=image.observation(observed,attempt,context,observed_sha256,image_bytes)
    plan=recovery.recovery_plan(backup_rows,backup_counter,prefix_sha256,attempt,observation)
    recovery.manifest(observed['private_files'],observed['boot_sequence'],True)
    require(not any(observed['tree'][n]['external_xattrs'] for n in image.CHANGED if n in observed['tree']),
        'External xattrs on replaced private inodes are not qualified')
    payload=recovery.compose_payload(plan,{n:v for n,v in observed['payloads'].items() if n in recovery.STABLE},rng)
    intermediate=stage/'intermediate';intermediate.mkdir(mode=0o700)
    prior=initial.compose(factory,factory_sha256,observed_path,observed_sha256,image_bytes,
        intermediate,observed['private_files'],observed['boot_sequence'])
    source=intermediate/'candidate.ext4';output=stage/'candidate.ext4'
    # This artifact is internal to C92, not the independently frozen C88 image.
    # The exclusive hardlink refuses a concurrent destination too. Consume the
    # intermediate link before opening the final output with nlink=1.
    require(not output.exists() and not output.is_symlink(),'Initial migration output exists')
    os.link(source,output,follow_symlinks=False);source.unlink();sync_dir(intermediate);sync_dir(stage)
    fd=os.open(output,os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        s=os.fstat(fd);require(stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1
            and stat.S_IMODE(s.st_mode)==0o600 and s.st_size==image_bytes,'Private intermediate metadata')
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        require(image.fd_sha(fd)==prior['candidate_sha256'],'Intermediate changed before seed replacement')
        before=image.scan(fd,stage)
        require(not any(before['tree'][n]['external_xattrs'] for n in image.CHANGED if n in before['tree']),
            'Intermediate replacement inode has external xattrs')
        for name in sorted(image.CHANGED):
            if name not in before['private_files']:continue
            for attr in before['attrs'].get(name,{}):image.debug(fd,'ea_rm /'+name+' '+attr,True)
            image.debug(fd,'rm /'+name,True)
        for index,name in enumerate([recovery.COUNTER,recovery.NO_CREDIT]):
            asset=stage/f'fresh-payload-{index}.dat';write_new(asset,payload[name])
            image.debug(fd,'write '+str(asset)+' /'+name,True);asset.unlink()
            mode=0o600 if name==recovery.COUNTER else 0o400
            image.debug(fd,'set_inode_field /'+name+' mode 0'+format(stat.S_IFREG|mode,'o'),True)
            template=name if name in observed['attrs'] else recovery.CREDIT
            for attr,value in observed['attrs'].get(template,{}).items():
                asset=stage/'attribute.dat';write_new(asset,value)
                image.debug(fd,'ea_set -f '+str(asset)+' /'+name+' '+attr,True);asset.unlink()
        os.fsync(fd);after=image.scan(fd,stage)
        eligibility(baseline,observed,after,backup_rows,backup_counter,prefix_sha256,
            attempt,context,observed_sha256,image_bytes)
        require(after['payloads']==payload,'Fresh migration payload readback changed')
        digest=image.fd_sha(fd)
    finally:os.close(fd)
    for path,wanted in [(factory,factory_sha256),(observed_path,observed_sha256)]:
        with image.source_image(path,wanted,image_bytes):pass
    # No complete C92 receipt exists until the transformed image passes fsck
    # and full readback. The intermediate receipt describes consumed bytes.
    write_new(intermediate/'consumed.json',recovery.encoded({'intermediate_consumed':True,
        'not_a_handoff_candidate':True,'seed_counter_replacement_completed':True}))
    report={'passed':True,'schema':92,'operation':'compose-initial-migration-regular-image',
        'candidate_sha256':digest,'root_bytes':image_bytes,'observed_counter':observed['boot_sequence'],
        'migration_counter':plan['recovery_counter'],'expected_first_C07_counter':plan['next_C07_counter'],
        'factory_public_tree_and_stable_identity_preserved':True,'historical_markers_preserved':True,
        'fresh_no_credit_seed_verified':True,'old_seeds_removed':True,'seed_loaded_or_credited':False,
        'root_fsck_exit':0,'source_images_unchanged':True,'physical_card_writer_available':False,
        'boot_handoff_authorized':False,'handoff_fence_created':False}
    write_new(stage/'tree.json',recovery.encoded(after['tree']))
    write_new(stage/'private-files.json',recovery.encoded(after['private_files']))
    write_new(stage/'plan.json',recovery.encoded(plan));write_new(stage/'analysis.json',recovery.encoded(report))
    return report
