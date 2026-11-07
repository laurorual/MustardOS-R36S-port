#!/usr/bin/env python3
"""Bounded diagnostics with a transient systemd restoration timer."""
import fcntl
import json
import os
from pathlib import Path
import selectors
import signal
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "session-state.json"
SERVICES = ["emulationstation.service", "ogage.service", "fn-menu-watcher.service"]


def systemctl(*args, check=True):
    return subprocess.run(["systemctl", *args], check=check, capture_output=True, text=True)


def restore():
    if not STATE.exists():
        return
    state = json.loads(STATE.read_text())
    if (ROOT / "fb-before.bin").exists():
        try:
            with open("/dev/fb0", "r+b", buffering=0) as fb:
                image = (ROOT / "fb-before.bin").read_bytes()
                offset = 0
                while offset < len(image):
                    written = os.pwrite(fb.fileno(), image[offset:], offset)
                    if written <= 0:
                        raise OSError("Framebuffer restore made no progress")
                    offset += written
                fcntl.ioctl(fb, 0x4606, bytes.fromhex(state["fb_var"]))
        except OSError as error:
            print("framebuffer_restore_warning=" + str(error), flush=True)
    for service in state["active_services"]:
        systemctl("start", service)
    print("services_restored=" + ",".join(state["active_services"]), flush=True)


def collect_input(seconds):
    event = struct.Struct("@llHHi")
    selector = selectors.DefaultSelector()
    sources = []
    for path in sorted(Path("/sys/class/input").glob("event*/device/name")):
        name = path.read_text().strip()
        if name not in ["GO-Super Gamepad", "odroidgo3-keys", "rk8xx_pwrkey"]:
            continue
        node = "/dev/input/" + path.parents[1].name
        descriptor = os.open(node, os.O_RDONLY | os.O_NONBLOCK)
        selector.register(descriptor, selectors.EVENT_READ, {"name": name, "node": node})
        sources.append(descriptor)
    started = time.monotonic()
    print("INPUT_CAPTURE_READY", flush=True)
    try:
        with (ROOT / "input-events.jsonl").open("w") as output:
            while time.monotonic() - started < seconds:
                for key, _ in selector.select(timeout=0.2):
                    data = os.read(key.fd, event.size * 128)
                    if len(data) % event.size:
                        raise RuntimeError("Unexpected input_event size")
                    for offset in range(0, len(data), event.size):
                        sec, usec, kind, code, value = event.unpack_from(data, offset)
                        if kind not in (1, 3) and not (kind == 0 and code == 3):
                            continue
                        entry = {**key.data, "elapsed": round(time.monotonic()-started, 4), "type": kind, "code": code, "value": value}
                        output.write(json.dumps(entry) + "\n")
                    output.flush()
    finally:
        selector.close()
        for descriptor in sources:
            os.close(descriptor)
    print("INPUT_CAPTURE_FINISHED", flush=True)


def stop_requested(sig, frame):
    raise SystemExit(128 + sig)


def main():
    if os.geteuid() != 0 or ROOT.parent != Path("/tmp") or not ROOT.name.startswith("muos-r35s-phase2."):
        raise SystemExit("Run through sudo in the temporary test directory")
    if len(sys.argv) == 2 and sys.argv[1] == "--restore":
        restore()
        return
    if len(sys.argv) == 2 and sys.argv[1] == "--capture-input":
        collect_input(120)
        return
    if len(sys.argv) != 2 or sys.argv[1] not in ["framebuffer", "sdl", "input", "normalized"]:
        raise SystemExit("Expected framebuffer, sdl, input or normalized")
    active = [service for service in SERVICES if systemctl("is-active", service, check=False).returncode == 0]
    with open("/dev/fb0", "rb", buffering=0) as fb:
        var, fix = bytearray(160), bytearray(80)
        fcntl.ioctl(fb, 0x4600, var)
        fcntl.ioctl(fb, 0x4602, fix)
        size = struct.unpack_from("I", fix, 24)[0]
        if size < 640*480*2 or size > 16*1024*1024:
            raise SystemExit("Unexpected framebuffer size")
        image = os.pread(fb.fileno(), size, 0)
        if len(image) != size:
            raise SystemExit("Cannot save the framebuffer")
        (ROOT / "fb-before.bin").write_bytes(image)
    STATE.write_text(json.dumps({"active_services": active, "fb_var": var.hex(), "mount_namespace": os.readlink("/proc/self/ns/mnt")}))
    unit = "muos-r35s-restore-" + ROOT.name.rsplit(".", 1)[-1].lower() + "-" + str(os.getpid())
    subprocess.run(["systemd-run", "--quiet", "--unit=" + unit, "--on-active=180s", "/usr/bin/python3", str(Path(__file__).resolve()), "--restore"], check=True)
    for sig in [signal.SIGHUP, signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, stop_requested)
    child = None
    try:
        if active:
            systemctl("stop", *active)
        if sys.argv[1] == "framebuffer":
            print("FRAMEBUFFER_TEST_READY", flush=True)
            child = subprocess.Popen(["timeout", "--signal=TERM", "45", str(ROOT / "musplash"), "-i", str(ROOT / "panel-test.png"), "-f", "/dev/fb0", "-v", "-w", "-l", str(ROOT / "musplash-trace.txt")], start_new_session=True)
            code = child.wait(timeout=55)
            print("MUSPLASH_SESSION_EXIT_STATUS=" + str(code), flush=True)
            if code not in (0, 124):
                raise SystemExit(code)
        elif sys.argv[1] == "sdl":
            environment = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "HOME": str(ROOT), "XDG_RUNTIME_DIR": "/run/user/1000", "SDL_VIDEODRIVER": "KMSDRM", "SDL_VIDEO_EGL_DRIVER": "libEGL.so", "SDL_VIDEO_GL_DRIVER": "libGLESv2.so"}
            print("SDL_TEST_READY", flush=True)
            child = subprocess.Popen(["/usr/sbin/runuser", "-u", "ark", "--", "env", "-i", *[k+"="+v for k,v in environment.items()], str(ROOT / "sdl-video-probe"), "30"], start_new_session=True)
            code = child.wait(timeout=55)
            print("SDL_SESSION_EXIT_STATUS=" + str(code), flush=True)
            if code:
                raise SystemExit(code)
        elif sys.argv[1] == "normalized":
            child = subprocess.Popen(["unshare", "--mount", "--fork", "/usr/bin/python3", str(ROOT / "phase2-input-namespace.py")], start_new_session=True)
            code = child.wait(timeout=115)
            print("NORMALIZED_SESSION_EXIT_STATUS=" + str(code), flush=True)
            if code:
                raise SystemExit(code)
        else:
            child = subprocess.Popen(["systemd-inhibit", "--what=handle-power-key:handle-suspend-key", "--mode=block", "--who=muOS phase 2", "--why=Temporary input capture", "/usr/bin/python3", str(Path(__file__).resolve()), "--capture-input"], start_new_session=True)
            code = child.wait(timeout=140)
            if code:
                raise SystemExit(code)
    finally:
        if child is not None and child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
        restore()
        systemctl("stop", unit + ".timer", check=False)
        systemctl("reset-failed", unit + ".service", check=False)


if __name__ == "__main__":
    main()
