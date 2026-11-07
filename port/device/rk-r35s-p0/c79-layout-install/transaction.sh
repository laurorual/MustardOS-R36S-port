# SPDX-License-Identifier: MIT
# C102: two additive paths. The adapter owns media guards, lock and remounts.
c102_parents() {
    for c102_p in "$layout_root" "$layout_root/etc" "$layout_root/mnt"; do
        [ -d "$c102_p" ] && [ ! -L "$c102_p" ] || return 64
        [ "$(stat -c '%u:%g:%a' "$c102_p")" = 0:0:755 ] || return 64
    done
}
c102_file() {
    [ -f "$1" ] && [ ! -L "$1" ] || return 64
    [ "$(stat -c '%u:%g:%a:%s' "$1")" = 0:0:644:444 ] || return 64
    [ "$(sha256sum "$1" | cut -d' ' -f1)" = 58aa042723b6935ddf81d44b47e6e960279f257e2543e0ed2626c461f585e8cb ]
}
c102_schema() {
    c102_file "$layout_payload/asound.conf" || return 64
    [ "$(stat -c %h "$layout_payload/asound.conf")" = 1 ] || return 64
}
c102_absent() {
    c102_parents || return 64
    for c102_p in etc/asound.conf etc/asound.conf.c102-new mnt/mmc; do
        [ ! -e "$layout_root/$c102_p" ] && [ ! -L "$layout_root/$c102_p" ] || return 64
    done
    [ "$(stat -c %h "$layout_root/mnt")" = 2 ] || return 64
    [ -z "$(find "$layout_root/mnt" -mindepth 1 -maxdepth 1 -print)" ] || return 64
}
c102_directory() {
    [ -d "$layout_root/mnt/mmc" ] && [ ! -L "$layout_root/mnt/mmc" ] || return 64
    [ "$(stat -c '%u:%g:%a:%h' "$layout_root/mnt/mmc")" = 0:0:755:2 ] || return 64
    [ -z "$(find "$layout_root/mnt/mmc" -mindepth 1 -maxdepth 1 -print)" ] || return 64
}
c102_foundation() {
    (cd "$layout_root" && sha256sum -c "$layout_payload/foundation.sha256") >/dev/null
}
c102_preflight() {
    layout_exec guard && c102_schema && c102_absent && c102_foundation
}
c102_verify() {
    c102_parents && c102_directory && c102_file "$layout_root/etc/asound.conf" || return 64
    [ "$(stat -c %h "$layout_root/etc/asound.conf")" = 1 ] || return 64
    [ ! -e "$layout_root/etc/asound.conf.c102-new" ] && [ ! -L "$layout_root/etc/asound.conf.c102-new" ] || return 64
    [ "$(stat -c %h "$layout_root/mnt")" = 3 ] || return 64
    [ "$(find "$layout_root/mnt" -mindepth 1 -maxdepth 1 -print)" = "$layout_root/mnt/mmc" ] || return 64
    c102_foundation
}
c102_apply() {
    c102_preflight || return 64
    layout_exec rw || return 1
    layout_rw=1
    # Ownership flags survive failed hooks; foreign/partial bytes are retained.
    (set -C; : > "$layout_root/etc/asound.conf.c102-new") || return 1
    layout_temporary=1
    cat "$layout_payload/asound.conf" > "$layout_root/etc/asound.conf.c102-new" || return 1
    chmod 644 "$layout_root/etc/asound.conf.c102-new" || return 1
    c102_file "$layout_root/etc/asound.conf.c102-new" || return 1
    layout_exec staged || return 1
    ln "$layout_root/etc/asound.conf.c102-new" "$layout_root/etc/asound.conf" || return 1
    layout_published=1
    layout_exec linked || return 1
    rm "$layout_root/etc/asound.conf.c102-new" || return 1
    layout_temporary=0
    layout_exec published || return 1
    mkdir -m 755 "$layout_root/mnt/mmc" || return 1
    layout_directory=1
    layout_exec directory || return 1
    c102_verify && layout_exec verify && layout_exec sync && layout_exec ro || return 1
    layout_rw=0
}
c102_rollback() {
    [ "${layout_rw:-0}" = 1 ] || return 0
    c102_parents && c102_schema && c102_foundation && layout_exec verify || return 64
    # Validate ALL owned paths before removing anything. An interrupted copy,
    # alias, changed file, extra hardlink or nonempty directory stays for audit.
    c102_count=0
    for c102_pair in "${layout_temporary:-0}:etc/asound.conf.c102-new" "${layout_published:-0}:etc/asound.conf"; do
        c102_owned=${c102_pair%%:*};c102_name=${c102_pair#*:}
        if [ "$c102_owned" = 1 ]; then
            c102_file "$layout_root/$c102_name" || return 64
            c102_count=$((c102_count+1))
        else
            [ ! -e "$layout_root/$c102_name" ] && [ ! -L "$layout_root/$c102_name" ] || return 64
        fi
    done
    for c102_name in etc/asound.conf.c102-new etc/asound.conf; do
        [ ! -e "$layout_root/$c102_name" ] || [ "$(stat -c %h "$layout_root/$c102_name")" = "$c102_count" ] || return 64
    done
    if [ "$c102_count" = 2 ]; then
        [ "$(stat -c '%d:%i' "$layout_root/etc/asound.conf")" = "$(stat -c '%d:%i' "$layout_root/etc/asound.conf.c102-new")" ] || return 64
    fi
    if [ "${layout_directory:-0}" = 1 ]; then c102_directory || return 64
    else [ ! -e "$layout_root/mnt/mmc" ] && [ ! -L "$layout_root/mnt/mmc" ] || return 64;fi
    [ "${layout_published:-0}" = 0 ] || rm "$layout_root/etc/asound.conf" || return 1
    [ "${layout_temporary:-0}" = 0 ] || rm "$layout_root/etc/asound.conf.c102-new" || return 1
    [ "${layout_directory:-0}" = 0 ] || rmdir "$layout_root/mnt/mmc" || return 1
    c102_absent && layout_exec verify && layout_exec sync && layout_exec ro || return 1
    layout_rw=0
}
