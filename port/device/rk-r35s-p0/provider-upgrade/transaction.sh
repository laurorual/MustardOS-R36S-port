# SPDX-License-Identifier: MIT
# C71 exact provider/consumer migration. The generated policy fixes every path.
# Adapter owns the lifetime lock, media guards, private-state check and RO trap.
c71_parents() {
    case "$1" in "$install_payload"/*) c71_destination=0 ;; *) c71_destination=1 ;; esac
    c71_parent=$(dirname "$1")
    while [ "$c71_parent" != / ] && [ "$c71_parent" != // ] && [ "$c71_parent" != "$install_root" ]; do
        [ ! -L "$c71_parent" ] || return 64
        if [ -e "$c71_parent" ]; then
            [ -d "$c71_parent" ] || return 64
            if [ "$c71_destination" = 1 ]; then
                [ "$(stat -c '%u:%g:%a' "$c71_parent")" = 0:0:755 ] || return 64
            fi
        fi
        c71_parent=$(dirname "$c71_parent")
    done
}
c71_file() {
    c71_path=$1;c71_hash=$2;c71_mode=$3
    c71_parents "$c71_path" || return 64
    [ -f "$c71_path" ] && [ ! -L "$c71_path" ] || return 64
    [ "$(stat -c '%u:%g:%a:%h' "$c71_path")" = "0:0:$c71_mode:1" ] || return 64
    [ "$(sha256sum "$c71_path" | cut -d' ' -f1)" = "$c71_hash" ] || return 64
}
c71_absent() { [ ! -e "$1" ] && [ ! -L "$1" ]; }
c71_specs() {
    c71_before > "$install_state/before.expected" || return 64
    c71_after > "$install_state/after.expected" || return 64
    cmp "$install_state/before.expected" "$install_payload/BEFORE" || return 64
    cmp "$install_state/after.expected" "$install_payload/AFTER" || return 64
    for c71_side in BEFORE AFTER; do
        if [ "$c71_side" = BEFORE ]; then c71_base=old; else c71_base=new; fi
        while read -r c71_h c71_m c71_n; do
            c71_file "$install_payload/$c71_base/$c71_n" "$c71_h" "$c71_m" || return 64
        done < "$install_payload/$c71_side"
    done
}
c71_layout() {
    { c71_old_dirs; c71_new_dirs; c71_before | awk '{print $3}'; c71_after | awk '{print $3}';
      c71_union | while read -r c71_n; do printf '%s.c71-new\n' "$c71_n"; done;
    } > "$install_state/layout.allowed"
    for c71_top in $(c71_metadata_roots); do
        c71_parents "$install_root/$c71_top" || return 64
        [ ! -L "$install_root/$c71_top" ] || return 64
        c71_absent "$install_root/$c71_top" && continue
        [ -d "$install_root/$c71_top" ] || return 64
        find "$install_root/$c71_top" -print > "$install_state/layout.actual" || return 64
        while read -r c71_path; do
            c71_rel=${c71_path#"$install_root"/}
            grep -Fxq "$c71_rel" "$install_state/layout.allowed" || return 64
        done < "$install_state/layout.actual"
    done
}
c71_tree() {
    # Exact before/after model, including absence, metadata directories and temps.
    c71_side=$1
    if [ "$c71_side" = BEFORE ]; then c71_present=old;c71_missing=new; else c71_present=new;c71_missing=old; fi
    c71_layout || return 64
    while read -r c71_h c71_m c71_n; do
        c71_file "$install_root/$c71_n" "$c71_h" "$c71_m" || return 64
    done < "$install_payload/$c71_side"
    c71_union > "$install_state/union"
    while read -r c71_n; do
        if ! awk -v n="$c71_n" '$3==n {found=1} END{exit !found}' "$install_payload/$c71_side"; then
            c71_absent "$install_root/$c71_n" || return 64
        fi
        c71_absent "$install_root/$c71_n.c71-new" || return 64
    done < "$install_state/union"
    if [ "$c71_present" = old ]; then c71_old_dirs; else c71_new_dirs; fi > "$install_state/present-dirs"
    while read -r c71_n; do
        c71_parents "$install_root/$c71_n" || return 64
        [ -d "$install_root/$c71_n" ] && [ ! -L "$install_root/$c71_n" ] || return 64
        [ "$(stat -c '%u:%g:%a' "$install_root/$c71_n")" = 0:0:755 ] || return 64
    done < "$install_state/present-dirs"
    if [ "$c71_missing" = old ]; then c71_old_dirs; else c71_new_dirs; fi > "$install_state/absent-dirs"
    while read -r c71_n; do c71_absent "$install_root/$c71_n" || return 64; done < "$install_state/absent-dirs"
    (cd "${install_root:-/}" && sha256sum -c "$install_payload/preserved.sha256") >/dev/null || return 64
}
c71_preflight() {
    install_exec guard && c71_specs && c71_tree BEFORE
}
c71_publish() {
    c71_target=$1;c71_source=$2;c71_expected_hash=$3;c71_expected_mode=$4
    c71_parents "$c71_target" || return 64
    c71_absent "$c71_target.c71-new" || return 64
    (set -C; cat "$c71_source" > "$c71_target.c71-new") || return 1
    chmod "$c71_expected_mode" "$c71_target.c71-new" || return 1
    c71_file "$c71_target.c71-new" "$c71_expected_hash" "$c71_expected_mode" || return 1
    install_exec file-staged "${c71_target#"$install_root"/}" || return 1
    # All destinations were checked before RW under the lifetime lock. Recheck
    # the current leaf immediately before an atomic replacement/publication.
    c71_rel=${c71_target#"$install_root"/}
    c71_prior=$(awk -v n="$c71_rel" '$3==n {print $1 " " $2}' "$install_payload/BEFORE")
    if [ -n "$c71_prior" ]; then
        c71_file "$c71_target" "${c71_prior% *}" "${c71_prior#* }" || return 64
        mv -f "$c71_target.c71-new" "$c71_target" || return 1
    else
        c71_absent "$c71_target" || return 64
        ln "$c71_target.c71-new" "$c71_target" && rm "$c71_target.c71-new" || return 1
    fi
    install_exec file-installed "$c71_rel"
}
c71_apply() {
    c71_preflight || return 64
    (set -C; : > "$install_state/created-directories") || return 64
    install_exec rw || return 1
    install_rw=1
    c71_new_dirs > "$install_state/new-dirs"
    while read -r c71_n; do
        mkdir -m 755 "$install_root/$c71_n" || return 1
        printf '%s\n' "$c71_n" >> "$install_state/created-directories" || return 1
        install_exec directory-created "$c71_n" || return 1
    done < "$install_state/new-dirs"
    while read -r c71_h c71_m c71_n; do
        c71_publish "$install_root/$c71_n" "$install_payload/new/$c71_n" "$c71_h" "$c71_m" || return $?
    done < "$install_payload/AFTER"
    c71_removed > "$install_state/removed"
    while read -r c71_n; do
        c71_prior=$(awk -v n="$c71_n" '$3==n {print $1 " " $2}' "$install_payload/BEFORE")
        c71_file "$install_root/$c71_n" "${c71_prior% *}" "${c71_prior#* }" || return 64
        rm "$install_root/$c71_n" || return 1
        install_exec file-removed "$c71_n" || return 1
    done < "$install_state/removed"
    c71_old_dirs | awk '{a[NR]=$0} END{for(i=NR;i>0;i--)print a[i]}' > "$install_state/old-dirs-reverse"
    while read -r c71_n; do
        rmdir "$install_root/$c71_n" || return 1
        install_exec directory-removed "$c71_n" || return 1
    done < "$install_state/old-dirs-reverse"
    c71_tree AFTER && install_exec verify && install_exec sync && install_exec ro || return 1
    install_rw=0
}
c71_recoverable() {
    # Validate every present leaf before deleting/restoring anything. Accept
    # only its original bytes or reviewed replacement; preserve unknown data.
    c71_specs && c71_layout || return 64
    c71_union > "$install_state/union"
    while read -r c71_n; do
        for c71_suffix in '' .c71-new; do
            c71_path=$install_root/$c71_n$c71_suffix
            c71_absent "$c71_path" && continue
            c71_ok=0
            for c71_side in BEFORE AFTER; do
                c71_record=$(awk -v n="$c71_n" '$3==n {print $1 " " $2}' "$install_payload/$c71_side")
                [ -n "$c71_record" ] || continue
                if c71_file "$c71_path" "${c71_record% *}" "${c71_record#* }"; then c71_ok=1; fi
            done
            [ "$c71_ok" = 1 ] || return 64
        done
    done < "$install_state/union"
    { c71_old_dirs; c71_new_dirs; } > "$install_state/all-dirs"
    while read -r c71_n; do
        c71_absent "$install_root/$c71_n" && continue
        [ -d "$install_root/$c71_n" ] && [ ! -L "$install_root/$c71_n" ] || return 64
        [ "$(stat -c '%u:%g:%a' "$install_root/$c71_n")" = 0:0:755 ] || return 64
    done < "$install_state/all-dirs"
}
c71_rollback() {
    [ "${install_rw:-0}" = 1 ] || return 0
    c71_recoverable || return 64
    # Remove only reviewed newly-added leaves and recognized temporaries.
    while read -r c71_n; do
        rm -f "$install_root/$c71_n.c71-new" || return 1
        if ! awk -v n="$c71_n" '$3==n {found=1} END{exit !found}' "$install_payload/BEFORE"; then
            rm -f "$install_root/$c71_n" || return 1
        fi
    done < "$install_state/union"
    c71_old_dirs > "$install_state/old-dirs"
    while read -r c71_n; do
        [ -d "$install_root/$c71_n" ] || mkdir -m 755 "$install_root/$c71_n" || return 1
    done < "$install_state/old-dirs"
    while read -r c71_h c71_m c71_n; do
        if c71_file "$install_root/$c71_n" "$c71_h" "$c71_m"; then continue; fi
        c71_target=$install_root/$c71_n
        (set -C; cat "$install_payload/old/$c71_n" > "$c71_target.c71-new") || return 1
        chmod "$c71_m" "$c71_target.c71-new" || return 1
        c71_file "$c71_target.c71-new" "$c71_h" "$c71_m" || return 1
        mv -f "$c71_target.c71-new" "$c71_target" || return 1
    done < "$install_payload/BEFORE"
    awk '{a[NR]=$0} END{for(i=NR;i>0;i--)print a[i]}' "$install_state/created-directories" > "$install_state/created-reverse"
    while read -r c71_n; do
        c71_new_dirs | grep -Fxq "$c71_n" || return 64
        c71_absent "$install_root/$c71_n" || rmdir "$install_root/$c71_n" || return 1
    done < "$install_state/created-reverse"
    c71_tree BEFORE && install_exec verify && install_exec sync && install_exec ro || return 1
    install_rw=0
}
