#!/bin/sh
# SPDX-License-Identifier: MIT
# Policy around the native BusyBox SeedRNG. Caller fixes paths/owner IDs.
entropy_file_valid() {
    seed_file=$1
    [ -f "$seed_file" ] && [ ! -L "$seed_file" ] || return 1
    [ "$(stat -c '%u:%g:%a:%h' "$seed_file")" = "$seed_uid:$seed_gid:400:1" ] || return 1
    bytes=$(stat -c '%s' "$seed_file")
    [ "$bytes" -ge 32 ] && [ "$bytes" -le 256 ]
}
entropy_seed_valid() { entropy_file_valid "$seed_dir/seed.credit"; }
entropy_dir_valid() {
    [ -d "$seed_dir" ] && [ ! -L "$seed_dir" ] || return 1
    [ "$(stat -c '%u:%g:%a' "$seed_dir")" = "$seed_uid:$seed_gid:700" ]
}
entropy_start() {
    umask 077
    mkdir -p "$entropy_state"
    [ ! -L "$seed_dir" ] || return 1
    [ -e "$seed_dir" ] || mkdir -m 700 "$seed_dir" || return 1
    entropy_dir_valid || return 1
    "$rng_probe" 0 > "$entropy_state/before.txt" 2>&1 || {
        rc=$?; [ "$rc" = 3 ] || return 1
    }
    if [ -e "$seed_dir/seed.credit" ]; then
        entropy_seed_valid || return 1
        echo persisted > "$entropy_state/mode"
        "$native_seedrng" start > "$entropy_state/start.log" 2>&1 || return 1
        grep -Eq '^Seeding [0-9]+ bits and crediting$' "$entropy_state/start.log" || return 1
        "$rng_probe" 60 > "$entropy_state/after.txt" 2>&1 || return 1
        if ! grep -Eq '^Saving [0-9]+ bits of creditable seed for next boot$' "$entropy_state/start.log"; then
            # Old random.c credits the input pool before the nonblocking pool
            # becomes ready. Native SeedRNG can conservatively save no-credit.
            # Never relabel those bytes: after readiness, ask the native tool
            # to consume them WITHOUT credit and generate a fresh ready seed.
            grep -Eq '^Saving [0-9]+ bits of non-creditable seed for next boot$' "$entropy_state/start.log" || return 1
            entropy_file_valid "$seed_dir/seed.no-credit" || return 1
            echo 'Legacy refresh after RNG readiness' >> "$entropy_state/start.log"
            "$native_seedrng" start >> "$entropy_state/start.log" 2>&1 || return 1
            "$rng_probe" 0 >> "$entropy_state/after.txt" 2>&1 || return 1
        fi
    else
        echo seedless > "$entropy_state/mode"
        # No fallback to urandom or synthetic entropy credits while unready.
        "$rng_probe" 60 > "$entropy_state/after.txt" 2>&1 || return 1
        "$native_seedrng" start > "$entropy_state/start.log" 2>&1 || return 1
    fi
    grep -Eq '^Saving [0-9]+ bits of creditable seed for next boot$' "$entropy_state/start.log" || return 1
    entropy_seed_valid || return 1
    stat -c 'seed_owner=%u:%g seed_mode=%a seed_bytes=%s' "$seed_dir/seed.credit" > "$entropy_state/start-metadata.txt"
    touch "$entropy_state/ready"
}
entropy_stop() {
    [ -e "$entropy_state/ready" ] || return 0
    "$rng_probe" 0 > "$entropy_state/stop-ready.txt" 2>&1 || return 1
    "$native_seedrng" stop > "$entropy_state/stop.log" 2>&1 || return 1
    grep -Eq '^Saving [0-9]+ bits of creditable seed for next boot$' "$entropy_state/stop.log" || return 1
    entropy_seed_valid || return 1
    stat -c 'seed_owner=%u:%g seed_mode=%a seed_bytes=%s' "$seed_dir/seed.credit" > "$entropy_state/stop-metadata.txt"
    rm -f "$entropy_state/ready"
    touch "$entropy_state/stopped"
}
entropy_status() {
    [ -f "$entropy_state/ready" ] && entropy_dir_valid && entropy_seed_valid && "$rng_probe" 0
}
