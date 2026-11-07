# SPDX-License-Identifier: MIT
# C79 has no /etc/asound.conf. Create it only in a private tmpfs /etc view.
session_c79_etc_prepare() {
    c79_etc=/etc
    c79_mnt=/mnt
    c79_template=/opt/muos/share/conf/rootfs/asound.conf
    [ -d "$c79_etc" ] && [ ! -L "$c79_etc" ] || return 1
    [ "$(stat -c '%u:%g:%a' "$c79_etc")" = 0:0:755 ] || return 1
    [ ! -e "$c79_etc/asound.conf" ] && [ ! -L "$c79_etc/asound.conf" ] || return 1
    [ -d "$c79_mnt" ] && [ ! -L "$c79_mnt" ] || return 1
    [ "$(stat -c '%u:%g:%a' "$c79_mnt")" = 0:0:755 ] || return 1
    [ -z "$(find "$c79_mnt" -mindepth 1 -maxdepth 1 -print)" ] || return 1
    [ -f "$c79_template" ] && [ ! -L "$c79_template" ] || return 1
    [ "$(stat -c '%u:%g:%a:%h:%s' "$c79_template")" = 0:0:755:1:444 ] || return 1
    printf '%s  %s\n' 58aa042723b6935ddf81d44b47e6e960279f257e2543e0ed2626c461f585e8cb "$c79_template" | sha256sum -c - >/dev/null || return 1
    [ "$(findmnt -rn -T "$dir" -o FSTYPE)" = tmpfs ] || return 1
    [ ! -e "$dir/etc-view" ] && [ ! -L "$dir/etc-view" ] || return 1
    [ ! -e "$dir/mnt-view" ] && [ ! -L "$dir/mnt-view" ] || return 1
    mkdir -m 700 "$dir/etc-view" || return 1
    # Preserve links and modes; never follow an /etc link while copying.
    # This private copy, including any identity files, stays in root-only RAM.
    cp -a "$c79_etc/." "$dir/etc-view/" || return 1
    cp -p "$c79_template" "$dir/etc-view/asound.conf" || return 1
    chmod 644 "$dir/etc-view/asound.conf" || return 1
    mkdir -m 755 "$dir/mnt-view" "$dir/mnt-view/mmc" || return 1
    session_bind "$dir/mnt-view" "$c79_mnt" || return 1
    session_bind "$dir/etc-view" "$c79_etc" || return 1
}
