# SPDX-License-Identifier: MIT
# C57 additions only. The native adapter owns card guards and remounts.
c57_dirs() {
    printf '%s\n' usr/libexec/muos-save-store usr/share/muos-save-store usr/share/licenses/muos-save-store
}
c57_names() {
    printf '%s\n' usr/libexec/muos-save-store/muos-save-store usr/libexec/muos-save-store/payload.sha256 usr/share/muos-save-store/contract.json usr/share/licenses/muos-save-store/LICENSE
}
c57_parents() {
    c57_parent=$(dirname "$1")
    while [ "$c57_parent" != / ] && [ "$c57_parent" != // ] && [ "$c57_parent" != "$install_root" ]; do
        [ ! -L "$c57_parent" ] || return 64
        c57_parent=$(dirname "$c57_parent")
    done
}
c57_schema() {
    [ "$(wc -l < "$install_payload/FILES")" = 4 ] || return 64
    c57_names > "$install_state/names.expected"
    awk '{print $3}' "$install_payload/FILES" > "$install_state/names.actual"
    cmp "$install_state/names.expected" "$install_state/names.actual" || return 64
    while read -r c57_hash c57_mode c57_name c57_extra; do
        [ -z "$c57_extra" ] && [ "${#c57_hash}" = 64 ] || return 64
        case "$c57_hash" in *[!0-9a-f]*) return 64 ;; esac
        if [ "$c57_name" = usr/libexec/muos-save-store/muos-save-store ]; then
            [ "$c57_mode" = 755 ] || return 64
        else [ "$c57_mode" = 644 ] || return 64; fi
        c57_file=$install_payload/new/$c57_name
        c57_parents "$c57_file" || return 64
        [ -f "$c57_file" ] && [ ! -L "$c57_file" ] || return 64
        [ "$(stat -c '%u:%g:%a:%h' "$c57_file")" = "0:0:$c57_mode:1" ] || return 64
        [ "$(sha256sum "$c57_file" | cut -d' ' -f1)" = "$c57_hash" ] || return 64
    done < "$install_payload/FILES"
}
c57_absent() {
    for c57_name in $(c57_dirs); do
        c57_parents "$install_root/$c57_name" || return 64
        [ -d "$(dirname "$install_root/$c57_name")" ] || return 64
        [ ! -e "$install_root/$c57_name" ] && [ ! -L "$install_root/$c57_name" ] || return 64
    done
}
c57_preflight() {
    install_exec guard || return 64
    c57_schema && c57_absent || return 64
    (cd "$install_root" && sha256sum -c "$install_payload/foundation.sha256") >/dev/null || return 64
}
c57_verify() {
    for c57_name in $(c57_dirs); do
        c57_file=$install_root/$c57_name
        c57_parents "$c57_file" || return 64
        [ -d "$c57_file" ] && [ ! -L "$c57_file" ] || return 64
        [ "$(stat -c '%u:%g:%a' "$c57_file")" = 0:0:755 ] || return 64
    done
    while read -r c57_hash c57_mode c57_name; do
        c57_file=$install_root/$c57_name
        [ -f "$c57_file" ] && [ ! -L "$c57_file" ] || return 64
        [ "$(stat -c '%u:%g:%a:%h' "$c57_file")" = "0:0:$c57_mode:1" ] || return 64
        [ "$(sha256sum "$c57_file" | cut -d' ' -f1)" = "$c57_hash" ] || return 64
        [ ! -e "$c57_file.c57-new" ] && [ ! -L "$c57_file.c57-new" ] || return 64
    done < "$install_payload/FILES"
    (cd "$install_root" && sha256sum -c "$install_payload/foundation.sha256") >/dev/null || return 64
}
c57_apply() {
    c57_preflight || return 64
    install_exec rw || return 1
    install_rw=1
    for c57_name in $(c57_dirs); do
        mkdir -m 755 "$install_root/$c57_name" || return 1
        install_exec directory-created "$c57_name" || return 1
    done
    while read -r c57_hash c57_mode c57_name; do
        c57_file=$install_root/$c57_name
        (set -C; cat "$install_payload/new/$c57_name" > "$c57_file.c57-new") || return 1
        chmod "$c57_mode" "$c57_file.c57-new" || return 1
        [ "$(sha256sum "$c57_file.c57-new" | cut -d' ' -f1)" = "$c57_hash" ] || return 1
        install_exec file-staged "$c57_name" || return 1
        # Hard-link publication is exclusive: never replace an existing path.
        ln "$c57_file.c57-new" "$c57_file" || return 1
        rm "$c57_file.c57-new" || return 1
        install_exec file-installed "$c57_name" || return 1
    done < "$install_payload/FILES"
    c57_verify && install_exec verify && install_exec sync && install_exec ro || return 1
    install_rw=0
}
c57_rollback() {
    [ "${install_rw:-0}" = 1 ] || return 0
    # Validate every existing published leaf before removing anything. Unexpected
    # content is retained for inspection, and the native trap still seals root.
    while read -r c57_hash c57_mode c57_name; do
        c57_file=$install_root/$c57_name
        c57_parents "$c57_file" || return 64
        if [ -e "$c57_file" ] || [ -L "$c57_file" ]; then
            [ -f "$c57_file" ] && [ ! -L "$c57_file" ] || return 64
            [ "$(sha256sum "$c57_file" | cut -d' ' -f1)" = "$c57_hash" ] || return 64
        fi
    done < "$install_payload/FILES"
    while read -r c57_hash c57_mode c57_name; do
        rm -f "$install_root/$c57_name" "$install_root/$c57_name.c57-new" || return 1
    done < "$install_payload/FILES"
    for c57_name in $(c57_dirs); do
        [ ! -d "$install_root/$c57_name" ] || rmdir "$install_root/$c57_name" || return 1
    done
    c57_absent && install_exec verify && install_exec sync && install_exec ro || return 1
    install_rw=0
}
