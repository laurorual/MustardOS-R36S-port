# SPDX-License-Identifier: MIT
"""C54 source binding. Does not alter the same-boot C53 contract."""
def bind_source(save, load, current_boot, identity, assets):
    for report, role in [(save, 'save'), (load, 'load')]:
        assert report['experiment'] == 'C53_SELECTIVE_GB_PERSISTENCE'
        assert report['mode'] == role and report['outcome'] == role+'-returned'
        assert report['passed'] is True and report['cleanup_passed'] is True
        assert report['RAM_removed'] is True and report['root_ro'] is True
        assert report['global_mountinfo_unchanged'] is True
        assert report['private_identity'] == identity
        assert type(report['boot_sequence']) is int
        for key, digest in assets.items():
            assert report[key] == digest
    origin = save['boot_sequence']
    assert load['boot_sequence'] == origin
    assert type(current_boot) is int and current_boot == origin+1
    return origin
