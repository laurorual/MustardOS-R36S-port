#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""RAM-only C12 guard audit on pinned candidate SSH; no boot/power activation."""
from pathlib import Path
import argparse
import hashlib
import io
import ipaddress
import json
import re
import shlex
import subprocess
import tarfile

repo = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("stage", type=Path)
parser.add_argument("phase", choices=["prepare", "start", "finish"])
parser.add_argument("--host", required=True, type=ipaddress.IPv4Address)
args = parser.parse_args()
stage = args.stage.resolve()
assert stage.is_relative_to(repo / "build/phase4/boot-order")
meta = json.loads((stage / "manifest.json").read_text())
assert meta["host_passed"] and not meta["active_inittab_changed"]
assert hashlib.sha256((stage / "deployment.tar").read_bytes()).hexdigest() == meta["deployment_sha256"]
ssh = ["ssh", "-p", "2222", "-i", str(repo / "build/phase4/private/c07-client"),
       "-oIdentitiesOnly=yes", "-oStrictHostKeyChecking=yes",
       "-oHostKeyAlias=[192.168.15.17]:2222",
       "-oUserKnownHostsFile=" + str(repo / "build/phase4/private/c07-known_hosts"),
       "-oBatchMode=yes", "-oConnectTimeout=8", "root@" + str(args.host)]

def remote(label, code, timeout=30):
    result = subprocess.run(ssh + ["sh -s"], input=code, capture_output=True, text=True, timeout=timeout)
    (stage / (label + ".stdout")).write_text(result.stdout)
    (stage / (label + ".stderr")).write_text(result.stderr)
    (stage / (label + ".exit")).write_text(str(result.returncode) + "\n")
    assert result.returncode == 0, (label, result.returncode, result.stdout, result.stderr)
    return result.stdout

guard = r'''set -eu
[ "$(readlink /proc/1/exe)" = /bin/busybox ]
[ "$(uname -r)" = 4.4.189-muos-r35s-p4 ]
[ "$(tr -d '\000' < /sys/firmware/devicetree/base/model)" = 'R36S-V12 2023-08-18 Panel 0' ]
[ "$(cat /proc/sys/kernel/tainted)" = 0 ]
. /usr/libexec/muos-diag-card-guard
boot=$(diag_card /sys); root=${boot%p1}p2
[ "$(findmnt -rn -o MAJ:MIN /)" = "$(cat /sys/class/block/${root##*/}/dev)" ]
[ "$(findmnt -rn -o PARTUUID /)" = 4d554432-02 ]
[ "$(findmnt -rn -o FSTYPE /)" = ext4 ]
findmnt -rn -o OPTIONS / | tr ',' '\n' | grep -qx ro
! findmnt -rn -M /boot >/dev/null
/usr/libexec/muos-c07-network status
[ -f /run/muos/entropy/stopped ] && [ ! -e /run/muos/entropy/ready ]
'''
infra = r'''
for name in udevd wpa_supplicant udhcpc dropbear; do
    main=
    for pid in $(pidof "$name"); do
        [ "$(awk '/^PPid:/ {print $2}' /proc/$pid/status)" = 1 ] || continue
        [ -z "$main" ]; main=$pid
    done
    [ -n "$main" ]
    printf '%s %s %s %s\n' "$name" "$main" "$(awk '{print $22}' /proc/$main/stat)" "$(readlink /proc/$main/exe)"
done
'''
expect = r'''
expect() {
    wanted=$1; label=$2; shift 2
    if "$@"; then actual=0; else actual=$?; fi
    printf '%s expected=%s actual=%s\n' "$label" "$wanted" "$actual"
    [ "$actual" = "$wanted" ]
}
'''
if args.phase == "prepare":
    assert not (stage / "remote-directory").exists(), "Resume existing audit rather than overwrite it"
    (stage / "audit-executed.py").write_bytes(Path(__file__).read_bytes())
    remote("native-preflight", guard + "[ ! -e /run/muos/session ]; [ ! -e /run/muos/boot ]\n")
    remote_dir = remote("allocate", guard + "mktemp -d /run/muos-c12.XXXXXX\n").strip()
    assert re.fullmatch(r"/run/muos-c12\.[A-Za-z0-9]{6}", remote_dir)
    (stage / "remote-directory").write_text(remote_dir + "\n")
    result = subprocess.run(ssh + ["tar -xf - -C " + shlex.quote(remote_dir)],
                            input=(stage / "deployment.tar").read_bytes(), capture_output=True, timeout=25)
    (stage / "upload.stderr").write_bytes(result.stderr)
    assert result.returncode == 0, result.stderr
    q = shlex.quote(remote_dir)
    code = guard + f"cd {q}; sha256sum -c SHA256SUMS\n"
    code += f"printf 'enabled=0\\nallow_power=0\\nsession_package={remote_dir}/session\\nsession_config={remote_dir}/session.conf\\n' > boot.conf\n"
    code += f"printf 'enabled=1\\nlease_seconds=60\\nprofile_dir={remote_dir}/session/profile\\nprerequisites={remote_dir}/session/prerequisites.sha256\\n' > session.conf\n"
    code += "chmod 600 boot.conf session.conf\n"
    code += f"export MUOS_BOOT_CONFIG={q}/boot.conf\n" + expect
    code += f"expect 0 idle-quiescent {q}/boot/service.sh check-stop\n"
    code += f"expect 0 boot-disabled {q}/boot/service.sh start\n"
    code += f"expect 64 power-disabled {q}/boot/service.sh reboot\n"
    code += f"expect 64 foreign-infrastructure-not-adopted {q}/boot/service.sh prepare-stop\n"
    code += "[ ! -e /run/muos/boot ]; [ ! -e /run/muos/session ]\n"
    remote("idle-audit", code)
    remote("infrastructure-before", guard + infra)
    print("C12 RAM-only idle/refusal checks passed:", remote_dir)
