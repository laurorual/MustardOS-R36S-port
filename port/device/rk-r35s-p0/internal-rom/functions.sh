# SPDX-License-Identifier: MIT
# C113 writes only a previously absent private ROM shelf, without overwrites.
rom_regular() { [ -f "$1" ] && [ ! -L "$1" ] && [ "$(stat -c '%u:%g:%a:%h' "$1")" = "0:0:$2:1" ]; }
rom_parent() {
 [ -d "$rom_mount/MUOS" ] && [ ! -L "$rom_mount/MUOS" ] || return 64
 case "$(stat -c '%u:%g:%a' "$rom_mount/MUOS")" in 0:0:700|0:0:755) ;;*) return 64;;esac
}
rom_absent() {
 rom_parent || return 64
 for rp in "$rom_mount/MUOS/port-roms-v1" "$rom_mount/MUOS/.port-roms-v1.new";do
  [ ! -e "$rp" ] && [ ! -L "$rp" ] || return 64
 done
}
rom_inputs() {
 rom_regular "$rom_cap/private.gb" 600 && rom_regular "$rom_cap/ROM.sha256" 600 || return 64
 [ "$(wc -c < "$rom_cap/ROM.sha256")" = 80 ] || return 64
 read -r rom_hash rom_name < "$rom_cap/ROM.sha256"
 [ "${#rom_hash}" = 64 ] && [ "$rom_name" = gb/private.gb ] || return 64
 case "$rom_hash" in *[!0-9a-f]*) return 64;;esac
 rom_bytes=$(stat -c %s "$rom_cap/private.gb")
 [ "$rom_bytes" -ge 32768 ] && [ "$rom_bytes" -le 8388608 ] || return 64
 [ "$(sha256sum "$rom_cap/private.gb" | cut -d' ' -f1)" = "$rom_hash" ]
}
rom_inventory() (
 cd "$rom_mount" || exit 64
 [ -z "$(find . -type l -print)" ] || exit 64
 [ -z "$(find . ! -type d ! -type f -print)" ] || exit 64
 find . -path ./MUOS/port-roms-v1 -prune -o -path ./MUOS/.port-roms-v1.new -prune -o \
  -type d -exec stat -c 'D %u:%g:%a %n' '{}' ';' -o \
  -type f -exec stat -c 'F %u:%g:%a:%h:%s:%i:%Y %n' '{}' ';' -exec sha256sum '{}' ';' | LC_ALL=C sort
)
rom_check() {
 rc_root=$1
 [ -d "$rc_root" ] && [ ! -L "$rc_root" ] && [ "$(stat -c '%u:%g:%a' "$rc_root")" = 0:0:700 ] || return 64
 [ -d "$rc_root/gb" ] && [ ! -L "$rc_root/gb" ] && [ "$(stat -c '%u:%g:%a' "$rc_root/gb")" = 0:0:700 ] || return 64
 [ "$(find "$rc_root" -mindepth 1 -maxdepth 1 -print | wc -l)" = 3 ] || return 64
 [ "$(find "$rc_root/gb" -mindepth 1 -maxdepth 1 -print | wc -l)" = 1 ] || return 64
 for rp in "$rc_root/gb/private.gb" "$rc_root/ROM.sha256" "$rc_root/.muos-rom-root-v1";do rom_regular "$rp" 600 || return 64;done
 printf 'MUOS-R35S-ROM-ROOT-V1\n' | cmp -s - "$rc_root/.muos-rom-root-v1" || return 64
 cmp -s "$rom_cap/ROM.sha256" "$rc_root/ROM.sha256" && cmp -s "$rom_cap/private.gb" "$rc_root/gb/private.gb"
}
rom_write() {
 rom_absent && rom_inputs || return 64
 rom_stage=$rom_mount/MUOS/.port-roms-v1.new;rom_final=$rom_mount/MUOS/port-roms-v1
 mkdir -m 700 "$rom_stage" || return 1
 rom_exec directory-created || return 1
 mkdir -m 700 "$rom_stage/gb" || return 1
 (set -C;cat "$rom_cap/private.gb" > "$rom_stage/gb/private.gb") || return 1
 chmod 600 "$rom_stage/gb/private.gb" || return 1
 rom_exec ROM-copied || return 1
 (set -C;cat "$rom_cap/ROM.sha256" > "$rom_stage/ROM.sha256") || return 1
 (set -C;printf 'MUOS-R35S-ROM-ROOT-V1\n' > "$rom_stage/.muos-rom-root-v1") || return 1
 rom_check "$rom_stage" || return 1
 rom_exec sync "$rom_stage/gb/private.gb" "$rom_stage/ROM.sha256" "$rom_stage/.muos-rom-root-v1" || return 74
 rom_exec sync "$rom_stage/gb" "$rom_stage" || return 74
 rom_exec before-publish || return 1
 [ ! -e "$rom_final" ] && [ ! -L "$rom_final" ] || return 64
 mv -nT "$rom_stage" "$rom_final" || return 1
 [ ! -e "$rom_stage" ] && [ ! -L "$rom_stage" ] || return 1
 rom_exec after-publish || return 74
 rom_exec sync "$rom_mount/MUOS" || return 74
 rom_check "$rom_final"
}
