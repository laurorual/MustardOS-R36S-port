#!/usr/bin/env bash
# A bounded native libc probe, with its own loader/libs under /tmp only.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
artifact="$repo/dist/phase4/rootfs-headless"
[[ $# == 1 && ( $1 == --emit-script || $1 =~ ^[a-zA-Z0-9_][a-zA-Z0-9_.@-]*$ ) ]] || {
    echo 'Usage: bash port/scripts/run-phase4-abi-probe.sh user@host|--emit-script' >&2; exit 2;
}
(cd "$artifact" && sha256sum --check --status SHA256SUMS)
emit_probe() {
    cat <<'REMOTE'
set -eu
export PATH=/usr/bin:/bin LC_ALL=C
unset LD_LIBRARY_PATH LD_PRELOAD
ulimit -c 0
[ "$(id -u)" -ne 0 ]
[ "$(uname -m)" = aarch64 ]
[ "$(uname -r)" = 4.4.189 ]
[ "$(cat /proc/sys/kernel/tainted)" = 0 ]
[ "$(tr '\000' '\n' < /sys/firmware/devicetree/base/model)" = 'R36S-V12 2023-08-18 Panel 0' ]
case ",$(findmnt -n -o OPTIONS /)," in *,rw,*) ;; *) exit 1 ;; esac
case ",$(findmnt -n -o OPTIONS -T /tmp)," in *,noexec,*) exit 1 ;; esac
umask 077
probe=$(mktemp -d /tmp/muos-r35s-phase4-abi.XXXXXX)
cleanup() {
    rm -f -- "$probe/abi-probe" "$probe/libc.so.6" "$probe/ld-linux-aarch64.so.1" "$probe/result.txt" "$probe/loader.txt"
    rmdir -- "$probe"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
REMOTE
    for file in abi-probe abi-runtime/libc.so.6 abi-runtime/ld-linux-aarch64.so.1; do
        name=${file##*/}
        hash=$(sha256sum "$artifact/$file"); hash=${hash%% *}
        printf 'base64 -d > "$probe/%s" <<\x27PHASE4_PAYLOAD\x27\n' "$name"
        base64 < "$artifact/$file"
        printf 'PHASE4_PAYLOAD\n'
        printf 'printf "%%s  %%s\\n" %s "$probe/%s" | sha256sum -c -\n' "$hash" "$name"
    done
    cat <<'REMOTE'
chmod 700 "$probe/abi-probe" "$probe/ld-linux-aarch64.so.1"
printf 'KERNEL=%s\nMODEL=%s\n' "$(uname -r)" "$(tr '\000' '\n' < /sys/firmware/devicetree/base/model)"
env -i PATH=/usr/bin:/bin LC_ALL=C timeout -k 2 15 \
    "$probe/ld-linux-aarch64.so.1" --inhibit-cache --library-path "$probe" \
    --list "$probe/abi-probe" > "$probe/loader.txt"
cat "$probe/loader.txt"
env -i PATH=/usr/bin:/bin LC_ALL=C timeout -k 2 15 \
    "$probe/ld-linux-aarch64.so.1" --inhibit-cache --library-path "$probe" \
    "$probe/abi-probe" > "$probe/result.txt"
cat "$probe/result.txt"
grep -Fqx "libc_path=$probe/libc.so.6" "$probe/result.txt"
[ "$(cat /proc/sys/kernel/tainted)" = 0 ]
printf 'PHASE4_NATIVE_ABI_EXIT_STATUS=0\n'
REMOTE
}
if [[ $1 == --emit-script ]]; then
    emit_probe
    exit
fi
ssh_options=(-o StrictHostKeyChecking=yes -o ConnectTimeout=10)
if [[ -n ${MUOS_SSH_CONTROL:-} ]]; then
    ssh_options+=(-S "$MUOS_SSH_CONTROL" -o BatchMode=yes)
fi
report="$repo/build/phase4/native-abi-$(date -u +%Y%m%dT%H%M%SZ).txt"
emit_probe | ssh "${ssh_options[@]}" -- "$1" sh -s | tee "$report"
printf 'Report: %s\n' "$report"
