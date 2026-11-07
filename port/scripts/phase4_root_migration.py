# SPDX-License-Identifier: MIT
"""C80 pure p2 migration/backup policy; no device or filesystem writer."""
import hashlib, re, struct

CAPACITY = 249872384
ROOT_OFFSET = 128 * 1024 * 1024
ROOT_BYTES = 512 * 1024 * 1024
PREFIX_BYTES = ROOT_OFFSET + ROOT_BYTES
R35S_CID = '12d2c78fbc14993fe2f8a00c413a5e3ef8d9659a3eba9a41a77b5c37029aa193'
DECK_CID = 'ddf407810b45ae7713ff682a9bb08985a725defe1d007455cd44b4187c39ee04'
ORIGINAL_CID = '9b4fc38015ae4a049ecd796ceceb2ef9473f4773c9b3a066ce59b567c516bbef'
PRIVATE_FILES = {
    'etc/muos-network-authorized_key', 'var/lib/muos-network/network.conf',
    'var/lib/muos-network/dropbear_ed25519_host_key', 'var/lib/muos-seedrng/seed.credit',
    'var/lib/muos-diagnostic/boot-seq',
}
OPTIONAL_PRIVATE = {'var/lib/muos-seedrng/seed.no-credit', 'var/lib/muos-network/dropbear_ed25519_host_key.tmp.pub'}
STABLE_PRIVATE = PRIVATE_FILES - {'var/lib/muos-seedrng/seed.credit', 'var/lib/muos-diagnostic/boot-seq'}

def require(condition, message):
    if not condition: raise ValueError(message)

def digest(value):
    require(type(value) is str and re.fullmatch('[0-9a-f]{64}', value), 'Invalid SHA256')
    return value

def geometry(mbr):
    require(type(mbr) is bytes and len(mbr) == 512 and mbr[510:] == b'\x55\xaa', 'Invalid MBR')
    require(struct.unpack_from('<I', mbr, 440)[0] == 0x4d554432, 'Unexpected disk signature')
    entries = [struct.unpack_from('<B3xB3xII', mbr, 446 + n*16) for n in range(4)]
    require(entries == [(0x80, 0x0c, 32768, 204800), (0, 0x83, 262144, 1048576),
                        (0, 0x83, 1310720, 248561664), (0, 0, 0, 0)], 'Expected existing three-partition test128')
    require(mbr[494:510] == bytes(16), 'Fourth partition slot not empty')
    return entries

def private_manifest(rows):
    require(type(rows) is dict and PRIVATE_FILES <= set(rows) <= PRIVATE_FILES | OPTIONAL_PRIVATE,
            'Missing or unexpected private path')
    for name, row in rows.items():
        require(type(row) is dict and set(row) == {'sha256','mode','uid','gid','links','bytes'}, 'Private metadata schema')
        digest(row['sha256'])
        require(all(type(row[k]) is int for k in ['mode','uid','gid','links','bytes']), 'Private metadata types')
        mode = 0o400 if name.startswith('var/lib/muos-seedrng/') else 0o644 if name == 'etc/muos-network-authorized_key' else 0o600
        require(row['mode'] == mode and row['uid'] == row['gid'] == 0 and row['links'] == 1,
                'Private file ownership/mode/link count')
        require(0 < row['bytes'] <= 65536, 'Private file size')
        if name.startswith('var/lib/muos-seedrng/'): require(32 <= row['bytes'] <= 256, 'Seed length')
    return rows

def make_plan(mbr, observed, factory):
    geometry(mbr)
    require(type(observed) is dict, 'Survey schema')
    require(observed['cid_sha256'] == R35S_CID and observed['original_present'] is False, 'Wrong/protected card')
    require(type(observed['capacity_sectors']) is int and observed['capacity_sectors'] == CAPACITY, 'Capacity')
    require(type(observed['sector_bytes']) is int and observed['sector_bytes'] == 512, 'Sector size')
    require(observed['model'] == 'R36S-V12 2023-08-18 Panel 0', 'Panel mismatch')
    require(observed['kernel'] == '4.4.189-muos-r35s-p4', 'Kernel mismatch')
    require(observed['root_partuuid'] == '4d554432-02' and observed['data_partuuid'] == '4d554432-03', 'PARTUUID')
    require(observed['root_ro'] is True and observed['quiet'] is True and observed['p3_mounted'] is False, 'Live health')
    require(type(observed['boot_sequence']) is int and 1 <= observed['boot_sequence'] <= 9998, 'Boot sequence')
    digest(observed['boot_prefix_16MiB_sha256'])
    private = private_manifest(observed['private_files'])
    counter = f"{observed['boot_sequence']}\n".encode()
    require(private['var/lib/muos-diagnostic/boot-seq']['sha256'] == hashlib.sha256(counter).hexdigest(), 'Counter hash')
    require(private['var/lib/muos-diagnostic/boot-seq']['bytes'] == len(counter), 'Counter length')
    require(factory['passed'] is True and factory['experiment'] == 'C79_PRIVATE_GAMBATTE_PANEL0_CARD_IMAGE', 'Factory receipt')
    require(factory['image_bytes'] == PREFIX_BYTES and factory['partition_count'] == 2, 'Factory layout')
    require(factory['gambatte_core_included'] is True and factory['userdata_partition_included'] is False, 'Factory contents')
    root = factory['regions']['rootfs.ext4']
    require(root['offset'] == ROOT_OFFSET and root['bytes'] == ROOT_BYTES, 'Factory p2 geometry')
    for h in [factory['image_sha256'], root['sha256'], factory['core_sha256']]: digest(h)
    return {'schema':1, 'experiment':'C80_ROOT_ONLY_MIGRATION_PLAN', 'execution_enabled':False,
        'device_writer_available':False, 'offline_backup_required':True, 'independent_host_copy_required':True,
        'factory_image_sha256':factory['image_sha256'], 'factory_root_sha256':root['sha256'],
        'core_sha256':factory['core_sha256'], 'survey_boot_sequence':observed['boot_sequence'],
        'mbr_sha256':hashlib.sha256(mbr).hexdigest(), 'boot_prefix_16MiB_sha256':observed['boot_prefix_16MiB_sha256'],
        'capacity_sectors':CAPACITY, 'live_cid_sha256':R35S_CID, 'offline_reader_cid_sha256':DECK_CID,
        'private_files_at_live_survey':private,
        'proposed_write':{'partition':2,'offset':ROOT_OFFSET,'bytes':ROOT_BYTES},
        'protected_ranges':[{'offset':0,'bytes':ROOT_OFFSET},
                            {'offset':PREFIX_BYTES,'bytes':CAPACITY*512-PREFIX_BYTES}],
        'mbr_p1_bootchain_p3_to_be_preserved':True, 'prefix_backup_bytes':PREFIX_BYTES,
        'userdata_logical_backup_required':True, 'raw_factory_whole_card_write_allowed':False,
        'candidate_must_use_fresh_offline_private_state':True, 'factory_counter_reset_allowed':False,
        'automatic_rollback':False, 'byte_exact_rollback_after_candidate_boot_allowed':False,
        'requires_new_survey_after_another_boot':True}