else:
    remote_dir = (stage / "remote-directory").read_text().strip()
    assert re.fullmatch(r"/run/muos-c12\.[A-Za-z0-9]{6}", remote_dir)
    q = shlex.quote(remote_dir)
    env = f"export MUOS_BOOT_CONFIG={q}/boot.conf MUOS_SESSION_CONFIG={q}/session.conf\n"
    if args.phase == "start":
        assert not (stage / "active-audit.exit").exists(), "Inspect prior run before starting another generation"
        code = guard + env + expect
        code += f"expect 0 session-start {q}/session/service.sh start\n"
        code += f"expect 0 session-ready {q}/session/service.sh status\n"
        code += f"expect 1 active-session-blocks-quiescence {q}/boot/service.sh check-stop\n"
        code += f"expect 64 power-disabled-while-active {q}/boot/service.sh reboot\n"
        code += f"expect 0 session-still-ready {q}/session/service.sh status\n"
        code += "cat /run/muos/session/current\n"
        remote("active-audit", code, timeout=125)
        assert remote("infrastructure-active", guard + infra) == (stage / "infrastructure-before.stdout").read_text()
        print("Menu ready; C12 refuses quiescence while C11 is active. Lease60; no power request.")
    else:
        code = guard + env + expect
        code += f"expect 0 session-stop {q}/session/service.sh stop\n"
        code += f"expect 0 stopped-session-quiescent {q}/boot/service.sh check-stop\n"
        code += "[ ! -e /run/muos/boot ]; cat /run/muos/session/current\n"
        remote("stopped-audit", code, timeout=120)
        assert remote("infrastructure-after", guard + infra) == (stage / "infrastructure-before.stdout").read_text()
        generation = remote("generation", "cat /run/muos/session/current\n").strip()
        assert generation == "run-0001"
        cycle = "/run/muos/session/" + generation
        names = ["result", "report.txt", "manager", "profile-source.txt", "profile-effective.txt",
                 "original-restored.txt", "volume-before.sha256", "volume-after.sha256",
                 "mixer-before.txt", "mixer-after.txt", "brightness-before.txt", "brightness-after.txt",
                 "drm-before.txt", "drm-after.txt", "first-paint.txt", "rng.txt", "root-writers.txt",
                 "start.log", "stop.log", "restore.log", "remount.txt"]
        code = f"set -eu; cd {cycle}; [ -f done ]; [ \"$(cat result)\" = 0 ]; set --\n"
        code += "for name in " + " ".join(names) + "; do\n"
        code += ' [ -f "$name" ]; [ "$(stat -c %s "$name")" -le 524288 ]; set -- "$@" "$name"\ndone\ntar -cf - "$@"\n'
        result = subprocess.run(ssh + ["sh -s"], input=code.encode(), capture_output=True, timeout=25)
        (stage / "collection.tar").write_bytes(result.stdout)
        (stage / "collection.stderr").write_bytes(result.stderr)
        assert result.returncode == 0, result.stderr
        out = stage / "native"
        out.mkdir(exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(result.stdout)) as archive:
            for entry in archive.getmembers():
                assert entry.isfile() and entry.name in names and entry.size <= 524288
                (out / entry.name).write_bytes(archive.extractfile(entry).read())
        for name in ["profile-effective.txt", "original-restored.txt"]:
            lines = (out / name).read_text().splitlines()
            assert len(lines) == 21 and all(line.endswith(": OK") for line in lines), name
        for before, after in [("mixer-before.txt", "mixer-after.txt"), ("brightness-before.txt", "brightness-after.txt"),
                              ("drm-before.txt", "drm-after.txt"), ("volume-before.sha256", "volume-after.sha256")]:
            assert (out / before).read_bytes() == (out / after).read_bytes(), before
        assert not re.search(rb"^(FD_WRITER|MAP_WRITER)", (out / "root-writers.txt").read_bytes(), re.M)
        remote("prerequisites-after", guard + f"cd {q}; sha256sum -c session/prerequisites.sha256; sha256sum -c SHA256SUMS\n")
        code = guard + env
        code += f"{q}/boot/service.sh check-stop\n"
        code += f"[ \"$(cat {cycle}/result)\" = 0 ]; [ -f {cycle}/done ]; [ ! -e {cycle}/ready ]\n"
        code += '[ "$(find /run/muos/session -maxdepth 1 -type d -name \'run-*\' | wc -l)" = 1 ]\n'
        code += f"rm -rf {q} /run/muos/session\n[ ! -e {q} ]; [ ! -e /run/muos/session ]; [ ! -e /run/muos/boot ]\n"
        code += "echo RAM_REMOVED_ROOT_RO_NETWORK_PRESERVED\n"
        remote("cleanup", code)
        analysis = {
            "passed": True, "scope": "RAM-only C12 guard/quiescence audit against C11 session",
            "guarded_native_candidate": True, "candidate_address": str(args.host),
            "pinned_host_key_unchanged": True, "quiescent_idle_passed": True,
            "quiescence_refused_while_session_ready": True, "session_remained_ready_after_refusal": True,
            "quiescent_after_stop_passed": True, "infrastructure_PID_starttime_unchanged": True,
            "profile_21_and_original_21_hashes_passed": True, "hardware_and_runtime_restored": True,
            "RAM_removed": True, "root_readonly_fat_unmounted_taint0": True,
            "C12_boot_start_or_shutdown_exercised": False, "power_request_sent": False,
            "C12_persistent_files_or_active_inittab_installed": False,
            "C11_private_namespace_transaction_executed": True,
            "private_seed_credentials_keys_collected": False,
            "postboot_offline_fsck_performed": False,
            "audit_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        }
        (stage / "analysis.json").write_text(json.dumps(analysis, indent=2) + "\n")
        print("C12 native quiescence/refusal/restoration audit passed; RAM removed; SSH preserved.")
