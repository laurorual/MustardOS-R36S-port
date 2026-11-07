# SPDX-License-Identifier: MIT
# C112: installed public inputs, one private ROM from the data volume.
resident_regular() { [ -f "$1" ] && [ ! -L "$1" ] && [ "$(stat -c '%u:%g:%a:%h' "$1")" = "0:0:$2:1" ]; }
resident_capsule() {
    case "$1" in /run/muos-prefs-data.??????) ;;*) return 64;;esac
    case "${1#/run/muos-prefs-data.}" in *[!A-Za-z0-9]*) return 64;;esac
    [ -d "$1" ] && [ ! -L "$1" ] && [ "$(stat -c '%u:%g:%a' "$1")" = 0:0:700 ] || return 64
    [ "$(findmnt -rn -T "$1" -o FSTYPE)" = tmpfs ]
}
resident_package() {
    for rp in "$resident_system_root" "$resident_system_root/usr" "$resident_system_root/usr/libexec" "$resident_root";do
        [ -d "$rp" ] && [ ! -L "$rp" ] && [ "$(stat -c '%u:%g:%a' "$rp")" = 0:0:755 ] || return 64
    done
    resident_regular "$resident_root/load.sh" 644 && resident_regular "$resident_root/payload.sha256" 644 || return 64
    [ "$(sha256sum "$resident_root/payload.sha256" | cut -d' ' -f1)" = "$resident_manifest_sha" ] || return 64
    [ "$(awk '{print $2}' "$resident_root/payload.sha256")" = "$(printf '%s\n' functions.sh assets.tsv dependencies.tsv contract.json LICENSE LICENSE.frontend runner state-metadata menu-libmuxmod.so provider-probe sync-path)" ] || return 64
    [ "$(find "$resident_root" -mindepth 1 -maxdepth 1 -print | wc -l)" = 13 ] || return 64
    while read -r rh rn;do
        resident_regular "$resident_root/$rn" 644 || return 64
        [ "$(sha256sum "$resident_root/$rn" | cut -d' ' -f1)" = "$rh" ] || return 64
    done < "$resident_root/payload.sha256"
    while read -r rh rm rn;do
        resident_regular "$resident_system_root/$rn" "$rm" || return 64
        [ "$(sha256sum "$resident_system_root/$rn" | cut -d' ' -f1)" = "$rh" ] || return 64
    done < "$resident_root/dependencies.tsv"
}
resident_inputs() {
    [ -d "$1/inputs" ] && [ ! -L "$1/inputs" ] && [ "$(stat -c '%u:%g:%a' "$1/inputs")" = 0:0:700 ] || return 64
    [ "$(find "$1/inputs" -mindepth 1 -maxdepth 1 -print | wc -l)" = "$2" ] || return 64
    while read -r rh rn;do
        resident_regular "$1/inputs/$rn" 700 || return 64
        [ "$(sha256sum "$1/inputs/$rn" | cut -d' ' -f1)" = "$rh" ] || return 64
    done < "$resident_root/assets.tsv"
}
resident_rom_copy() {
    [ -d "$1/MUOS" ] && [ ! -L "$1/MUOS" ] || return 64
    case "$(stat -c '%u:%g:%a' "$1/MUOS")" in 0:0:700|0:0:755) ;;*) return 64;;esac
    rr=$1/MUOS/port-roms-v1
    for rp in "$rr" "$rr/gb";do
        [ -d "$rp" ] && [ ! -L "$rp" ] && [ "$(stat -c '%u:%g:%a' "$rp")" = 0:0:700 ] || return 64
    done
    [ "$(find "$rr" -mindepth 1 -maxdepth 1 -print | wc -l)" = 3 ] || return 64
    [ "$(find "$rr/gb" -mindepth 1 -maxdepth 1 -print | wc -l)" = 1 ] || return 64
    for rp in "$rr/.muos-rom-root-v1" "$rr/ROM.sha256" "$rr/gb/private.gb";do resident_regular "$rp" 600 || return 64;done
    printf 'MUOS-R35S-ROM-ROOT-V1\n' | cmp -s - "$rr/.muos-rom-root-v1" || return 64
    [ "$(wc -c < "$rr/ROM.sha256")" = 80 ] || return 64
    read -r rh rn < "$rr/ROM.sha256"
    [ "${#rh}" = 64 ] && [ "$rn" = gb/private.gb ] || return 64
    case "$rh" in *[!0-9a-f]*) return 64;;esac
    rb=$(stat -c %s "$rr/gb/private.gb")
    [ "$rb" -ge 32768 ] && [ "$rb" -le 8388608 ] || return 64
    [ "$(sha256sum "$rr/gb/private.gb" | cut -d' ' -f1)" = "$rh" ] || return 64
    resident_inputs "$2" 4 || return 64
    [ ! -e "$2/inputs/private.gb" ] && [ ! -L "$2/inputs/private.gb" ] || return 64
    (set -C;cat "$rr/gb/private.gb" > "$2/inputs/private.gb") || return 1
    chmod 700 "$2/inputs/private.gb" || return 1
    resident_regular "$2/inputs/private.gb" 700 && cmp -s "$rr/gb/private.gb" "$2/inputs/private.gb" || return 1
}
resident_prepare() {
    [ "$#" = 1 ] && resident_capsule "$1" && resident_package && resident_exec platform || return 64
    [ -z "$(find "$1" -mindepth 1 -maxdepth 1 -print)" ] || return 64
    mkdir -m 700 "$1/inputs" || return 1
    while read -r rh rn;do
        (set -C;cat "$resident_root/$rn" > "$1/inputs/$rn") || return 1
        chmod 700 "$1/inputs/$rn" || return 1
    done < "$resident_root/assets.tsv"
    resident_inputs "$1" 4 && resident_exec read-rom "$1" && resident_inputs "$1" 5 || return 1
    resident_exec platform && resident_exec prepare "$1" || return 1
    printf 'C112_RESIDENT_INPUTS_READY_ROM_P3\n' > "$1/preparation.once/resident" || return 1
}
