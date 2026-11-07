#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C80 pure migration policy fixtures: synthetic records, no device IO or secrets."""
from pathlib import Path
import copy, hashlib, json, struct, tempfile
from phase4_candidate import sha
from phase4_card_image import mbr_bytes
from phase4_root_migration import *

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/root-migration';area.mkdir(exist_ok=True)
h=lambda s:hashlib.sha256(s.encode()).hexdigest()
mbr=bytearray(mbr_bytes())
struct.pack_into('<B3sB3sII',mbr,478,0,b'\xfe\xff\xff',0x83,b'\xfe\xff\xff',1310720,248561664)
mbr=bytes(mbr)
rows={}
for name in PRIVATE_FILES|OPTIONAL_PRIVATE:
 mode=0o400 if name.startswith('var/lib/muos-seedrng/') else 0o644 if name=='etc/muos-network-authorized_key' else 0o600
 rows[name]={'mode':mode,'uid':0,'gid':0,'links':1,'bytes':256 if 'seed.' in name else 64,'sha256':h('synthetic '+name)}
rows['var/lib/muos-diagnostic/boot-seq'].update(bytes=3,sha256=h('72\n'))
survey={'cid_sha256':R35S_CID,'original_present':False,'capacity_sectors':CAPACITY,'sector_bytes':512,
 'model':'R36S-V12 2023-08-18 Panel 0','kernel':'4.4.189-muos-r35s-p4','root_partuuid':'4d554432-02',
 'data_partuuid':'4d554432-03','root_ro':True,'quiet':True,'p3_mounted':False,'boot_sequence':72,
 'boot_prefix_16MiB_sha256':h('synthetic boot prefix'),'private_files':rows}
factory={'passed':True,'experiment':'C79_PRIVATE_GAMBATTE_PANEL0_CARD_IMAGE','image_bytes':PREFIX_BYTES,
 'partition_count':2,'gambatte_core_included':True,'userdata_partition_included':False,
 'regions':{'rootfs.ext4':{'offset':ROOT_OFFSET,'bytes':ROOT_BYTES,'sha256':h('synthetic factory root')}},
 'image_sha256':h('synthetic factory card'),'core_sha256':h('synthetic core')}
plan=make_plan(mbr,survey,factory)
assert plan['proposed_write']=={'partition':2,'offset':134217728,'bytes':536870912}
assert plan['protected_ranges']==[{'offset':0,'bytes':134217728},{'offset':671088640,'bytes':127263571968}]
assert sum(r['bytes'] for r in plan['protected_ranges'])+plan['proposed_write']['bytes']==CAPACITY*512
assert not plan['execution_enabled'] and not plan['device_writer_available'] and not plan['raw_factory_whole_card_write_allowed']
cases=['valid-three-partition-plan','only-p2-range-entire-card-coverage']
def rejects(name,op):
 try:op()
 except (ValueError,KeyError,TypeError):cases.append(name)
 else:raise AssertionError(name)
for key,value in [('cid_sha256',ORIGINAL_CID),('cid_sha256',DECK_CID),('original_present',True),
 ('capacity_sectors',True),('capacity_sectors',CAPACITY-1),('sector_bytes',4096),('model','other panel'),
 ('kernel','other kernel'),('root_partuuid','4d554432-01'),('data_partuuid','4d554432-02'),
 ('root_ro',False),('quiet',False),('p3_mounted',True),('boot_sequence',True),('boot_sequence',0),
 ('boot_sequence',9999),('boot_prefix_16MiB_sha256','x'*64)]:
 s=copy.deepcopy(survey);s[key]=value
 rejects('reject-survey-'+key+'-'+str(len(cases)),lambda:make_plan(mbr,s,factory))
for offset in [440,446,450,454,470,486,494,510]:
 altered=bytearray(mbr);altered[offset]^=1
 rejects('reject-MBR-byte-'+str(offset),lambda:make_plan(bytes(altered),survey,factory))
rejects('reject-two-partition-factory-as-live-card',lambda:make_plan(mbr_bytes(),survey,factory))
for label,edit in [
 ('missing-seed',lambda r:r.pop('var/lib/muos-seedrng/seed.credit')),
 ('unexpected-path',lambda r:r.update({'var/lib/muos-diagnostic/c25.once':dict(next(iter(r.values())))})),
 ('seed-writable',lambda r:r['var/lib/muos-seedrng/seed.credit'].update(mode=0o600)),
 ('seed-short',lambda r:r['var/lib/muos-seedrng/seed.credit'].update(bytes=16)),
 ('public-key-wrong-mode',lambda r:r['etc/muos-network-authorized_key'].update(mode=0o600)),
 ('host-key-hardlink',lambda r:r['var/lib/muos-network/dropbear_ed25519_host_key'].update(links=2)),
 ('network-wrong-owner',lambda r:r['var/lib/muos-network/network.conf'].update(uid=1000)),
 ('counter-hash-drift',lambda r:r['var/lib/muos-diagnostic/boot-seq'].update(sha256=h('0\n'))),
 ('counter-length-drift',lambda r:r['var/lib/muos-diagnostic/boot-seq'].update(bytes=2)),
 ('metadata-bool',lambda r:r['var/lib/muos-network/network.conf'].update(links=True))]:
 s=copy.deepcopy(survey);edit(s['private_files'])
 rejects('reject-private-'+label,lambda:make_plan(mbr,s,factory))
