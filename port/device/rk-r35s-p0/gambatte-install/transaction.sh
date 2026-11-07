# SPDX-License-Identifier: MIT
# C76 exact C75 core additions; native adapter owns media guards, lock and remounts.
c76_dirs() {
    printf '%s
' usr/share/muos-gambatte opt/muos/share/core usr/share/licenses/muos-gambatte usr/share/licenses/muos-gambatte/libgambatte usr/share/licenses/muos-gambatte/libgambatte/libretro usr/share/licenses/muos-gambatte/libgambatte/libretro-common usr/share/licenses/muos-gambatte/libgambatte/libretro-common/include usr/share/licenses/muos-gambatte/libgambatte/libretro-common/streams
}
c76_names() {
    printf '%s
' opt/muos/share/core/gambatte_libretro.so usr/share/licenses/muos-gambatte/COPYING usr/share/licenses/muos-gambatte/libgambatte/libretro-common/include/libretro.h usr/share/licenses/muos-gambatte/libgambatte/libretro-common/streams/file_stream.c usr/share/licenses/muos-gambatte/libgambatte/libretro/blipper.c usr/share/licenses/muos-gambatte/libgambatte/libretro/cc_resampler.c usr/share/licenses/muos-gambatte/libgambatte/libretro/cc_resampler.h usr/share/muos-gambatte/license-review.json usr/share/muos-gambatte/payload.sha256
}
c76_parents() {
    case "$1" in "$install_root"/*) c76_destination=1;;*) c76_destination=0;;esac
    c76_parent=$(dirname "$1")
    while [ "$c76_parent" != / ] && [ "$c76_parent" != // ] && [ "$c76_parent" != "$install_root" ]; do
        [ ! -L "$c76_parent" ] || return 64
        if [ -e "$c76_parent" ];then
            [ -d "$c76_parent" ] || return 64
            if [ "$c76_destination" = 1 ];then
                [ "$(stat -c '%u:%g:%a' "$c76_parent")" = 0:0:755 ] || return 64
            fi
        fi
        c76_parent=$(dirname "$c76_parent")
    done
}
c76_schema() {
    [ "$(wc -l < "$install_payload/FILES")" = 9 ] || return 64
    c76_names > "$install_state/names.expected"
    awk '{print $3}' "$install_payload/FILES" > "$install_state/names.actual"
    cmp "$install_state/names.expected" "$install_state/names.actual" || return 64
    while read -r c76_hash c76_mode c76_name c76_extra; do
        [ -z "$c76_extra" ] && [ "${#c76_hash}" = 64 ] || return 64
        case "$c76_hash" in *[!0-9a-f]*) return 64;;esac
        [ "$c76_mode" = 644 ] || return 64
        c76_file=$install_payload/new/$c76_name
        c76_parents "$c76_file" || return 64
        [ -f "$c76_file" ] && [ ! -L "$c76_file" ] || return 64
        [ "$(stat -c '%u:%g:%a:%h' "$c76_file")" = "0:0:$c76_mode:1" ] || return 64
        [ "$(sha256sum "$c76_file" | cut -d' ' -f1)" = "$c76_hash" ] || return 64
    done < "$install_payload/FILES"
}
c76_absent() {
    # Shared parents must already exist; all package-owned roots/leaves absent.
    for c76_name in opt/muos/share/core usr/share/muos-gambatte usr/share/licenses/muos-gambatte;do
        c76_parents "$install_root/$c76_name" || return 64
        [ -d "$(dirname "$install_root/$c76_name")" ] || return 64
        [ ! -e "$install_root/$c76_name" ] && [ ! -L "$install_root/$c76_name" ] || return 64
        [ ! -e "$install_root/$c76_name.c76-new" ] && [ ! -L "$install_root/$c76_name.c76-new" ] || return 64
    done
}
c76_preflight() {
    install_exec guard || return 64
    c76_schema && c76_absent || return 64
    (cd "$install_root" && sha256sum -c "$install_payload/foundation.sha256") >/dev/null || return 64
}
c76_layout() {
    # A neighboring file/directory is never silently removed during recovery.
    { c76_dirs;c76_names;while read -r h m n;do printf '%s.c76-new\n' "$n";done < "$install_payload/FILES"; } > "$install_state/layout.allowed"
    for c76_top in opt/muos/share/core usr/share/muos-gambatte usr/share/licenses/muos-gambatte;do
        [ ! -L "$install_root/$c76_top" ] || return 64
        [ ! -e "$install_root/$c76_top" ] || find "$install_root/$c76_top" -print > "$install_state/layout.actual" || return 64
        [ -e "$install_root/$c76_top" ] || continue
        while read -r c76_path;do
            c76_rel=${c76_path#"$install_root"/}
            grep -Fxq "$c76_rel" "$install_state/layout.allowed" || return 64
        done < "$install_state/layout.actual"
    done
}
c76_verify() {
    c76_layout || return 64
    for c76_name in $(c76_dirs);do
        c76_file=$install_root/$c76_name
        c76_parents "$c76_file" || return 64
        [ -d "$c76_file" ] && [ ! -L "$c76_file" ] || return 64
        [ "$(stat -c '%u:%g:%a' "$c76_file")" = 0:0:755 ] || return 64
    done
    while read -r c76_hash c76_mode c76_name;do
        c76_file=$install_root/$c76_name
        c76_parents "$c76_file" || return 64
        [ -f "$c76_file" ] && [ ! -L "$c76_file" ] || return 64
        [ "$(stat -c '%u:%g:%a:%h' "$c76_file")" = "0:0:$c76_mode:1" ] || return 64
        [ "$(sha256sum "$c76_file" | cut -d' ' -f1)" = "$c76_hash" ] || return 64
        [ ! -e "$c76_file.c76-new" ] && [ ! -L "$c76_file.c76-new" ] || return 64
    done < "$install_payload/FILES"
    (cd "$install_root" && sha256sum -c "$install_payload/foundation.sha256") >/dev/null || return 64
}
c76_apply() {
    c76_preflight || return 64
    (set -C; : > "$install_state/created-directories") || return 64
    install_exec rw || return 1
    install_rw=1
    for c76_name in $(c76_dirs);do
        mkdir -m 755 "$install_root/$c76_name" || return 1
        printf '%s\n' "$c76_name" >> "$install_state/created-directories" || return 1
        install_exec directory-created "$c76_name" || return 1
    done
    while read -r c76_hash c76_mode c76_name;do
        c76_file=$install_root/$c76_name
        (set -C; cat "$install_payload/new/$c76_name" > "$c76_file.c76-new") || return 1
        chmod "$c76_mode" "$c76_file.c76-new" || return 1
        [ "$(sha256sum "$c76_file.c76-new" | cut -d' ' -f1)" = "$c76_hash" ] || return 1
        install_exec file-staged "$c76_name" || return 1
        ln "$c76_file.c76-new" "$c76_file" || return 1
        rm "$c76_file.c76-new" || return 1
        install_exec file-installed "$c76_name" || return 1
    done < "$install_payload/FILES"
    c76_verify && install_exec verify && install_exec sync && install_exec ro || return 1
    install_rw=0
}
c76_rollback() {
    [ "${install_rw:-0}" = 1 ] || return 0
    c76_layout || return 64
    # Validate every published/staged file first. A partial/changed temporary
    # is retained for inspection; the native EXIT trap still seals root RO.
    while read -r c76_hash c76_mode c76_name;do
        for c76_suffix in '' .c76-new;do
            c76_file=$install_root/$c76_name$c76_suffix
            c76_parents "$c76_file" || return 64
            if [ -e "$c76_file" ] || [ -L "$c76_file" ];then
                [ -f "$c76_file" ] && [ ! -L "$c76_file" ] || return 64
                [ "$(stat -c '%u:%g:%a' "$c76_file")" = "0:0:$c76_mode" ] || return 64
                [ "$(sha256sum "$c76_file" | cut -d' ' -f1)" = "$c76_hash" ] || return 64
            fi
        done
    done < "$install_payload/FILES"
    while read -r c76_hash c76_mode c76_name;do
        rm -f "$install_root/$c76_name" "$install_root/$c76_name.c76-new" || return 1
    done < "$install_payload/FILES"
    # Only directories successfully created by this apply (or explicitly
    # adopted after a full verification on recovery) may be removed.
    awk '{a[NR]=$0} END{for(i=NR;i>0;i--)print a[i]}' "$install_state/created-directories" > "$install_state/directories.reverse"
    while read -r c76_name;do
        c76_dirs | grep -Fxq "$c76_name" || return 64
        [ ! -L "$install_root/$c76_name" ] || return 64
        [ ! -d "$install_root/$c76_name" ] || rmdir "$install_root/$c76_name" || return 1
    done < "$install_state/directories.reverse"
    c76_absent && install_exec verify && install_exec sync && install_exec ro || return 1
    install_rw=0
}
