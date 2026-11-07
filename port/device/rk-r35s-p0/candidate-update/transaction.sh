# SPDX-License-Identifier: MIT
# Directed C24 transaction. Native adapter owns media guards and root remounts.
c24_allowed() {
    case "$1" in ''|*..*|*[!a-zA-Z0-9_./-]*) return 1 ;; esac
    case "$1" in
      etc/inittab|sbin/muos-ext4-diag|usr/libexec/muos-candidate-boot-checks|usr/libexec/muos-c07-run|etc/default/muos-session|etc/default/muos-core|etc/default/muos-ui|etc/init.d/S98muos-session|etc/modprobe.d/90-muos-r35s-wifi-only.conf|opt/muos/config/*|opt/muos/device/config/*|opt/muos/device/control/asound.state|opt/muos/share/hotkey/r35s-bringup.json|opt/muos/share/theme/MustardOS/sound/navigate.wav|opt/muos/share/theme/MustardOS/sound/info_open.wav|opt/muos/share/theme/MustardOS/sound/info_close.wav|usr/libexec/muos-session/*|usr/share/muos-r35s-profile/*|usr/share/licenses/muos-r35s-*/*) return 0 ;;
      usr/libexec/muos-c25/card-guard.sh|usr/libexec/muos-c25/native.sh|usr/libexec/muos-c25/policy.sh|usr/libexec/muos-c25/select.sh|usr/libexec/muos-c25/session.sh|usr/libexec/muos-c25/payload.sha256) return 0 ;;
      etc/init.d/S95muos-core) return 0 ;;
      opt/muos/device/control/wireplumber.conf) return 0 ;;
      *) return 1 ;;
    esac
}
c24_parents() {
    c24_parent=$(dirname "$1")
    while [ "$c24_parent" != "$update_root" ] && [ "$c24_parent" != / ] && [ "$c24_parent" != // ];do
        [ ! -L "$c24_parent" ] || return 1
        c24_parent=$(dirname "$c24_parent")
    done
}
c24_old_file() {
    c24_target=$update_root/$c24_name
    c24_parents "$c24_target" && [ ! -L "$c24_target" ] || return 1
    if [ "$c24_before" = - ];then [ ! -e "$c24_target" ] || return 1
    else
        [ -f "$c24_target" ] && [ "$(stat -c '%u:%g:%a:%h' "$c24_target")" = "0:0:$c24_oldmode:1" ] || return 1
        [ "$(sha256sum "$c24_target" | cut -d' ' -f1)" = "$c24_before" ] || return 1
    fi
}
c24_preflight() {
    update_exec guard || return 64
    [ -s "$update_payload/FILES" ] && [ -f "$update_payload/DIRS" ] || return 64
    while read -r c24_before c24_oldmode c24_after c24_mode c24_name;do
        c24_allowed "$c24_name" || return 64
        case "$c24_mode" in 600|644|755) ;; *) return 64 ;; esac
        c24_old_file || return 64
        [ ! -e "$c24_target.muos-c24-new" ] && [ ! -L "$c24_target.muos-c24-new" ] || return 64
        [ -f "$update_payload/new/$c24_name" ] && [ ! -L "$update_payload/new/$c24_name" ] || return 64
        [ "$(sha256sum "$update_payload/new/$c24_name" | cut -d' ' -f1)" = "$c24_after" ] || return 64
    done < "$update_payload/FILES"
    while read -r c24_mode c24_name;do
        case "$c24_name" in usr/libexec/muos-c25|usr/libexec/muos-session/*|usr/share/muos-r35s-profile*|usr/share/licenses/muos-r35s-*) ;; *) return 64 ;; esac
        case "$c24_name" in *..*|*[!a-zA-Z0-9_./-]*) return 64 ;; esac
        case "$c24_mode" in 700|755) ;; *) return 64 ;; esac
        c24_parents "$update_root/$c24_name" || return 64
        [ ! -e "$update_root/$c24_name" ] && [ ! -L "$update_root/$c24_name" ] || return 64
    done < "$update_payload/DIRS"
    (cd "$update_root" && sha256sum -c "$update_payload/unchanged.sha256") >/dev/null || return 64
}
c24_backup() {
    c24_preflight || return 64
    [ ! -e "$update_payload/backup" ] || return 64
    mkdir -m 700 "$update_payload/backup" || return 1
    while read -r c24_before c24_oldmode c24_after c24_mode c24_name;do
        [ "$c24_before" != - ] || continue
        mkdir -p "$(dirname "$update_payload/backup/$c24_name")" || return 1
        cp -p "$update_root/$c24_name" "$update_payload/backup/$c24_name" || return 1
    done < "$update_payload/FILES"
    (cd "$update_payload/backup" && sha256sum -c ../before.sha256) >/dev/null || return 1
}
c24_apply() {
    c24_preflight || return 64
    (cd "$update_payload/backup" && sha256sum -c ../before.sha256) >/dev/null || return 64
    update_exec rw || return 1
    update_rw=1
    while read -r c24_mode c24_name;do
        mkdir -m "$c24_mode" "$update_root/$c24_name" || return 1
        chown 0:0 "$update_root/$c24_name" || return 1
    done < "$update_payload/DIRS"
    # Validate every staged sibling before replacing the first existing file.
    while read -r c24_before c24_oldmode c24_after c24_mode c24_name;do
        c24_target=$update_root/$c24_name
        cp "$update_payload/new/$c24_name" "$c24_target.muos-c24-new" || return 1
        chmod "$c24_mode" "$c24_target.muos-c24-new" && chown 0:0 "$c24_target.muos-c24-new" || return 1
        [ "$(sha256sum "$c24_target.muos-c24-new" | cut -d' ' -f1)" = "$c24_after" ] || return 1
        update_exec file-staged "$c24_name" || return 1
    done < "$update_payload/FILES"
    while read -r c24_before c24_oldmode c24_after c24_mode c24_name;do
        mv "$update_root/$c24_name.muos-c24-new" "$update_root/$c24_name" || return 1
        update_exec file-installed "$c24_name" || return 1
    done < "$update_payload/FILES"
    (cd "$update_root" && sha256sum -c "$update_payload/after.sha256" && sha256sum -c "$update_payload/unchanged.sha256") >/dev/null || return 1
    update_exec verify-after && update_exec sync && update_exec ro || return 1
    update_rw=0
}
c24_rollback() {
    [ "${update_rw:-0}" = 1 ] || return 0
    update_exec rw || return 1
    # Restore the old bootstrap/dispatcher first; only files in the exact plan.
    for c24_activation in etc/inittab sbin/muos-ext4-diag;do
        if [ -f "$update_payload/backup/$c24_activation" ];then
            cp -p "$update_payload/backup/$c24_activation" "$update_root/$c24_activation.muos-c24-new" && mv "$update_root/$c24_activation.muos-c24-new" "$update_root/$c24_activation" || return 1
        fi
    done
    while read -r c24_before c24_oldmode c24_after c24_mode c24_name;do
        c24_target=$update_root/$c24_name
        if [ "$c24_before" = - ];then rm -f "$c24_target" "$c24_target.muos-c24-new" || return 1
        else
            cp -p "$update_payload/backup/$c24_name" "$c24_target.muos-c24-new" && mv "$c24_target.muos-c24-new" "$c24_target" || return 1
        fi
    done < "$update_payload/FILES"
    awk '{a[NR]=$0} END{for(i=NR;i>0;i--)print a[i]}' "$update_payload/DIRS" > "$update_payload/reverse-dirs" || return 1
    while read -r c24_mode c24_name;do
        [ ! -d "$update_root/$c24_name" ] || rmdir "$update_root/$c24_name" || return 1
    done < "$update_payload/reverse-dirs"
    (cd "$update_root" && sha256sum -c "$update_payload/before.sha256") >/dev/null || return 1
    update_exec verify-before && update_exec sync && update_exec ro || return 1
    update_rw=0
}
