#!/bin/sh
# SPDX-License-Identifier: MIT
# One explicitly initialized GB identity. All runtime writers remain in tmpfs.
set -eu
umask 077
capsule=${1:-};op=${2:-}
case "$capsule" in /run/muos-prefs-data.??????) ;; *) exit 64;;esac
case "$op" in seed|verify) ;; *) exit 64;;esac
[ "$#" = 2 ] && [ ! -L "$capsule" ] && [ "$(stat -c '%u:%g:%a' "$capsule")" = 0:0:700 ]
for name in identity role;do
 [ -f "$capsule/$name" ] && [ ! -L "$capsule/$name" ]
 [ "$(stat -c '%u:%g:%a:%h' "$capsule/$name")" = 0:0:600:1 ]
done
identity=$(cat "$capsule/identity")
[ "${#identity}" = 64 ]
case "$identity" in *[!0-9a-f]*) exit 64;;esac
role=$(cat "$capsule/role")
case "$role" in load) ;; *) exit 64;;esac
. /usr/libexec/muos-session/card-guard.sh
. /usr/libexec/muos-session/data-functions.sh
prefs_mount=$capsule/data
prefs_data_mounted ro
root=$prefs_mount/MUOS/port-saves-v1
store=$root/gb/$identity
native=/run/muos/storage/pickles/state/gambatte/GB/private
state=$capsule/state
pair_hash() { (cd "$prefs_mount/MUOS/preferences" && find . -type f -exec sha256sum '{}' ';' | sort); }
pair_hash > "$state/store-prefs-$op-before.sha256"
finish() {
 rc=$?;trap - EXIT HUP INT TERM;data_ro=0
 if prefs_data_mounted ro;then
  data_ro=1
  pair_hash > "$state/store-prefs-$op-after.sha256" || rc=74
  cmp "$state/store-prefs-$op-before.sha256" "$state/store-prefs-$op-after.sha256" || rc=74
 else rc=74;fi
 printf 'C53_STORE_END operation=%s status=%s data_ro=%s\n' "$op" "$rc" "$data_ro"
 exit "$rc"
}
trap finish EXIT
trap 'exit 143' HUP INT TERM
checked_tree() {
 [ ! -L "$prefs_mount/MUOS" ]
 case "$(stat -c '%u:%g:%a' "$prefs_mount/MUOS")" in 0:0:700|0:0:755) ;; *) return 64;;esac
 for path in "$root" "$root/gb" "$store";do
  [ -d "$path" ] && [ ! -L "$path" ]
  [ "$(stat -c '%u:%g:%a' "$path")" = 0:0:700 ]
 done
 for marker in "$root/.muos-save-root-v1" "$store/.muos-saves-v1";do
  [ -f "$marker" ] && [ ! -L "$marker" ] && [ "$(stat -c '%u:%g:%a:%h' "$marker")" = 0:0:600:1 ]
 done
 printf 'MUOS-R35S-SAVE-ROOT-V1\n' | cmp -s - "$root/.muos-save-root-v1"
 printf 'MUOS-R35S-SAVES-V1\n' | cmp -s - "$store/.muos-saves-v1"
}
status() { /bin/sh "$capsule/installed-store.sh" "$capsule" status "$store" "$identity"; }
store_hash() { (cd "$store" && find . -type f -exec sha256sum '{}' ';' | sort); }
case "$op" in
 seed)
  checked_tree
  status > "$state/store-seed-status.txt"
  if [ "$role" = save ];then
   printf 'MUOS_SAVE_STORE_OK current=00000000 previous=00000000 next=00000001\n' | cmp -s - "$state/store-seed-status.txt"
   printf 'C53_SEED_EMPTY current=0\n'
  else
   [ "$role" = load ]
   printf 'MUOS_SAVE_STORE_OK current=00000001 previous=00000000 next=00000002\n' | cmp -s - "$state/store-seed-status.txt"
   for path in /run/muos/storage/pickles/state /run/muos/storage/pickles/state/gambatte /run/muos/storage/pickles/state/gambatte/GB "$native";do
    [ ! -L "$path" ];mkdir -p -m 700 "$path"
   done
   [ "$(findmnt -rn -T "$native" -o FSTYPE)" = tmpfs ]
   /bin/sh "$capsule/installed-store.sh" "$capsule" export "$store" "$identity" "$native" > "$state/store-export-status.txt"
   "$capsule/state-metadata" "$native" > "$state/seed-metadata.txt"
   store_hash > "$state/store-readonly-before.sha256"
   printf 'C53_SEEDED_FROM_EXT4 current=1 identity_matched=1 metadata_valid=1\n'
  fi
  ;;
 verify)
  [ "$role" = load ]
  checked_tree
  status > "$state/store-verify-status.txt"
  cmp "$state/store-seed-status.txt" "$state/store-verify-status.txt"
  store_hash > "$state/store-readonly-after.sha256"
  cmp "$state/store-readonly-before.sha256" "$state/store-readonly-after.sha256"
  printf 'C53_STORE_READONLY_BYTE_EXACT current=1\n'
  ;;
esac