for key,value in [('passed',False),('gambatte_core_included',False),('userdata_partition_included',True),
 ('image_bytes',ROOT_BYTES),('partition_count',3),('experiment','C70_PRIVATE_PANEL0_CARD_IMAGE')]:
 f=copy.deepcopy(factory);f[key]=value
 rejects('reject-factory-'+key,lambda:make_plan(mbr,survey,f))
for key,value in [('offset',0),('bytes',PREFIX_BYTES),('sha256','bad')]:
 f=copy.deepcopy(factory);f['regions']['rootfs.ext4'][key]=value
 rejects('reject-factory-root-'+key,lambda:make_plan(mbr,survey,f))
# Fresh offline seed may differ after shutdown; the provisioned candidate must
# retain exactly the fresh backup version, never the earlier live sample.
fresh=copy.deepcopy(rows);fresh['var/lib/muos-seedrng/seed.credit']['sha256']=h('synthetic fresh offline seed')
evidence={'offline':True,'all_namespaces_unmounted':True,'swap_or_holders':False,'alias_cache_synchronized':True,
 'cid_sha256':DECK_CID,'original_present':False,'capacity_sectors':CAPACITY,'mbr_sha256':plan['mbr_sha256'],
 'boot_prefix_16MiB_sha256':plan['boot_prefix_16MiB_sha256'],'boot_sequence':72,'prefix_backup_bytes':PREFIX_BYTES,
 'prefix_backup_sha256':h('synthetic offline backup'),'independent_host_prefix_sha256':h('synthetic offline backup'),
 'backup_fsynced':True,'host_copy_fsynced':True,'root_fsck_exit':0,'fat_fsck_exit':0,
 'userdata_logical_backup_verified':True,'private_files_from_backup':fresh,'candidate_private_files':copy.deepcopy(fresh),
 'candidate_factory_root_sha256':plan['factory_root_sha256'],'provisioned_root_sha256':h('synthetic provisioned root'),
 'candidate_counter':72,'candidate_public_tree_matches_factory':True,'candidate_only_private_allowlist_changed':True,
 'candidate_tokens_or_runtime_state_present':False}
bound=bind_backup(plan,evidence)
assert bound['passed'] and not bound['execution_enabled'] and not bound['device_writer_available']
assert bound['proposed_write']==plan['proposed_write']
cases.append('fresh-offline-seed-retained-no-execution')
for key,value in [('offline',False),('all_namespaces_unmounted',False),('swap_or_holders',True),
 ('alias_cache_synchronized',False),('cid_sha256',R35S_CID),('cid_sha256',ORIGINAL_CID),('original_present',True),
 ('capacity_sectors',True),('mbr_sha256',h('different MBR')),('boot_prefix_16MiB_sha256',h('different boot')),
 ('boot_sequence',73),('boot_sequence',True),('prefix_backup_bytes',ROOT_BYTES),
 ('independent_host_prefix_sha256',h('stale host copy')),('backup_fsynced',False),('host_copy_fsynced',False),
 ('root_fsck_exit',1),('root_fsck_exit',False),('fat_fsck_exit',1),('userdata_logical_backup_verified',False),
 ('candidate_private_files',rows),('candidate_factory_root_sha256',h('other factory')),
 ('provisioned_root_sha256',plan['factory_root_sha256']),('candidate_counter',0),('candidate_counter',73),
 ('candidate_public_tree_matches_factory',False),('candidate_only_private_allowlist_changed',False),
 ('candidate_tokens_or_runtime_state_present',True)]:
 e=copy.deepcopy(evidence);e[key]=value
 rejects('reject-backup-'+key+'-'+str(len(cases)),lambda:bind_backup(plan,e))
for name in ['var/lib/muos-network/dropbear_ed25519_host_key','var/lib/muos-network/network.conf',
             'etc/muos-network-authorized_key','var/lib/muos-diagnostic/boot-seq']:
 e=copy.deepcopy(evidence);e['private_files_from_backup'][name]['sha256']=h('different private state')
 e['candidate_private_files']=copy.deepcopy(e['private_files_from_backup'])
 rejects('reject-offline-identity-change-'+name,lambda:bind_backup(plan,e))
pre=recovery_policy(False);post=recovery_policy(True)
assert pre['byte_exact_p2_rollback_eligible'] and not pre['automatic_rollback'] and not pre['execution_enabled']
assert not post['byte_exact_p2_rollback_eligible'] and post['fresh_seed_and_monotonic_counter_recovery_required']
assert not post['p1_mbr_p3_write_allowed']
cases+=['preboot-only-exact-rollback-eligibility','postboot-blocks-seed-and-counter-rewind']
rejects('reject-unknown-boot-fence',lambda:recovery_policy(None))
rejects('reject-integer-boot-fence',lambda:recovery_policy(0))
stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area))
(stage/'analysis.json').write_text(json.dumps({'passed':True,'experiment':'C80_ROOT_MIGRATION_POLICY_CHECKS',
 'case_count':len(cases),'cases':cases,'device_accessed':False,'secret_contents_used':False,
 'writer_or_provisioner_executed':False,'receipts_are_synthetic':True,
 'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/scripts/phase4_root_migration.py']}},indent=2)+'\n')
(area/'latest-checks').write_text(str(stage)+'\n')
print('C80 pure migration policy:',len(cases),'cases passed:',stage)
