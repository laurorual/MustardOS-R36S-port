# SPDX-License-Identifier: MIT
"""C59 explicit C54 -> C58 -> observed next-boot binding; C54 stays unchanged."""
def bind_installed_source(prior, installed, current_boot, identity, assets, prior_sha):
    assert prior['experiment']=='C54_PRIOR_BOOT_GB_LOAD'
    assert installed['experiment']=='C58_INSTALLED_STORE_HEADLESS'
    for r in [prior,installed]:
        assert r['passed'] is True and r['cleanup_passed'] is True and r['RAM_removed'] is True
        assert r['private_identity']==identity
        assert type(r['boot_sequence']) is int
    assert prior['mode']=='load' and prior['outcome']=='load-after-boot-returned'
    assert prior['root_ro'] is True and prior['store_matches_previous_boot'] is True
    assert installed['root_read_only'] is True and installed['global_mountinfo_unchanged'] is True
    assert installed['snapshot_matches_C54'] is True and installed['real_p3_read_only_noload'] is True
    assert installed['installed_CLI_used'] is True and installed['store_ELF_transferred'] is False
    assert installed['card_saves_written'] is False and installed['installed_files_modified'] is False
    assert installed['source_snapshot_generation']==1 and installed['core_bytes']==26861
    assert installed['source_C54_analysis_sha256']==prior_sha
    assert installed['boot_sequence']==prior['boot_sequence']
    assert type(current_boot) is int and current_boot==installed['boot_sequence']+1
    for key,digest in assets.items():assert prior[key]==digest,key
    return installed['boot_sequence']
