# SPDX-License-Identifier: MIT
"""Render a load-only C53 backend without modifying the frozen C53/C54 sources."""
def render_backend(source):
    text=source
    for old,new in [('prepare|seed|commit|verify','seed|verify'),('prepare|save|load','load')]:
        assert text.count(old)==1;text=text.replace(old,new)
    start=text.index('write_mount() {\n');end=text.index('checked_tree() {\n',start)
    text=text[:start]+text[end:]
    start=text.index(' prepare)\n',text.index('case "$op" in\n'))
    end=text.index(' seed)\n',start);text=text[:start]+text[end:]
    start=text.index(' commit)\n',text.index('case "$op" in\n'))
    end=text.index(' verify)\n',start);text=text[:start]+text[end:]
    start=text.index(' if [ "$transition" = 1 ];then\n')
    end=text.index(' if prefs_data_mounted ro;then\n',start);text=text[:start]+text[end:]
    text=text.replace('transition=0\n','')
    assert text.count('"$capsule/save-store"')==2
    text=text.replace('"$capsule/save-store"','/bin/sh "$capsule/installed-store.sh" "$capsule"')
    assert 'write_mount' not in text and 'mount -t ext4 -o rw' not in text
    assert ' prepare)' not in text and ' commit)' not in text
    return text
