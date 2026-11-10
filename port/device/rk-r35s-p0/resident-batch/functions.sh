# SPDX-License-Identifier: MIT
# C122 copies the qualified C120 contract from a read-only resident prefix.
rb_names() { printf '%s\n' functions.sh host.sh contract.json LICENSE payload.sha256 caller.sh resident-functions.sh; }
rb_package() {
    for p in "$rb_system_root" "$rb_system_root/usr" "$rb_system_root/usr/libexec" "$rb_root";do
        [ -d "$p" ] && [ ! -L "$p" ] && [ "$(stat -c %u:%g:%a "$p")" = 0:0:755 ] || return 64
    done
    [ "$(find "$rb_root" -mindepth 1 -maxdepth 1 -print | wc -l)" = 9 ] || return 64
    for n in $(rb_names) resident.sha256 load.sh;do c105_regular "$rb_root/$n" 644 || return 64;done
    [ "$(sha256sum "$rb_root/resident.sha256" | cut -d' ' -f1)" = "$rb_manifest_sha" ] || return 64
    [ "$(awk '{print $2}' "$rb_root/resident.sha256")" = "$(rb_names)" ] || return 64
    (cd "$rb_root" && sha256sum -c resident.sha256 >/dev/null) || return 64
}
rb_ready() {
    [ "$#" = 1 ] && rb_package && c105_package && c105_dependencies && caller_exec platform && c105_capsule "$1" || return 64
    for n in contract-v3 caller-stage/run.once caller-v3-stage caller-v3-before selection.once;do
        [ ! -e "$1/$n" ] && [ ! -L "$1/$n" ] || return 64
    done
    c105_staged "$1" && c105_assets "$1" || return 64
    [ -d "$1/preparation.once" ] && [ ! -L "$1/preparation.once" ] && [ "$(stat -c %u:%g:%a "$1/preparation.once")" = 0:0:700 ] || return 64
    c105_regular "$1/preparation.once/ready" 600 && c105_regular "$1/preparation.once/resident" 600 || return 64
    printf 'C107_CAPSULE_READY\n' | cmp -s - "$1/preparation.once/ready" || return 64
    printf 'C112_RESIDENT_INPUTS_READY_ROM_P3\n' | cmp -s - "$1/preparation.once/resident" || return 64
}
rb_adopt() {
    rb_ready "$1" || return 64
    # This directory reserves the copy before its first leaf. A partial copy
    # remains owned by this capsule and is never overwritten or retried.
    mkdir -m 700 "$1/contract-v3" || return 64
    for n in functions.sh host.sh contract.json LICENSE payload.sha256 caller.sh;do
        (set -C;cat "$rb_root/$n" > "$1/contract-v3/$n") || return 1
        chmod 644 "$1/contract-v3/$n" || return 1
        c105_regular "$1/contract-v3/$n" 644 && cmp -s "$rb_root/$n" "$1/contract-v3/$n" || return 1
    done
    caller_exec adopt "$1" || return 1
}
