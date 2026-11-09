# SPDX-License-Identifier: MIT
# C119 RAM adoption contract; the original C105 package/stage stays on disk.
c119_package() {
    c105_capsule "$v2_cap" || return 64
    [ "$v2_root" = "$v2_cap/contract-v2" ] || return 64
    [ -d "$v2_root" ] && [ ! -L "$v2_root" ] && [ "$(stat -c %u:%g:%a "$v2_root")" = 0:0:700 ] || return 64
    [ "$(find "$v2_root" -mindepth 1 -maxdepth 1 -print | wc -l)" = 6 ] || return 64
    for n in caller.sh payload.sha256 functions.sh host.sh contract.json LICENSE;do
        c105_regular "$v2_root/$n" 644 || return 64
    done
    [ "$(sha256sum "$v2_root/payload.sha256" | cut -d' ' -f1)" = "$v2_manifest_sha" ] || return 64
    [ "$(awk '{print $2}' "$v2_root/payload.sha256")" = "$(printf '%s\n' functions.sh host.sh contract.json LICENSE)" ] || return 64
    (cd "$v2_root" && sha256sum -c payload.sha256 >/dev/null) || return 64
}
c119_legacy_ready() {
    [ "$1" = "$v2_cap" ] && c119_package || return 64
    for n in caller-stage/run.once caller-v2-stage caller-v2-before selection.once;do
        [ ! -e "$1/$n" ] && [ ! -L "$1/$n" ] || return 64
    done
    c105_package && c105_dependencies && caller_exec platform && c105_staged "$1" && c105_assets "$1" || return 64
    [ -d "$1/preparation.once" ] && [ ! -L "$1/preparation.once" ] && [ "$(stat -c %u:%g:%a "$1/preparation.once")" = 0:0:700 ] || return 64
    c105_regular "$1/preparation.once/ready" 600 && c105_regular "$1/preparation.once/resident" 600 || return 64
    grep -qx C107_CAPSULE_READY "$1/preparation.once/ready" || return 64
    grep -qx C112_RESIDENT_INPUTS_READY_ROM_P3 "$1/preparation.once/resident" || return 64
}
c119_adopt() {
    c119_legacy_ready "$1" || return 64
    # This directory consumes the adoption attempt BEFORE its first mutation.
    # Any partial attempt is retained for inspection; never overwrite/retry.
    mkdir -m 700 "$1/caller-v2-stage" || return 64
    # Race with an old caller is decided by mkdir BEFORE changing any script.
    mkdir -m 700 "$1/caller-stage/run.once" || return 64
    printf '%s\n' "$v2_manifest_sha" > "$1/caller-stage/run.once/adopted-by-c119" || return 1
    mkdir -m 700 "$1/caller-v2-before" || return 1
    for n in ready boot package;do
        (set -C;cat "$1/caller-stage/$n" > "$1/caller-v2-before/$n") || return 1
        chmod 600 "$1/caller-v2-before/$n" || return 1
        cmp -s "$1/caller-stage/$n" "$1/caller-v2-before/$n" || return 1
    done
    (set -C;cat "$1/installed-host.sh" > "$1/caller-v2-before/installed-host.sh") || return 1
    chmod 700 "$1/caller-v2-before/installed-host.sh" || return 1
    cmp -s "$caller_root/installed-host.sh" "$1/caller-v2-before/installed-host.sh" || return 1
    [ ! -e "$1/caller-v2-host.tmp" ] && [ ! -L "$1/caller-v2-host.tmp" ] || return 64
    (set -C;cat "$v2_root/host.sh" > "$1/caller-v2-host.tmp") || return 1
    chmod 700 "$1/caller-v2-host.tmp" || return 1
    c105_regular "$1/caller-v2-host.tmp" 700 && cmp -s "$v2_root/host.sh" "$1/caller-v2-host.tmp" || return 1
    mv -T "$1/caller-v2-host.tmp" "$1/installed-host.sh" || return 1
    caller_exec boot > "$1/caller-v2-stage/boot" || return 1
    printf '%s\n' "$v2_manifest_sha" > "$1/caller-v2-stage/package" || return 1
    printf 'C119_ADOPTED_HOST_BATCH_V1\n' > "$1/caller-v2-stage/ready" || return 1
    c119_staged "$1"
}
c119_staged() {
    [ "$1" = "$v2_cap" ] && c119_package && c105_package && c105_capsule "$1" || return 64
    for d in caller-stage caller-v2-stage caller-v2-before;do
        [ -d "$1/$d" ] && [ ! -L "$1/$d" ] && [ "$(stat -c %u:%g:%a "$1/$d")" = 0:0:700 ] || return 64
    done
    for n in ready boot package;do
        c105_regular "$1/caller-stage/$n" 600 && c105_regular "$1/caller-v2-before/$n" 600 && c105_regular "$1/caller-v2-stage/$n" 600 || return 64
        cmp -s "$1/caller-stage/$n" "$1/caller-v2-before/$n" || return 64
    done
    printf 'C105_STAGE_READY\n' | cmp -s - "$1/caller-stage/ready" || return 64
    printf '%s\n' "$caller_manifest_sha" | cmp -s - "$1/caller-stage/package" || return 64
    caller_exec boot | cmp -s - "$1/caller-stage/boot" || return 64
    caller_exec boot | cmp -s - "$1/caller-v2-stage/boot" || return 64
    printf 'C119_ADOPTED_HOST_BATCH_V1\n' | cmp -s - "$1/caller-v2-stage/ready" || return 64
    printf '%s\n' "$v2_manifest_sha" | cmp -s - "$1/caller-v2-stage/package" || return 64
    c105_regular "$1/caller-v2-before/installed-host.sh" 700 && cmp -s "$caller_root/installed-host.sh" "$1/caller-v2-before/installed-host.sh" || return 64
    for n in $(c105_scripts);do
        c105_regular "$1/$n" 700 || return 64
        if [ "$n" = installed-host.sh ];then src=$v2_root/host.sh;else src=$caller_root/$n;fi
        cmp -s "$src" "$1/$n" || return 64
    done
    [ -d "$1/caller-stage/run.once" ] && [ ! -L "$1/caller-stage/run.once" ] && [ "$(stat -c %u:%g:%a "$1/caller-stage/run.once")" = 0:0:700 ] || return 64
    [ "$(find "$1/caller-stage/run.once" -mindepth 1 -maxdepth 1 -print | wc -l)" = 1 ] || return 64
    c105_regular "$1/caller-stage/run.once/adopted-by-c119" 600 || return 64
    printf '%s\n' "$v2_manifest_sha" | cmp -s - "$1/caller-stage/run.once/adopted-by-c119" || return 64
    for n in caller-v2-stage/run.once caller-v2-host.tmp;do
        [ ! -e "$1/$n" ] && [ ! -L "$1/$n" ] || return 64
    done
    c105_assets "$1"
}
