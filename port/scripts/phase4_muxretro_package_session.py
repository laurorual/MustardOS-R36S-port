# SPDX-License-Identifier: MIT
"""Bind a new C60 ELF to a C59 same-boot session without rewriting history."""
def bind_package_host(prior, package, provenance, current_boot, boot_id, identity, assets, binary_sha):
    assert prior['experiment']=='C59_INSTALLED_CLI_GB_LOAD'
    for key in ['passed','cleanup_passed','RAM_removed','global_mountinfo_unchanged','root_ro',
                'store_matches_previous_boot','installed_CLI_used']:
        assert prior[key] is True,key
    assert prior['store_ELF_transferred'] is False and prior['preferences_persisted'] is False
    assert prior['mode']=='load' and prior['outcome']=='installed-load-returned'
    assert type(current_boot) is int and type(prior['boot_sequence']) is int
    assert current_boot==prior['boot_sequence']
    assert boot_id==prior['kernel_boot_id']
    assert prior['private_identity']==identity
    for key,digest in assets.items():assert prior[key]==digest,key
    assert package['experiment']=='C60_MUXRETRO_PRIVATE_SDK_PACKAGE'
    for key in ['passed','default_off','private_SDK_required','real_Kconfig_rsync_legal_info',
                'source_only_legal_archive_verified','frontend_source_matches_C50','clean_source_build',
                'missing_and_changed_SDK_refused_before_compiler','C07_boot_contract_preserved',
                'private_composition_loader_passed','SDK_config_unchanged']:
        assert package[key] is True,key
    for key in ['full_frontend_library_provider_integrated','platform_libraries_installed',
                'full_Buildroot_rebuild','device_accessed','new_native_runtime_qualified','new_image_built',
                'C50_binary_byte_identical']:
        assert package[key] is False,key
    assert package['binary_sha256']==binary_sha and binary_sha!=assets['host_binary_sha256']
    assert provenance['C50_binary_sha256']==assets['host_binary_sha256']
    assert provenance['all_prepared_frontend_source_matches_C50'] is True
    assert provenance['private_only'] is True and provenance['full_frontend_provider_integrated'] is False
    assert provenance['cores_ROMs_saves_or_platform_binaries_packaged'] is False
    assert package['private_composition']['foundation_files']==97
    assert package['C56_existing_items_preserved']==3330 and package['composition_added_files']==13
    return binary_sha
