# SPDX-License-Identifier: MIT
# Directed update of five public C12 files; never arms a token or enables power.
c12_update_preflight() {
    update_exec guard || return 64
    (cd "$update_payload/new" && sha256sum -c ../new.sha256) || return 64
    (cd "$update_root" && sha256sum -c "$update_payload/installed-before.sha256") || return 64
    install_root=$update_root
    for name in power-functions.sh order.sh native-functions.sh diagnostic-save.sh service.sh; do
        target=$update_root/usr/libexec/muos-boot/$name
        c12_install_parents "$target" || return 64
        [ ! -L "$target" ] && [ ! -e "$target.muos-power-new" ] && [ ! -L "$target.muos-power-new" ] || return 64
        if [ "$name" = power-functions.sh ]; then
            [ ! -e "$target" ] || return 64
        else [ -f "$target" ] || return 64; fi
        [ -f "$update_payload/new/$name" ] && [ ! -L "$update_payload/new/$name" ] || return 64
    done
    mkdir "$update_payload/backup" || return 64
    for name in order.sh native-functions.sh diagnostic-save.sh service.sh; do
        cp -p "$update_root/usr/libexec/muos-boot/$name" "$update_payload/backup/$name" || return 1
    done
}
c12_update_apply() {
    c12_update_preflight || return 64
    update_exec rw || return 1
    update_rw=1
    # Install the newly sourced library first, the controller last.
    for name in power-functions.sh order.sh native-functions.sh diagnostic-save.sh service.sh; do
        target=$update_root/usr/libexec/muos-boot/$name
        cp "$update_payload/new/$name" "$target.muos-power-new" || return 1
        chmod 755 "$target.muos-power-new" && chown 0:0 "$target.muos-power-new" || return 1
        mv "$target.muos-power-new" "$target" || return 1
        update_exec file-installed "$name" || return 1
    done
    (cd "$update_root/usr/libexec/muos-boot" && sha256sum -c "$update_payload/new.sha256") || return 1
    update_exec originals && update_exec sync && update_exec ro || return 1
    update_rw=0
}
c12_update_rollback() {
    [ "${update_rw:-0}" = 1 ] || return 0
    # A failed final remount may have left root RO. Reopen only for this rollback.
    update_exec rw || return 1
    for name in order.sh native-functions.sh diagnostic-save.sh service.sh; do
        target=$update_root/usr/libexec/muos-boot/$name
        cp -p "$update_payload/backup/$name" "$target.muos-power-new" && mv "$target.muos-power-new" "$target" || return 1
    done
    rm -f "$update_root/usr/libexec/muos-boot/power-functions.sh" "$update_root/usr/libexec/muos-boot/power-functions.sh.muos-power-new" || return 1
    (cd "$update_root" && sha256sum -c "$update_payload/installed-before.sha256") || return 1
    update_exec sync && update_exec ro || return 1
    update_rw=0
}