def bind_backup(plan, evidence):
    """Validate a future controller's computed receipts; never authorize device IO.

    Receipts alone are not authentication. The future offline helper must derive
    them from its exclusive guarded descriptors, not accept them over RPC.
    """
    require(plan['execution_enabled'] is False and plan['device_writer_available'] is False, 'Planner only')
    require(evidence['offline'] is True and evidence['all_namespaces_unmounted'] is True and
            evidence['swap_or_holders'] is False and evidence['alias_cache_synchronized'] is True, 'Offline preconditions')
    require(evidence['cid_sha256'] == plan['offline_reader_cid_sha256'] and evidence['original_present'] is False,
            'Offline card identity')
    require(type(evidence['capacity_sectors']) is int and evidence['capacity_sectors'] == CAPACITY, 'Offline capacity')
    require(evidence['mbr_sha256'] == plan['mbr_sha256'] and
            evidence['boot_prefix_16MiB_sha256'] == plan['boot_prefix_16MiB_sha256'], 'Offline identity changed')
    require(type(evidence['boot_sequence']) is int and evidence['boot_sequence'] == plan['survey_boot_sequence'], 'New boot: resurvey')
    require(type(evidence['prefix_backup_bytes']) is int and evidence['prefix_backup_bytes'] == PREFIX_BYTES, 'Backup length')
    backup_sha = digest(evidence['prefix_backup_sha256'])
    require(evidence['independent_host_prefix_sha256'] == backup_sha and
            evidence['backup_fsynced'] is True and evidence['host_copy_fsynced'] is True, 'Independent backup not verified')
    require(type(evidence['root_fsck_exit']) is int and evidence['root_fsck_exit'] == 0 and
            type(evidence['fat_fsck_exit']) is int and evidence['fat_fsck_exit'] == 0, 'Offline filesystems not clean')
    require(evidence['userdata_logical_backup_verified'] is True, 'Userdata backup missing')
    private = private_manifest(evidence['private_files_from_backup'])
    stable = lambda rows: {n for n in rows if not n.startswith('var/lib/muos-seedrng/') and n != 'var/lib/muos-diagnostic/boot-seq'}
    require(stable(private) == stable(plan['private_files_at_live_survey']), 'Network/key member changed')
    for n in stable(private):
        require(private[n] == plan['private_files_at_live_survey'][n], 'Network/key identity changed')
    require(private['var/lib/muos-diagnostic/boot-seq'] == plan['private_files_at_live_survey']['var/lib/muos-diagnostic/boot-seq'],
            'Counter changed')
    require(evidence['candidate_private_files'] == private, 'Candidate must retain latest offline private state')
    require(evidence['candidate_factory_root_sha256'] == plan['factory_root_sha256'], 'Wrong candidate base')
    candidate = digest(evidence['provisioned_root_sha256'])
    require(candidate != plan['factory_root_sha256'] and evidence['candidate_counter'] == plan['survey_boot_sequence'] and
            type(evidence['candidate_counter']) is int, 'Unprovisioned/reset candidate')
    require(evidence['candidate_public_tree_matches_factory'] is True and evidence['candidate_only_private_allowlist_changed'] is True and
            evidence['candidate_tokens_or_runtime_state_present'] is False, 'Candidate composition')
    return {'passed':True,'execution_enabled':False,'device_writer_available':False,
            'proposed_write':dict(plan['proposed_write']), 'verified_backup_sha256':backup_sha,
            'provisioned_root_sha256':candidate, 'backend_and_physical_validation_pending':True}

def recovery_policy(boot_attempted):
    require(type(boot_attempted) is bool, 'Boot fence must be explicit')
    return {'execution_enabled':False,'automatic_rollback':False,
            'byte_exact_p2_rollback_eligible':not boot_attempted,
            'fresh_seed_and_monotonic_counter_recovery_required':boot_attempted,
            'p1_mbr_p3_write_allowed':False}
