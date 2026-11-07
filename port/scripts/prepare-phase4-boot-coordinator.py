#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Exercise C12 installation in isolation and stage a RAM-only native audit.

Installs an inactive inittab template; never rewrites the live candidate or the
SDK configuration. Reuses byte-verified C11 support tools and approved profile.
"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tarfile
import tempfile

repo = Path(__file__).resolve().parents[2]
work = repo / "build/phase4"
area = work / "boot-order"
area.mkdir(exist_ok=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
reports = {}
for label, pointer in [("order", "latest-checks"), ("adapters", "latest-adapter-checks"), ("power", "latest-power-checks")]:
    checked = Path((area / pointer).read_text().strip())
    report = json.loads((checked / "report.json").read_text())
    assert report["passed"]
    for name, digest in report["sources"].items():
        assert sha(repo / name) == digest, (label, name, "checks are stale")
    reports[label] = report
baseline = work / "network-tools/baseline.config"
assert (work / "graphics-config/output/.config").read_bytes() == baseline.read_bytes()
session_stage = Path((work / "runtime-session/latest-service").read_text().strip())
session_manifest = json.loads((session_stage / "manifest.json").read_text())
assert session_manifest["host_passed"] and not session_manifest["service_default_enabled"]
session = session_stage / "package"
for line in (session / "SHA256SUMS").read_text().splitlines():
    digest, name = line.split("  ", 1)
    assert sha(session / name) == digest, name
for name, digest in session_manifest["source_sha256"].items():
    assert sha(repo / name) == digest, ("C11 changed", name)

stage = Path(tempfile.mkdtemp(prefix="coordinator.", dir=area))
source = stage / "source"
shutil.copytree(repo / "port/device/rk-r35s-p0/boot", source)
shutil.copyfile(repo / "port/device/rk-r35s-p0/linux-diagnostic/card-guard.sh", source / "card-guard.sh")
shutil.copyfile(repo / "port/LICENSE", source / "LICENSE")
target = stage / "recipe-target"
(target / "usr/libexec/muos-session/bin").mkdir(parents=True)
shutil.copyfile(session / "bin/muos-run-bounded", target / "usr/libexec/muos-session/bin/muos-run-bounded")
rel = lambda p: "/work/" + str(p.relative_to(work))
harness = stage / "recipe.mk"
harness.write_text(
    f"TARGET_DIR := {rel(target)}\nINSTALL := install\ngeneric-package =\n"
    "include /port/buildroot/package/muos-r35s-boot/muos-r35s-boot.mk\n"
    f"{rel(source / '.installed')}:\n\t$(MUOS_R35S_BOOT_INSTALL_TARGET_CMDS)\n\ttouch $@\n"
)
container = [
    "podman", "run", "--rm", "--network=none", "--read-only", "--cap-drop=all",
    "--security-opt=no-new-privileges", "--userns=keep-id", "--tmpfs", "/tmp:rw,nosuid,nodev",
    "-v", f"{work}:/work:rw,z", "-v", f"{repo}/port:/port:ro,z",
    (work / "rootfs-container.iid").read_text().strip(),
]
result = subprocess.run(container + ["make", "-f", rel(harness)], capture_output=True, text=True, timeout=30)
(stage / "recipe.stdout").write_text(result.stdout)
(stage / "recipe.stderr").write_text(result.stderr)
assert result.returncode == 0, result.stderr
assert not (target / "etc/inittab").exists()
assert not (target / "etc/init.d").exists()
assert (target / "etc/default/muos-boot").read_text().splitlines()[1:3] == ["enabled=0", "allow_power=0"]
assert sha(target / "usr/libexec/muos-boot/bin/muos-run-bounded") == sha(session / "bin/muos-run-bounded")

# Check the inactive selection against the current host blueprint, without copying
# /var/lib, private keys, credentials, entropy or any live root filesystem.
layout = stage / "root-layout/etc"
layout.mkdir(parents=True)
root = work / "linux-diagnostic/network-recovery.zz7sq2ve/extracted"
shutil.copyfile(root / "etc/inittab", layout / "inittab.c07")
shutil.copyfile(target / "usr/share/muos-r35s-boot/inittab", layout / "inittab.c12")
active = [line for line in (layout / "inittab.c12").read_text().splitlines() if line and not line.startswith("#")]
assert sum("muos-boot/service.sh start" in line for line in active) == 1
assert sum("muos-boot/service.sh shutdown" in line for line in active) == 1
assert not any(name in "\n".join(active) for name in ["/rcS", "/rcK", "muos-c07-run", "S30", "S90", "S95", "S96", "S98", "S99"])
assert active.index("::shutdown:/usr/libexec/muos-boot/service.sh shutdown") < active.index("::shutdown:/bin/umount -a -r")

boot = target / "usr/libexec/muos-boot"
code = "set -eu\n"
for path in sorted(boot.glob("*.sh")):
    code += f"qemu-aarch64 -cpu cortex-a35 -L {rel(root)} {rel(root / 'bin/busybox')} sh -n {rel(path)}\n"
code += (
    f"readelf -h -l -d {rel(boot / 'bin/muos-run-bounded')} > {rel(stage / 'bounded-elf.txt')}\n"
    f"qemu-aarch64 -cpu cortex-a35 -L {rel(root)} -E LD_BIND_NOW=1 "
    f"{rel(root / 'lib/ld-linux-aarch64.so.1')} --inhibit-cache --library-path "
    f"{rel(root / 'lib')}:{rel(root / 'usr/lib')} --list {rel(boot / 'bin/muos-run-bounded')} "
    f"> {rel(stage / 'bounded-loader.txt')}\n"
)
result = subprocess.run(container + ["sh", "-c", code], capture_output=True, text=True, timeout=30)
(stage / "audit.stdout").write_text(result.stdout)
(stage / "audit.stderr").write_text(result.stderr)
assert result.returncode == 0, result.stderr
assert "Machine:                           AArch64" in (stage / "bounded-elf.txt").read_text()
assert (work / "graphics-config/output/.config").read_bytes() == baseline.read_bytes()

package = stage / "package"
shutil.copytree(boot, package / "boot")
shutil.copytree(session, package / "session")
shutil.copyfile(target / "etc/default/muos-boot", package / "muos-boot.default")
(package / "SHA256SUMS").write_text("".join(
    sha(p) + "  " + str(p.relative_to(package)) + "\n"
    for p in sorted(package.rglob("*")) if p.is_file()
))
with tarfile.open(stage / "deployment.tar", "w") as archive:
    for path in package.iterdir():
        archive.add(path, arcname=path.name)
inputs = [Path(__file__), repo / "port/buildroot/Config.in", repo / "port/device/rk-r35s-p0/phase4-boot.fragment",
          repo / "port/device/rk-r35s-p0/linux-diagnostic/card-guard.sh",
          *sorted((repo / "port/buildroot/package/muos-r35s-boot").iterdir()),
          *sorted((repo / "port/device/rk-r35s-p0/boot").iterdir())]
manifest = {
    "experiment": "MUOS-R35S-BOOT-P4-C12", "host_passed": True, "hardware_tested": False,
    "checks": reports, "recipe_install_passed": True, "inactive_inittab_selection_passed": True,
    "active_inittab_changed": False, "SDK_config_unchanged": True, "full_image_built": False,
    "service_default_enabled": False, "power_default_allowed": False, "persistence": "volatile",
    "session_source_stage": str(session_stage), "session_manifest_sha256": sha(session_stage / "manifest.json"),
    "session_package_byte_verified": True, "deployment_sha256": sha(stage / "deployment.tar"),
    "source_sha256": {str(p.relative_to(repo)): sha(p) for p in inputs},
}
(stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
pending = area / "source.pending"
pending.unlink(missing_ok=True)
pending.symlink_to(source.relative_to(area), target_is_directory=True)
pending.replace(area / "source")
(area / "latest-coordinator").write_text(str(stage) + "\n")
print("C12 recipe/ABI/inactive init selection prepared:", stage)
