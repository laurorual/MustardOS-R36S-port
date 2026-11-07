# SPDX-License-Identifier: MIT
# C62 exact C60 additions; native adapter owns media guards, lock and remounts.
c62_dirs() {
    printf '%s\n' usr/share/muos-muxretro usr/share/licenses/muos-muxretro usr/share/licenses/muos-muxretro/frontend usr/share/licenses/muos-muxretro/rcheevos usr/share/licenses/muos-muxretro/frontend/retro usr/share/licenses/muos-muxretro/frontend/vendor usr/share/licenses/muos-muxretro/frontend/retro/core usr/share/licenses/muos-muxretro/frontend/vendor/json usr/share/licenses/muos-muxretro/frontend/vendor/mdns usr/share/licenses/muos-muxretro/frontend/vendor/mini usr/share/licenses/muos-muxretro/frontend/vendor/miniz usr/share/licenses/muos-muxretro/frontend/vendor/stb usr/share/licenses/muos-muxretro/frontend/vendor/xxhash
}
c62_names() {
    printf '%s\n' opt/muos/frontend/muxretro usr/share/licenses/muos-muxretro/frontend/LICENSE usr/share/licenses/muos-muxretro/frontend/retro/core/libretro.h usr/share/licenses/muos-muxretro/frontend/vendor/json/LICENSE usr/share/licenses/muos-muxretro/frontend/vendor/mdns/LICENSE usr/share/licenses/muos-muxretro/frontend/vendor/mini/LICENSE usr/share/licenses/muos-muxretro/frontend/vendor/miniz/LICENSE usr/share/licenses/muos-muxretro/frontend/vendor/stb/LICENSE usr/share/licenses/muos-muxretro/frontend/vendor/xxhash/LICENSE usr/share/licenses/muos-muxretro/rcheevos/LICENSE usr/share/muos-muxretro/payload.sha256 usr/share/muos-muxretro/platform.sha256 usr/share/muos-muxretro/provenance.json
}
c62_parents() {
    case "$1" in "$install_root"/*) c62_destination=1;;*) c62_destination=0;;esac
    c62_parent=$(dirname "$1")
    while [ "$c62_parent" != / ] && [ "$c62_parent" != // ] && [ "$c62_parent" != "$install_root" ]; do
        [ ! -L "$c62_parent" ] || return 64
        if [ -e "$c62_parent" ];then
            [ -d "$c62_parent" ] || return 64
            if [ "$c62_destination" = 1 ];then
                [ "$(stat -c '%u:%g:%a' "$c62_parent")" = 0:0:755 ] || return 64
            fi
        fi
        c62_parent=$(dirname "$c62_parent")
    done
}
c62_schema() {
    [ "$(wc -l < "$install_payload/FILES")" = 13 ] || return 64
    c62_names > "$install_state/names.expected"
    awk '{print $3}' "$install_payload/FILES" > "$install_state/names.actual"
    cmp "$install_state/names.expected" "$install_state/names.actual" || return 64
    while read -r c62_hash c62_mode c62_name c62_extra; do
        [ -z "$c62_extra" ] && [ "${#c62_hash}" = 64 ] || return 64
        case "$c62_hash" in *[!0-9a-f]*) return 64;;esac
        if [ "$c62_name" = opt/muos/frontend/muxretro ];then
            [ "$c62_mode" = 755 ] || return 64
        else [ "$c62_mode" = 644 ] || return 64;fi
        c62_file=$install_payload/new/$c62_name
        c62_parents "$c62_file" || return 64
        [ -f "$c62_file" ] && [ ! -L "$c62_file" ] || return 64
        [ "$(stat -c '%u:%g:%a:%h' "$c62_file")" = "0:0:$c62_mode:1" ] || return 64
        [ "$(sha256sum "$c62_file" | cut -d' ' -f1)" = "$c62_hash" ] || return 64
    done < "$install_payload/FILES"
}
c62_absent() {
    # Shared parents must already exist; all package-owned roots/leaves absent.
    for c62_name in opt/muos/frontend/muxretro usr/share/muos-muxretro usr/share/licenses/muos-muxretro;do
        c62_parents "$install_root/$c62_name" || return 64
        [ -d "$(dirname "$install_root/$c62_name")" ] || return 64
        [ ! -e "$install_root/$c62_name" ] && [ ! -L "$install_root/$c62_name" ] || return 64
        [ ! -e "$install_root/$c62_name.c62-new" ] && [ ! -L "$install_root/$c62_name.c62-new" ] || return 64
    done
}
c62_preflight() {
    install_exec guard || return 64
    c62_schema && c62_absent || return 64
    (cd "$install_root" && sha256sum -c "$install_payload/foundation.sha256") >/dev/null || return 64
}
c62_layout() {
    # A neighboring file/directory is never silently removed during recovery.
    { c62_dirs;c62_names;while read -r h m n;do printf '%s.c62-new\n' "$n";done < "$install_payload/FILES"; } > "$install_state/layout.allowed"
    for c62_top in usr/share/muos-muxretro usr/share/licenses/muos-muxretro;do
        [ ! -L "$install_root/$c62_top" ] || return 64
        [ ! -e "$install_root/$c62_top" ] || find "$install_root/$c62_top" -print > "$install_state/layout.actual" || return 64
        [ -e "$install_root/$c62_top" ] || continue
        while read -r c62_path;do
            c62_rel=${c62_path#"$install_root"/}
            grep -Fxq "$c62_rel" "$install_state/layout.allowed" || return 64
        done < "$install_state/layout.actual"
    done
}
c62_verify() {
    c62_layout || return 64
    for c62_name in $(c62_dirs);do
        c62_file=$install_root/$c62_name
        c62_parents "$c62_file" || return 64
        [ -d "$c62_file" ] && [ ! -L "$c62_file" ] || return 64
        [ "$(stat -c '%u:%g:%a' "$c62_file")" = 0:0:755 ] || return 64
    done
    while read -r c62_hash c62_mode c62_name;do
        c62_file=$install_root/$c62_name
        c62_parents "$c62_file" || return 64
        [ -f "$c62_file" ] && [ ! -L "$c62_file" ] || return 64
        [ "$(stat -c '%u:%g:%a:%h' "$c62_file")" = "0:0:$c62_mode:1" ] || return 64
        [ "$(sha256sum "$c62_file" | cut -d' ' -f1)" = "$c62_hash" ] || return 64
        [ ! -e "$c62_file.c62-new" ] && [ ! -L "$c62_file.c62-new" ] || return 64
    done < "$install_payload/FILES"
    (cd "$install_root" && sha256sum -c "$install_payload/foundation.sha256") >/dev/null || return 64
}
c62_apply() {
    c62_preflight || return 64
    (set -C; : > "$install_state/created-directories") || return 64
    install_exec rw || return 1
    install_rw=1
    for c62_name in $(c62_dirs);do
        mkdir -m 755 "$install_root/$c62_name" || return 1
        printf '%s\n' "$c62_name" >> "$install_state/created-directories" || return 1
        install_exec directory-created "$c62_name" || return 1
    done
    while read -r c62_hash c62_mode c62_name;do
        c62_file=$install_root/$c62_name
        (set -C; cat "$install_payload/new/$c62_name" > "$c62_file.c62-new") || return 1
        chmod "$c62_mode" "$c62_file.c62-new" || return 1
        [ "$(sha256sum "$c62_file.c62-new" | cut -d' ' -f1)" = "$c62_hash" ] || return 1
        install_exec file-staged "$c62_name" || return 1
        ln "$c62_file.c62-new" "$c62_file" || return 1
        rm "$c62_file.c62-new" || return 1
        install_exec file-installed "$c62_name" || return 1
    done < "$install_payload/FILES"
    c62_verify && install_exec verify && install_exec sync && install_exec ro || return 1
    install_rw=0
}
c62_rollback() {
    [ "${install_rw:-0}" = 1 ] || return 0
    c62_layout || return 64
    # Validate every published/staged file first. A partial/changed temporary
    # is retained for inspection; the native EXIT trap still seals root RO.
    while read -r c62_hash c62_mode c62_name;do
        for c62_suffix in '' .c62-new;do
            c62_file=$install_root/$c62_name$c62_suffix
            c62_parents "$c62_file" || return 64
            if [ -e "$c62_file" ] || [ -L "$c62_file" ];then
                [ -f "$c62_file" ] && [ ! -L "$c62_file" ] || return 64
                [ "$(stat -c '%u:%g:%a' "$c62_file")" = "0:0:$c62_mode" ] || return 64
                [ "$(sha256sum "$c62_file" | cut -d' ' -f1)" = "$c62_hash" ] || return 64
            fi
        done
    done < "$install_payload/FILES"
    while read -r c62_hash c62_mode c62_name;do
        rm -f "$install_root/$c62_name" "$install_root/$c62_name.c62-new" || return 1
    done < "$install_payload/FILES"
    # Only directories successfully created by this apply (or explicitly
    # adopted after a full verification on recovery) may be removed.
    awk '{a[NR]=$0} END{for(i=NR;i>0;i--)print a[i]}' "$install_state/created-directories" > "$install_state/directories.reverse"
    while read -r c62_name;do
        c62_dirs | grep -Fxq "$c62_name" || return 64
        [ ! -L "$install_root/$c62_name" ] || return 64
        [ ! -d "$install_root/$c62_name" ] || rmdir "$install_root/$c62_name" || return 1
    done < "$install_state/directories.reverse"
    c62_absent && install_exec verify && install_exec sync && install_exec ro || return 1
    install_rw=0
}
