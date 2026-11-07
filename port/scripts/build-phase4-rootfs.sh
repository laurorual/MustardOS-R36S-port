#!/usr/bin/env bash
# Host-only, resumable Buildroot jobs. Never deploys or accesses block devices.
# Usage: bash port/scripts/build-phase4-rootfs.sh prepare|fetch|build|status|stop
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
name=muos-r35s-phase4-rootfs
image=localhost/muos-r35s-phase4-rootfs:20261024
if [[ -f "$work/core/active" && ${1:-status} != status ]]; then
    echo 'The additive core profile is active; use build-phase4-core.sh.' >&2
    exit 1
fi
case "${1:-status}" in
    prepare)
        expected=3cd1cfa51f9ac90aa5ce793a2274d982b62c240c2897808e582e11fcc7737f49
        actual=$(podman image inspect --format '{{.Id}}' localhost/muos-r35s-phase4-kernel:20261024)
        [[ ${actual#sha256:} == "$expected" ]]
        if podman container exists "$name"; then
            [[ $(podman inspect --format '{{.State.Running}}' "$name") == false ]]
        fi
        bash "$repo/port/scripts/configure-phase4-rootfs.sh"
        podman build --pull=never --iidfile "$work/rootfs-container.iid" -t "$image" \
            -f "$repo/port/packaging/phase4-rootfs.Containerfile" "$repo/port/packaging" \
            > "$work/rootfs-container-build.log" 2>&1
        ;;
    fetch|build)
        stage=$1
        if podman container exists "$name"; then
            [[ $(podman inspect --format '{{.State.Running}}' "$name") == false ]] || {
                echo 'A rootfs job is already running; use status.' >&2; exit 1;
            }
            podman logs "$name" > "$work/rootfs-previous-job.log" 2>&1
            podman rm "$name" >/dev/null
        fi
        [[ -f "$work/rootfs-container.iid" && -f "$work/rootfs-output/.config" ]]
        [[ $(git -C "$work/buildroot" rev-parse HEAD) == 4f924fd52841608d68ac3dcb83fccee8b8c90316 ]]
        [[ -z $(git -C "$work/buildroot" status --porcelain --untracked-files=no) ]]
        # Refuse to resume a build against a silently edited defconfig.
        cmp "$repo/port/device/rk-r35s-p0/phase4-rootfs.defconfig" "$work/headless.defconfig"
        available=$(df --output=avail -k "$work" | tail -1)
        (( available > 20 * 1024 * 1024 )) || { echo 'Need at least 20 GiB free.' >&2; exit 1; }
        network=none
        target=all
        if [[ $stage == fetch ]]; then network=slirp4netns; target=source; fi
        if [[ $stage == build ]]; then
            [[ $(cat "$work/rootfs-fetch.exit" 2>/dev/null) == 0 ]] || {
                echo 'Run fetch successfully before the offline build.' >&2; exit 1;
            }
            expected_headers=$(python3 - "$repo/port/device/rk-r35s-p0/phase4-sources.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1]))['rootfs_configuration']['headers_archive_sha256'])
PY
            )
            printf '%s  %s\n' "$expected_headers" \
                "$work/rootfs-downloads/linux/d8402159c04b1044106b4f27b7ed7c22ed09228f.tar.gz" | sha256sum -c -
        fi
        rm -f "$work/rootfs-$stage.exit"
        epoch=$(git -C "$work/buildroot" show -s --format=%ct HEAD)
        headers_sha=$(python3 - "$repo/port/device/rk-r35s-p0/phase4-sources.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1]))['rootfs_configuration']['headers_archive_sha256'])
PY
        )
        podman run --detach --name "$name" --network="$network" --read-only \
            --cap-drop=all --security-opt=no-new-privileges --userns=keep-id \
            --memory=12g --pids-limit=2048 --tmpfs /tmp:rw,nosuid,nodev,size=2g \
            -v "$work:/work:rw,z" -w /work/buildroot \
            -e SOURCE_DATE_EPOCH="$epoch" -e PHASE4_STAGE="$stage" \
            -e PHASE4_TARGET="$target" -e PHASE4_JOBS="${PHASE4_JOBS:-8}" \
            -e PHASE4_HEADERS_SHA256="$headers_sha" \
            "$(cat "$work/rootfs-container.iid")" sh -c '
            set -u
            cp /usr/local/share/phase4-rootfs-packages.txt /work/rootfs-packages.txt
            printf "%s\n" "$PHASE4_STAGE" > /work/rootfs-job-stage
            make O=/work/rootfs-output BR2_DL_DIR=/work/rootfs-downloads \
                BR2_JLEVEL="$PHASE4_JOBS" \
                BR2_WGET="wget --passive-ftp -nd -t 3 --connect-timeout=10 --read-timeout=30" \
                "$PHASE4_TARGET" > /work/rootfs-"$PHASE4_STAGE".log 2>&1
            result=$?
            if [ "$result" = 0 ] && [ "$PHASE4_STAGE" = fetch ]; then
                printf "%s  %s\n" "$PHASE4_HEADERS_SHA256" \
                    /work/rootfs-downloads/linux/d8402159c04b1044106b4f27b7ed7c22ed09228f.tar.gz \
                    | sha256sum -c - >> /work/rootfs-fetch.log 2>&1
                result=$?
            fi
            printf "%s\n" "$result" > /work/rootfs-"$PHASE4_STAGE".exit
            tail -40 /work/rootfs-"$PHASE4_STAGE".log
            exit "$result"
            '
        printf 'Detached %s started. Use: bash port/scripts/build-phase4-rootfs.sh status\n' "$stage"
        ;;
    status)
        if podman container exists "$name"; then
            podman inspect --format '{{if .State.Running}}running=true exit=pending{{else}}running=false exit={{.State.ExitCode}}{{end}} started={{.State.StartedAt}}' "$name"
            stage=$(cat "$work/rootfs-job-stage" 2>/dev/null || true)
            if [[ $stage == fetch || $stage == build ]]; then
                awk '/^>>>/ {last=$0} END {print last}' "$work/rootfs-$stage.log" 2>/dev/null || true
                tail -4 "$work/rootfs-$stage.log" 2>/dev/null | cut -c1-220 || true
            fi
        else
            echo 'No rootfs job container. Use prepare, then fetch, then build.'
        fi
        ;;
    stop)
        # Only stops the local build container. Incremental output is retained.
        podman stop --time=30 "$name"
        ;;
    *) echo 'Usage: prepare|fetch|build|status|stop' >&2; exit 2 ;;
esac
