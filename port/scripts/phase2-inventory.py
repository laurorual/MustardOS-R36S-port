#!/usr/bin/env python3
"""Read graphics/input metadata without initialising SDL or grabbing input."""

import fcntl
import glob
import json
import os
from pathlib import Path
import struct
import subprocess
import sys


def read(path):
    try:
        return Path(path).read_text(errors="replace").strip()
    except OSError as error:
        return {"error": str(error)}


report = {"sysfs": {}, "devices": {}, "processes": []}
for pattern, fields in [
    ("/sys/class/graphics/fb[0-9]*", ["name", "virtual_size", "bits_per_pixel", "stride", "mode", "modes", "blank"]),
    ("/sys/class/backlight/*", ["brightness", "actual_brightness", "max_brightness", "bl_power"]),
    ("/sys/class/drm/card*-*", ["status", "enabled", "modes"]),
    ("/sys/class/input/event*/device", ["name", "phys", "capabilities/ev", "capabilities/key", "capabilities/abs"]),
]:
    for path in sorted(glob.glob(pattern)):
        report["sysfs"][path] = {name: read(f"{path}/{name}") for name in fields}

try:
    with open("/dev/fb0", "rb", buffering=0) as fb:
        var = bytearray(160)
        fix = bytearray(80)
        fcntl.ioctl(fb, 0x4600, var)  # FBIOGET_VSCREENINFO
        fcntl.ioctl(fb, 0x4602, fix)  # FBIOGET_FSCREENINFO, native AArch64 layout
        values = struct.unpack("40I", var)
        report["fb"] = {
            "id": bytes(fix[:16]).split(b"\0")[0].decode(errors="replace"),
            "smem_len": struct.unpack_from("I", fix, 24)[0],
            "line_length": struct.unpack_from("I", fix, 48)[0],
            "xres": values[0], "yres": values[1],
            "virtual": values[2:4], "offset": values[4:6], "bpp": values[6],
            "red": values[8:11], "green": values[11:14], "blue": values[14:17],
            "pixclock_ps": values[25], "margins_l_r_u_d": values[26:30],
            "sync_lengths": values[30:32], "rotate": values[34],
        }
except OSError as error:
    report["fb"] = {"error": str(error)}

for path in sorted(glob.glob("/dev/input/event*")):
    axes = {}
    try:
        with open(path, "rb", buffering=0) as source:
            capabilities = bytearray(8)
            fcntl.ioctl(source, 0x80084523, capabilities)  # EVIOCGBIT(EV_ABS, 8)
            supported = int.from_bytes(capabilities, sys.byteorder)
            for axis in [0, 1, 3, 4, 16, 17]:
                if not supported & (1 << axis):
                    continue
                try:
                    data = bytearray(24)
                    fcntl.ioctl(source, 0x80184540 + axis, data)  # EVIOCGABS(axis)
                    axes[str(axis)] = dict(zip(["value", "min", "max", "fuzz", "flat", "resolution"], struct.unpack("6i", data)))
                except OSError:
                    pass
    except OSError as error:
        axes["error"] = str(error)
    report["devices"][path] = axes

sdl_code = r'''
import ctypes, json
from pathlib import Path
sdl = ctypes.CDLL("libSDL2-2.0.so.0")
sdl.SDL_GetVideoDriver.restype = ctypes.c_char_p
sdl.SDL_GetRevision.restype = ctypes.c_char_p
version = (ctypes.c_ubyte * 3)()
sdl.SDL_GetVersion(version)
result = {"version": list(version), "revision": sdl.SDL_GetRevision().decode(),
    "video_drivers": [sdl.SDL_GetVideoDriver(i).decode() for i in range(sdl.SDL_GetNumVideoDrivers())],
    "loaded_paths": sorted({line.split()[-1] for line in Path("/proc/self/maps").read_text().splitlines() if "libSDL2" in line})}
print("SDL_JSON=" + json.dumps(result), flush=True)
'''
child = subprocess.run([sys.executable, "-c", sdl_code], capture_output=True, text=True)
lines = child.stdout.splitlines()
payload = next((line[9:] for line in lines if line.startswith("SDL_JSON=")), None)
report["sdl"] = json.loads(payload) if payload else {"error": child.stderr, "status": child.returncode}
report["sdl"]["native_diagnostics"] = [line for line in lines if not line.startswith("SDL_JSON=")] + child.stderr.splitlines()

for proc in Path("/proc").iterdir():
    if not proc.name.isdigit():
        continue
    try:
        name = (proc / "comm").read_text(errors="replace").strip()
        if not any(s in name for s in ["emulation", "ogage", "gptokeyb", "oga_control", "evtest"]):
            continue
        environment = (proc / "environ").read_bytes().split(b"\0")
        chosen = [entry.decode(errors="replace") for entry in environment if entry.startswith((b"SDL_VIDEO", b"SDL_RENDER", b"XDG_RUNTIME_DIR=", b"DISPLAY=", b"WAYLAND_DISPLAY="))]
        devices = []
        for fd in (proc / "fd").iterdir():
            try:
                target = os.readlink(fd)
                if target.startswith(("/dev/dri/", "/dev/fb", "/dev/mali", "/dev/input/")):
                    devices.append(target)
            except OSError:
                pass
        report["processes"].append({"pid": int(proc.name), "name": name, "graphics_env": chosen, "devices": sorted(set(devices))})
    except OSError:
        continue

result = subprocess.run(["/sbin/ldconfig", "-p"], capture_output=True, text=True, check=True)
report["graphics_libraries"] = [line.strip() for line in result.stdout.splitlines() if any(s in line for s in ["libSDL2-2.0", "libEGL.so", "libGLESv2.so", "libgbm.so", "libmali", "libpng16"])]
print(json.dumps(report, indent=2))
