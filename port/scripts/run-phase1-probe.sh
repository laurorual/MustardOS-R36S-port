#!/usr/bin/env bash
set -euo pipefail

repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
artifact="$repo/dist/phase1/muinput"
if [[ $# != 1 ]]; then
    printf 'Usage: bash %s user@host | --emit-script\n' "$0" >&2
    exit 2
fi
[[ -f "$artifact" ]] || { printf 'Build dist/phase1/muinput first.\n' >&2; exit 1; }
(
    cd "$repo/dist/phase1"
    sha256sum --check --status SHA256SUMS
)
expected_hash=$(sha256sum "$artifact")
expected_hash=${expected_hash%% *}

emit_probe() {
    printf 'expected_sha256=%s\n' "$expected_hash"
    cat <<'REMOTE'
set -eu
export PATH=/usr/bin:/bin LC_ALL=C
unset LD_LIBRARY_PATH LD_PRELOAD
[ "$(id -u)" -ne 0 ] || { echo 'Run as ark, without sudo.' >&2; exit 1; }
model=$(tr '\000' '\n' < /sys/firmware/devicetree/base/model)
[ "$model" = 'R36S-V12 2023-08-18 Panel 0' ] || { echo 'Unexpected device model.' >&2; exit 1; }
[ "$(uname -m)" = aarch64 ] || { echo 'Expected native AArch64.' >&2; exit 1; }
[ "$(getconf GNU_LIBC_VERSION)" = 'glibc 2.41' ] || { echo 'Review target glibc before proceeding.' >&2; exit 1; }
loader=/lib/ld-linux-aarch64.so.1
[ -x "$loader" ] || { echo 'Expected loader is missing.' >&2; exit 1; }
options=$(findmnt -n -o OPTIONS -T /tmp)
case ",$options," in
    *,noexec,*) echo '/tmp is mounted noexec; no files transferred.' >&2; exit 1 ;;
esac
printf 'MODEL=%s\nKERNEL=%s\nLIBC=%s\n' "$model" "$(uname -r)" "$(getconf GNU_LIBC_VERSION)"
findmnt -T /tmp -o TARGET,FSTYPE,OPTIONS
umask 077
probe=$(mktemp -d /tmp/muos-r35s-phase1.XXXXXX)
cleanup() {
    rm -f -- "$probe/muinput"
    rmdir -- "$probe"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
base64 -d > "$probe/muinput" <<'MUINPUT_BASE64'
REMOTE
    base64 < "$artifact"
    cat <<'REMOTE'
MUINPUT_BASE64
printf '%s  %s\n' "$expected_sha256" "$probe/muinput" | sha256sum -c -
chmod 700 "$probe/muinput"
env -i PATH=/usr/bin:/bin LC_ALL=C "$loader" --verify "$probe/muinput"
env -i PATH=/usr/bin:/bin LC_ALL=C "$loader" --list "$probe/muinput"
if env -i PATH=/usr/bin:/bin LC_ALL=C MUOS_RUMBLE_STRENGTH=0 \
    "$probe/muinput" --list-devices; then
    result=0
else
    result=$?
fi
printf 'LIST_DEVICES_EXIT_STATUS=%s\n' "$result"
exit "$result"
REMOTE
}

if [[ $1 == --emit-script ]]; then
    emit_probe
    exit
fi
[[ $1 =~ ^[a-zA-Z0-9_][a-zA-Z0-9_.@-]*$ ]] || { printf 'Use user@host.\n' >&2; exit 2; }
mkdir -p "$repo/build/phase1"
report="$repo/build/phase1/device-test-$(date -u +%Y%m%dT%H%M%SZ).txt"
ssh_options=(-o StrictHostKeyChecking=yes -o ConnectTimeout=10)
if [[ -n ${MUOS_SSH_CONTROL:-} ]]; then
    ssh_options+=(-S "$MUOS_SSH_CONTROL" -o BatchMode=yes)
fi
printf 'Testing only --list-devices; SSH may prompt for your password locally.\n'
emit_probe | ssh "${ssh_options[@]}" -- "$1" sh -s | tee "$report"
printf 'Report: %s\n' "$report"
