#!/usr/bin/env python3
"""Run muinput in private /dev and /run mounts, retaining native evdev grabs."""
import fcntl
import json
import os
from pathlib import Path
import selectors
import signal
import stat
import struct
import subprocess
import time

root = Path(__file__).resolve().parent
if os.geteuid() != 0 or root.parent != Path("/tmp") or not root.name.startswith("muos-r35s-phase2."):
    raise SystemExit("Expected root inside the temporary phase 2 directory")
state = json.loads((root / "session-state.json").read_text())
if os.readlink("/proc/self/ns/mnt") == state["mount_namespace"]:
    raise SystemExit("Refusing to mount over /dev or /run outside a private mount namespace")
duration = int(os.environ.get("PHASE2_CAPTURE_SECONDS", "90"))
if not 1 <= duration <= 90:
    raise SystemExit("Capture duration must be between 1 and 90 seconds")
nodes = [Path("/dev/null"), Path("/dev/uinput"), *Path("/dev/input").glob("event*"), *Path("/dev/input").glob("js*")]
devices = [(str(p), os.stat(p).st_rdev) for p in nodes]
subprocess.run(["mount", "--make-rprivate", "/"], check=True)
subprocess.run(["mount", "-t", "tmpfs", "-o", "mode=0755,nosuid", "tmpfs", "/dev"], check=True)
subprocess.run(["mount", "-t", "tmpfs", "-o", "mode=0755,nosuid,nodev", "tmpfs", "/run"], check=True)
Path("/dev/input").mkdir()
for path, device in devices:
    os.mknod(path, stat.S_IFCHR | 0o600, device)
log = (root / "muinput-normalized.log").open("w")
child = subprocess.Popen([str(root / "muinput-r35s"), "--device", "rk-r35s-p0", "--foreground", "--verbose", "--rumble-strength", "0"], stdout=log, stderr=log)
selector = selectors.DefaultSelector()


def interrupted(sig, frame):
    raise SystemExit(128 + sig)


for sig in [signal.SIGHUP, signal.SIGINT, signal.SIGTERM]:
    signal.signal(sig, interrupted)
try:
    deadline = time.monotonic() + 10
    node = None
    while time.monotonic() < deadline:
        if child.poll() is not None:
            raise RuntimeError("muinput exited before source isolation")
        for name in Path("/sys/class/input").glob("event*/device/name"):
            if name.read_text().strip() != "muOS-Keys":
                continue
            identity = name.parent / "id"
            if (identity / "product").read_text().strip() != "3504":
                continue
            major, minor = map(int, (name.parents[1] / "dev").read_text().split(":"))
            node = Path("/dev/input") / name.parents[1].name
            if not node.exists():
                os.mknod(node, stat.S_IFCHR | 0o600, os.makedev(major, minor))
            break
        if node and Path("/dev/muinput/rk-r35s-p0-source").exists():
            break
        time.sleep(0.05)
    if not node or not Path("/dev/muinput/rk-r35s-p0-source").exists():
        raise RuntimeError("No isolated source and matching virtual controller")
    descriptor = os.open(node, os.O_RDONLY | os.O_NONBLOCK)
    selector.register(descriptor, selectors.EVENT_READ)
    device_id = bytearray(8)
    fcntl.ioctl(descriptor, 0x80084502, device_id)
    print("virtual_id=" + json.dumps(struct.unpack("4H", device_id)), flush=True)
    print("NORMALIZED_CAPTURE_READY", flush=True)
    event = struct.Struct("@llHHi")
    started = time.monotonic()
    with (root / "normalized-events.jsonl").open("w") as output:
        while time.monotonic() - started < duration:
            if child.poll() is not None:
                raise RuntimeError("muinput exited during capture")
            for key, _ in selector.select(timeout=0.2):
                data = os.read(key.fd, event.size * 128)
                if len(data) % event.size:
                    raise RuntimeError("Unexpected input_event size")
                for offset in range(0, len(data), event.size):
                    _, _, kind, code, value = event.unpack_from(data, offset)
                    if kind in (1, 3) or (kind == 0 and code == 3):
                        output.write(json.dumps({"elapsed": round(time.monotonic()-started, 4), "type": kind, "code": code, "value": value}) + "\n")
                output.flush()
    print("NORMALIZED_CAPTURE_FINISHED", flush=True)
finally:
    selector.close()
    child.terminate()
    try:
        code = child.wait(timeout=5)
    except subprocess.TimeoutExpired:
        child.kill()
        code = child.wait()
    log.close()
    print("muinput_exit_status=" + str(code), flush=True)
