# SPDX-License-Identifier: MIT
# C105 fixed installed scripts, explicit RAM staging, load-only bounded runtime.
c105_scripts() {
    printf '%s\n' adapter.sh app-launch.sh cycle.sh frontend-libs.sh installed-host.sh installed-store.sh select.sh store-base.sh store.sh worker.sh
}
c105_contents() { c105_scripts;printf '%s\n' functions.sh dependencies.tsv assets.tsv contract.json LICENSE; }
c105_regular() {
    [ -f "$1" ] && [ ! -L "$1" ] && [ "$(stat -c '%u:%g:%a:%h' "$1")" = "0:0:$2:1" ]
}
c105_package() {
    for c105_p in "$caller_system_root" "$caller_system_root/usr" "$caller_system_root/usr/libexec" "$caller_root";do
        [ -d "$c105_p" ] && [ ! -L "$c105_p" ] && [ "$(stat -c '%u:%g:%a' "$c105_p")" = 0:0:755 ] || return 64
    done
    c105_regular "$caller_root/caller.sh" 644 && c105_regular "$caller_root/payload.sha256" 644 || return 64
    [ "$(sha256sum "$caller_root/payload.sha256" | cut -d' ' -f1)" = "$caller_manifest_sha" ] || return 64
    [ "$(awk '{print $2}' "$caller_root/payload.sha256")" = "$(c105_contents)" ] || return 64
    awk 'NF!=2 || length($1)!=64 || $1~/[^0-9a-f]/ {bad=1} END{exit bad || NR!=15}' "$caller_root/payload.sha256" || return 64
    while read -r c105_h c105_n;do
        c105_regular "$caller_root/$c105_n" 644 || return 64
        [ "$(sha256sum "$caller_root/$c105_n" | cut -d' ' -f1)" = "$c105_h" ] || return 64
    done < "$caller_root/payload.sha256"
    [ "$(find "$caller_root" -mindepth 1 -maxdepth 1 -print | wc -l)" = 17 ] || return 64
}
c105_dependencies() {
    while read -r c105_h c105_mode c105_size c105_n;do
        c105_p=$caller_system_root/$c105_n
        c105_parent=$(dirname "$c105_p")
        while [ "$c105_parent" != / ] && [ "$c105_parent" != // ] && [ "$c105_parent" != "$caller_system_root" ];do
            [ ! -L "$c105_parent" ] && [ -d "$c105_parent" ] && [ "$(stat -c '%u:%g:%a' "$c105_parent")" = 0:0:755 ] || return 64
            c105_parent=$(dirname "$c105_parent")
        done
        c105_regular "$c105_p" "$c105_mode" || return 64
        [ "$(stat -c %s "$c105_p")" = "$c105_size" ] || return 64
        [ "$(sha256sum "$c105_p" | cut -d' ' -f1)" = "$c105_h" ] || return 64
    done < "$caller_root/dependencies.tsv"
}
c105_capsule() {
    case "$1" in /run/muos-prefs-data.??????) ;;*) return 64;;esac
    c105_tag=${1#/run/muos-prefs-data.}
    case "$c105_tag" in *[!A-Za-z0-9]*) return 64;;esac
    [ -d "$1" ] && [ ! -L "$1" ] && [ "$(stat -c '%u:%g:%a' "$1")" = 0:0:700 ] || return 64
    caller_exec capsule "$1"
}
c105_stage() {
    c105_capsule "$1" && c105_package && c105_dependencies && caller_exec platform || return 64
    c105_cap=$1
    for c105_n in $(c105_scripts) caller-stage;do
        [ ! -e "$c105_cap/$c105_n" ] && [ ! -L "$c105_cap/$c105_n" ] || return 64
    done
    mkdir -m 700 "$c105_cap/caller-stage" || return 1
    # A partial attempt stays in its owned tmpfs capsule. Never overwrite/retry.
    for c105_n in $(c105_scripts);do
        (set -C;cat "$caller_root/$c105_n" > "$c105_cap/$c105_n") || return 1
        chmod 700 "$c105_cap/$c105_n" || return 1
        cmp -s "$caller_root/$c105_n" "$c105_cap/$c105_n" || return 1
        caller_exec staged "$c105_n" || return 1
    done
    caller_exec boot > "$c105_cap/caller-stage/boot" || return 1
    printf '%s\n' "$caller_manifest_sha" > "$c105_cap/caller-stage/package" || return 1
    printf 'C105_STAGE_READY\n' > "$c105_cap/caller-stage/ready" || return 1
}
c105_staged() {
    c105_capsule "$1" || return 64
    c105_cap=$1
    [ ! -L "$c105_cap/caller-stage" ] && [ "$(stat -c '%u:%g:%a' "$c105_cap/caller-stage")" = 0:0:700 ] || return 64
    for c105_n in ready boot package;do c105_regular "$c105_cap/caller-stage/$c105_n" 600 || return 64;done
    printf 'C105_STAGE_READY\n' | cmp -s - "$c105_cap/caller-stage/ready" || return 64
    printf '%s\n' "$caller_manifest_sha" | cmp -s - "$c105_cap/caller-stage/package" || return 64
    caller_exec boot | cmp -s - "$c105_cap/caller-stage/boot" || return 64
    for c105_n in $(c105_scripts);do
        c105_regular "$c105_cap/$c105_n" 700 && cmp -s "$caller_root/$c105_n" "$c105_cap/$c105_n" || return 64
    done
}
c105_assets() {
    c105_cap=$1
    for c105_n in muxretro save-store host core.so core-check;do
        [ ! -e "$c105_cap/$c105_n" ] && [ ! -L "$c105_cap/$c105_n" ] || return 64
    done
    for c105_n in role identity launcher.sha256 store-base.sha256 installed-store.sha256 gb-assets.sha256;do
        c105_regular "$c105_cap/$c105_n" 600 || return 64
    done
    for c105_pair in 'store-base.sha256:store-base.sh' 'installed-store.sha256:installed-store.sh';do
        c105_mark=${c105_pair%%:*};c105_src=${c105_pair#*:}
        [ "$(cat "$c105_cap/$c105_mark")" = "$(sha256sum "$caller_root/$c105_src" | cut -d' ' -f1)" ] || return 64
    done
    printf 'load\n' | cmp -s - "$c105_cap/role" || return 64
    [ "$(cat "$c105_cap/launcher.sha256")" = "$(sha256sum "$caller_root/app-launch.sh" | cut -d' ' -f1)" ] || return 64
    c105_regular "$c105_cap/private.gb" 700 || return 64
    c105_bytes=$(stat -c %s "$c105_cap/private.gb")
    [ "$c105_bytes" -ge 32768 ] && [ "$c105_bytes" -le 8388608 ] || return 64
    for c105_n in lib provider-lib state owner watchdog;do
        [ -d "$c105_cap/$c105_n" ] && [ ! -L "$c105_cap/$c105_n" ] && [ "$(stat -c '%u:%g:%a' "$c105_cap/$c105_n")" = 0:0:700 ] || return 64
    done
    while read -r c105_h c105_n;do
        c105_regular "$c105_cap/$c105_n" 700 || return 64
        [ "$(sha256sum "$c105_cap/$c105_n" | cut -d' ' -f1)" = "$c105_h" ] || return 64
    done < "$caller_root/assets.tsv"
    for c105_n in lib provider-lib;do
        [ "$(find "$c105_cap/$c105_n" -mindepth 1 -maxdepth 1 -print | wc -l)" = 4 ] || return 64
    done
}
c105_run() {
    [ "$#" = 2 ] && [ "$2" = observe ] || return 64
    c105_package && c105_dependencies && caller_exec platform && c105_staged "$1" && c105_assets "$1" || return 64
    mkdir -m 700 "$1/caller-stage/run.once" || return 64
    # The original worker itself checks the private namespace, takes the lock,
    # starts/stops services and runs its 210s child. Outer subreaper stays 240s.
    caller_exec run "$1"
}
