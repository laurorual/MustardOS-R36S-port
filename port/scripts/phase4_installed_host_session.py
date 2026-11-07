# SPDX-License-Identifier: MIT
"""C63 installed-host binding; leave all C59/C61 historical guards unchanged."""
def bind_installed_host(prior, deployment, plan, boot, boot_id, identity, assets, plan_sha):
    assert prior['experiment']=='C61_PACKAGE_HOST_GB_LOAD'
    for key in ['passed','cleanup_passed','RAM_removed','root_ro','global_mountinfo_unchanged',
                'store_matches_previous_boot','installed_CLI_used','native_ABI_passed','exact_C59_boot_retained']:
        assert prior[key] is True,key
    assert prior['mode']=='load' and prior['outcome']=='package-host-load-returned'
    assert prior['private_identity']==identity
    assert type(boot) is int and type(prior['boot_sequence']) is int
    assert boot==prior['boot_sequence'] and boot_id==prior['kernel_boot_id']
    assert prior['store_ELF_transferred'] is False and prior['preferences_persisted'] is False
    for key,digest in assets.items():assert prior[key]==digest,key
    assert deployment['experiment']=='C62_INSTALLED_MUXRETRO'
    for key in ['passed','root_read_only','infrastructure_unchanged','private_state_fingerprint_matched',
                'installed_ABI_tested','RAM_removed','global_mounts_unchanged']:
        assert deployment[key] is True,key
    for key in ['reboot_requested','token_or_service_enabled','p3_mounted','GUI_replayed','runtime_C46_override_installed']:
        assert deployment[key] is False,key
    assert type(deployment['boot_sequence']) is int and deployment['boot_sequence']==boot
    assert deployment['files_added']==13 and deployment['directories_added']==13
    assert deployment['existing_files_replaced']==0 and deployment['foundation_files']==97
    assert deployment['plan_sha256']==plan_sha
    assert plan['experiment']=='C62_MUXRETRO_INSTALL' and plan['boot_sequence']==boot
    assert plan['preserved_prerequisites']==105
    contract=plan['runtime_contract']
    assert contract['activation']=='manual only'
    assert contract['core_ROM_save_service_or_provider_installed'] is False
    assert contract['GUI_requires_C46_RAM_libmuxmod_sha256']==assets['library_sha256']
    rows=plan['files'];assert len(rows)==13 and len({r['path'] for r in rows})==13
    hosts=[r for r in rows if r['path']=='opt/muos/frontend/muxretro']
    assert len(hosts)==1 and hosts[0]['mode']==0o755 and hosts[0]['before']=='absent'
    assert hosts[0]['sha256']==assets['host_binary_sha256']
    return hosts[0]['sha256']
