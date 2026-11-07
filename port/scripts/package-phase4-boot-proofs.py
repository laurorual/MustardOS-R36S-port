#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze explicit public C12 records. Never collect live files or private state."""
from pathlib import Path
import hashlib
import json
import shutil

repo = Path(__file__).resolve().parents[2]
work = repo / "build/phase4"
area = work / "boot-order"
stage = Path((area / "latest-coordinator").read_text().strip()).resolve()
assert stage.is_relative_to(area)
meta = json.loads((stage / "manifest.json").read_text())
analysis = json.loads((stage / "analysis.json").read_text())
assert meta["host_passed"] and analysis["passed"] and analysis["RAM_removed"]
assert not analysis["power_request_sent"] and not analysis["C12_boot_start_or_shutdown_exercised"]
assert json.loads((stage / "user-confirmation.json").read_text())["confirmed"]
health = (stage / "final-health.stdout").read_text()
for marker in ["NETWORK_OK", "TAINT=0", "KERNEL_ERROR_SIGNATURES=0", "IDLE_RAM_REMOVED"]:
    assert marker in health
assert "/dev/mmcblk0p2 ext4 ro," in health
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
for name, digest in meta["source_sha256"].items():
    assert sha(repo / name) == digest, name
assert sha(stage / "audit-executed.py") == analysis["audit_script_sha256"]
assert (work / "graphics-config/output/.config").read_bytes() == (work / "network-tools/baseline.config").read_bytes()
analysis["boot_sequence"] = int(health.split("BOOT_SEQUENCE=", 1)[1].splitlines()[0])
analysis["selected_kernel_error_signatures"] = 0
(stage / "analysis.json").write_text(json.dumps(analysis, indent=2) + "\n")

pre = repo / "dist/phase4/boot-coordinator-preflight"
native = repo / "dist/phase4/boot-coordinator-native"
assert not pre.exists() and not native.exists(), "Never overwrite immutable proof directories"
pre.mkdir(parents=True)
native.mkdir(parents=True)

def copy(src, dest):
    assert src.is_file() and not src.is_symlink(), src
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)

for name in ["manifest.json", "recipe.mk", "recipe.stdout", "recipe.stderr", "audit.stdout", "audit.stderr",
             "bounded-elf.txt", "bounded-loader.txt"]:
    copy(stage / name, pre / name)
for dirname in ["root-layout", "recipe-target", "source", "package"]:
    for path in sorted((stage / dirname).rglob("*")):
        if path.is_file():
            copy(path, pre / path.relative_to(stage))
for label, pointer in [("order", "latest-checks"), ("adapters", "latest-adapter-checks"), ("kconfig", "latest-kconfig")]:
    checked = Path((area / pointer).read_text().strip())
    report = json.loads((checked / "report.json").read_text())
    assert report["passed"]
    copy(checked / "report.json", pre / (label + "-report.json"))
    for name in ["stdout", "stderr", "fixture.sh", "candidate.defconfig", "command.json"]:
        if (checked / name).is_file():
            copy(checked / name, pre / label / name)

for path in sorted((stage / "native").iterdir()):
    copy(path, native / "native" / path.name)
for name in ["analysis.json", "manifest.json", "user-confirmation.json", "audit-executed.py"]:
    copy(stage / name, native / name)
for label in ["native-preflight", "idle-audit", "active-audit", "stopped-audit", "infrastructure-before",
              "infrastructure-active", "infrastructure-after", "prerequisites-after", "cleanup", "final-health"]:
    for suffix in ["stdout", "stderr", "exit"]:
        path = stage / (label + "." + suffix)
        if path.is_file():
            copy(path, native / path.name)

sources = [*sorted((repo / "port/device/rk-r35s-p0/boot").iterdir()),
           *sorted((repo / "port/buildroot/package/muos-r35s-boot").iterdir()),
           repo / "port/buildroot/Config.in", repo / "port/device/rk-r35s-p0/phase4-boot.fragment",
           *[repo / "port/scripts" / n for n in ["check-phase4-boot-order.py", "check-phase4-boot-adapters.py",
              "prepare-phase4-boot-coordinator.py", "audit-phase4-boot-coordinator.py", Path(__file__).name]]]
for path in sources:
    copy(path, pre / "port-source" / path.relative_to(repo / "port"))
for out in [pre, native]:
    for name in ["phase4-boot-coordinator.md", "phase4-resume-checkpoint.md", "roadmap.md"]:
        copy(repo / "docs/analysis" / name, out / "docs" / name)
    (out / "STATE.txt").write_text(
        "C12 opt-in adapters and inactive inittab template.20 ordering +33 adapter/controller fixtures.\n"
        "Native check-stop: idle0, active1 with C11 still ready0, after manual stop0.\n"
        "Visual menu confirmed; profile21/original21 hashes and runtime/hardware restored.\n"
        "C07 infrastructure PID/starttime unchanged; rootRO/FAT unmounted/taint0; RAM removed.\n"
        "BOOT_SEQUENCE26; SSH 192.168.15.13:2222 pinned to original public host key.\n"
        "No C12 boot/shutdown, power syscall, active inittab, persistent install or settings persistence tested.\n"
        "C11 cache/restore transaction ran; no whole-filesystem byte-identity claim.\n"
        "Post-run audit source only clarifies metadata; exact executed audit is frozen separately.\n"
        "No live root clone, saved seed, Wi-Fi credentials or private SSH key collected. No offline fsck.\n"
    )
    files = sorted(p for p in out.rglob("*") if p.is_file())
    (out / "SHA256SUMS").write_text("".join(sha(p) + "  " + str(p.relative_to(out)) + "\n" for p in files))
    for line in (out / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split("  ", 1)
        assert sha(out / name) == digest, name
    print("Frozen and hash-verified:", out)
