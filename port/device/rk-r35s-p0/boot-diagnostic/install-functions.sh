# SPDX-License-Identifier: MIT
# Targeted transaction; caller supplies guarded install_exec and fixed root/payload.
c12_install_parents() {
    parent=$(dirname "$1")
    while [ "$parent" != "$install_root" ] && [ "$parent" != / ] && [ "$parent" != // ]; do
        [ ! -L "$parent" ] || return 1
        parent=$(dirname "$parent")
    done
}
c12_install_preflight() {
    install_exec guard || return 64
    (cd "$install_payload/tree" && sha256sum -c ../SHA256SUMS) || return 64
    [ "$(sha256sum "$install_root/etc/inittab" | cut -d' ' -f1)" = "$(cat "$install_payload/inittab-before.sha256")" ] || return 64
    for path in usr/libexec/muos-boot usr/libexec/muos-session usr/share/muos-r35s-boot etc/default/muos-boot etc/default/muos-session var/lib/muos-diagnostic/c12.once; do
        [ ! -e "$install_root/$path" ] && [ ! -L "$install_root/$path" ] || return 64
    done
    while read mode path; do
        case "$mode" in 600|644|755) ;; *) return 64 ;; esac
        case "$path" in *..*|*[!a-zA-Z0-9_/.-]*|'') return 64 ;; esac
        case "$path" in usr/libexec/muos-boot/*|usr/libexec/muos-session/*|usr/share/muos-r35s-boot/*|etc/default/muos-boot|etc/default/muos-session) ;; *) return 64 ;; esac
        [ -f "$install_payload/tree/$path" ] && [ ! -L "$install_payload/tree/$path" ] || return 64
        c12_install_parents "$install_root/$path" || return 64
    done < "$install_payload/MODES"
}
c12_install_apply() {
    c12_install_preflight || return 64
    install_exec rw || return 1
    install_rw=1
    while read mode path; do
        mkdir -p "$(dirname "$install_root/$path")" || return 1
        cp "$install_payload/tree/$path" "$install_root/$path" || return 1
        chmod "$mode" "$install_root/$path" && chown 0:0 "$install_root/$path" || return 1
        install_exec file-installed "$path" || return 1
    done < "$install_payload/MODES"
    (cd "$install_root" && sha256sum -c "$install_payload/SHA256SUMS") || return 1
    install_exec originals || return 1
    cp "$install_payload/inittab.selected" "$install_root/etc/.muos-c12-inittab" || return 1
    chmod 644 "$install_root/etc/.muos-c12-inittab" && chown 0:0 "$install_root/etc/.muos-c12-inittab" || return 1
    mv "$install_root/etc/.muos-c12-inittab" "$install_root/etc/inittab" || return 1
    install_exec selection-installed || return 1
    # Arm only after the complete selector and both dispatch paths are installed.
    printf 'MUOS-C12-ONCE\n' > "$install_root/var/lib/muos-diagnostic/c12.once" || return 1
    chmod 600 "$install_root/var/lib/muos-diagnostic/c12.once" && chown 0:0 "$install_root/var/lib/muos-diagnostic/c12.once" || return 1
    install_exec sync && install_exec ro || return 1
    install_rw=0
}
c12_install_rollback() {
    [ "${install_rw:-0}" = 1 ] || return 0
    rm -f "$install_root/var/lib/muos-diagnostic/c12.once" "$install_root/etc/.muos-c12-inittab" || return 1
    cp "$install_payload/inittab.c07" "$install_root/etc/.muos-c12-rollback" || return 1
    chmod 644 "$install_root/etc/.muos-c12-rollback" && chown 0:0 "$install_root/etc/.muos-c12-rollback" || return 1
    mv "$install_root/etc/.muos-c12-rollback" "$install_root/etc/inittab" || return 1
    # Every path below was proved absent before this transaction.
    rm -rf "$install_root/usr/libexec/muos-boot" "$install_root/usr/libexec/muos-session" "$install_root/usr/share/muos-r35s-boot" || return 1
    rm -f "$install_root/etc/default/muos-boot" "$install_root/etc/default/muos-session" || return 1
    install_exec sync && install_exec ro || return 1
    install_rw=0
}
