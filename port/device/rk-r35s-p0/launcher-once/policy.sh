# SPDX-License-Identifier: MIT
# Pure selection policy; native adapter supplies guarded paths and durability.
c25_regular() {
    [ -f "$1" ] && [ ! -L "$1" ] &&
        [ "$(stat -c '%u:%g:%a:%h' "$1")" = 0:0:600:1 ]
}
c25_record() { printf 'MUOS-C25-%s\nBOOT=%s\n' "$1" "$2"; }
c25_matches() {
    c25_regular "$1" && c25_record "$2" "$3" | cmp -s - "$1"
}
c25_select() {
    printf 'c07\n' > "$c25_state/selected"
    printf '0\n' > "$c25_state/fallback"
    c25_previous=$(cat "$c25_store/boot-seq") || return 64
    case "$c25_previous" in ''|*[!0-9]*|?????*) return 64 ;; esac
    [ "$c25_previous" -lt 9998 ] || return 64
    c25_next=$((c25_previous+1))
    c25_used=$c25_store/$(printf 'c25.used.BOOT%04d' "$c25_next")
    if [ ! -e "$c25_store/c25.once" ] && [ ! -L "$c25_store/c25.once" ]; then
        c25_last=$c25_store/$(printf 'c25.used.BOOT%04d' "$c25_previous")
        if c25_matches "$c25_last" ONCE "$c25_previous"; then
            printf '1\n' > "$c25_state/fallback"
        fi
        return 0
    fi
    c25_matches "$c25_store/c25.once" ONCE "$c25_next" || return 64
    [ ! -e "$c25_used" ] && [ ! -L "$c25_used" ] || return 64
    # If rename/sync fails, selection stays C07. Never reconstruct c25.once.
    mv "$c25_store/c25.once" "$c25_used" && c25_durable || return 1
    c25_record GRANT "$c25_next" > "$c25_state/grant" || return 1
    chmod 600 "$c25_state/grant" || return 1
    printf 'c25\n' > "$c25_state/selected"
}
