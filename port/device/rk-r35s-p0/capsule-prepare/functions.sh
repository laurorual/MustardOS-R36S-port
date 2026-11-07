# SPDX-License-Identifier: MIT
# C107 prepare a load-only RAM capsule; never mount or write persistent media.
capsule_regular() {
    [ -f "$1" ] && [ ! -L "$1" ] && [ "$(stat -c '%u:%g:%a:%h' "$1")" = "0:0:$2:1" ]
}
capsule_parents() {
    cap_parent=$(dirname "$1")
    while [ "$cap_parent" != / ] && [ "$cap_parent" != // ] && [ "$cap_parent" != "$capsule_system_root" ];do
        [ -d "$cap_parent" ] && [ ! -L "$cap_parent" ] && [ "$(stat -c '%u:%g:%a' "$cap_parent")" = 0:0:755 ] || return 64
        cap_parent=$(dirname "$cap_parent")
    done
}
capsule_package() {
    capsule_parents "$capsule_package_root/prepare.sh" || return 64
    for cap_name in prepare.sh payload.sha256;do capsule_regular "$capsule_package_root/$cap_name" 644 || return 64;done
    [ "$(sha256sum "$capsule_package_root/payload.sha256" | cut -d' ' -f1)" = "$capsule_manifest_sha" ] || return 64
    [ "$(awk '{print $2}' "$capsule_package_root/payload.sha256")" = "$(printf '%s\n' functions.sh assets.tsv contract.json LICENSE)" ] || return 64
    while read -r cap_hash cap_name;do
        capsule_regular "$capsule_package_root/$cap_name" 644 || return 64
        [ "$(sha256sum "$capsule_package_root/$cap_name" | cut -d' ' -f1)" = "$cap_hash" ] || return 64
    done < "$capsule_package_root/payload.sha256"
    [ "$(find "$capsule_package_root" -mindepth 1 -maxdepth 1 -print | wc -l)" = 6 ] || return 64
}
capsule_identity() {
    for cap_hex in "$1" "$2";do
        [ "${#cap_hex}" = 64 ] || return 64
        case "$cap_hex" in *[!0-9a-f]*) return 64;;esac
    done
    # Stream binary digest bytes. Shell variables never contain NUL bytes.
    {
        printf 'MUOS-R35S-GB-SNAPSHOT-V1\000'
        for cap_hex in "$1" "$2";do
            for cap_byte in $(printf '%s' "$cap_hex" | sed 's/../& /g');do
                printf "\\$(printf '%03o' "$((0x$cap_byte))")"
            done
        done
    } | sha256sum | cut -d' ' -f1
}
capsule_source() {
    case "$1" in
    inputs/runner|inputs/state-metadata|inputs/menu-libmuxmod.so|inputs/provider-probe) printf '%s/%s\n' "$cap_dir" "$1" ;;
    opt/muos/frontend/lib/libui.so|opt/muos/frontend/lib/libmuxcom.so|opt/muos/frontend/lib/libmuxmod.so|opt/muos/frontend/lib/libplutosvg.so)
        printf '%s/%s\n' "$capsule_system_root" "$1" ;;
    *) return 64;;esac
}
capsule_copy() {
    [ ! -e "$2" ] && [ ! -L "$2" ] || return 64
    (set -C;cat "$1" > "$2") || return 1
    chmod 700 "$2" || return 1
    capsule_regular "$2" 700 && cmp -s "$1" "$2" || return 1
    [ "$(sha256sum "$2" | cut -d' ' -f1)" = "$3" ] || return 1
    capsule_exec copied "$2"
}
capsule_prepare() {
    [ "$#" = 1 ] || return 64
    cap_dir=$1
    case "$cap_dir" in /run/muos-prefs-data.??????) ;;*) return 64;;esac
    case "${cap_dir#/run/muos-prefs-data.}" in *[!A-Za-z0-9]*) return 64;;esac
    [ -d "$cap_dir" ] && [ ! -L "$cap_dir" ] && [ "$(stat -c '%u:%g:%a' "$cap_dir")" = 0:0:700 ] || return 64
    capsule_package && capsule_exec platform && capsule_exec tmpfs "$cap_dir" || return 64
    [ "$(find "$cap_dir" -mindepth 1 -maxdepth 1 -print)" = "$cap_dir/inputs" ] || return 64
    [ -d "$cap_dir/inputs" ] && [ ! -L "$cap_dir/inputs" ] && [ "$(stat -c '%u:%g:%a' "$cap_dir/inputs")" = 0:0:700 ] || return 64
    [ "$(find "$cap_dir/inputs" -mindepth 1 -maxdepth 1 -print | wc -l)" = 5 ] || return 64
    for cap_name in runner state-metadata menu-libmuxmod.so provider-probe private.gb;do
        capsule_regular "$cap_dir/inputs/$cap_name" 700 || return 64
    done
    cap_rom_bytes=$(stat -c %s "$cap_dir/inputs/private.gb")
    [ "$cap_rom_bytes" -ge 32768 ] && [ "$cap_rom_bytes" -le 8388608 ] || return 64
    cap_rom_sha=$(sha256sum "$cap_dir/inputs/private.gb" | cut -d' ' -f1)
    while read -r cap_hash cap_mode cap_dest cap_origin;do
        cap_source=$(capsule_source "$cap_origin") || return 64
        case "$cap_origin" in opt/*) capsule_parents "$cap_source" || return 64;;esac
        capsule_regular "$cap_source" "$cap_mode" || return 64
        [ "$(sha256sum "$cap_source" | cut -d' ' -f1)" = "$cap_hash" ] || return 64
    done < "$capsule_package_root/assets.tsv"
    cap_core=$capsule_system_root/opt/muos/share/core/gambatte_libretro.so
    capsule_parents "$cap_core" && capsule_regular "$cap_core" 644 || return 64
    [ "$(sha256sum "$cap_core" | cut -d' ' -f1)" = "$capsule_core_sha" ] || return 64
    mkdir -m 700 "$cap_dir/preparation.once" || return 64
    # C105 performs its own readiness/boot/package checks. Partial stages are
    # retained, never retried or silently replaced by another source.
    capsule_exec stage "$cap_dir" || return 1
    for cap_name in lib provider-lib state owner watchdog;do mkdir -m 700 "$cap_dir/$cap_name" || return 1;done
    while read -r cap_hash cap_mode cap_dest cap_origin;do
        cap_source=$(capsule_source "$cap_origin") || return 64
        capsule_copy "$cap_source" "$cap_dir/$cap_dest" "$cap_hash" || return 1
    done < "$capsule_package_root/assets.tsv"
    capsule_copy "$cap_dir/inputs/private.gb" "$cap_dir/private.gb" "$cap_rom_sha" || return 1
    printf '%s\n' load > "$cap_dir/role" || return 1
    capsule_identity "$capsule_core_sha" "$cap_rom_sha" > "$cap_dir/identity" || return 1
    printf '%s  %s\n%s  %s\n' "$capsule_core_sha" /opt/muos/share/core/gambatte_libretro.so "$cap_rom_sha" private.gb > "$cap_dir/gb-assets.sha256" || return 1
    for cap_pair in launcher:app-launch store-base:store-base installed-store:installed-store;do
        cap_mark=${cap_pair%%:*};cap_name=${cap_pair#*:}
        sha256sum "$cap_dir/$cap_name.sh" | cut -d' ' -f1 > "$cap_dir/$cap_mark.sha256" || return 1
    done
    capsule_exec staged "$cap_dir" || return 1
    printf 'C107_CAPSULE_READY\n' > "$cap_dir/preparation.once/ready" || return 1
}
