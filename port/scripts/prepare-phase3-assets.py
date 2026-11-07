#!/usr/bin/env python3
"""Copy selected pinned upstream blobs; fetch missing blobs only into build/."""
import json
import os
from pathlib import Path
import subprocess

repo = Path(__file__).resolve().parents[2]
work = repo / "build/phase3"
upstream = repo / "refs/muos/internal"
revision = "550cc58f9cd3449a17f53ca55efcdc6c473b5a89"
cache = work / "deps/internal.git"
env = dict(os.environ, GIT_NO_LAZY_FETCH="1")

def git(*args, cwd=upstream, **kw):
    return subprocess.check_output(["git", *args], cwd=cwd, env=env, **kw)

if not cache.exists():
    subprocess.run(["git", "init", "--bare", str(cache)], check=True, stdout=subprocess.DEVNULL)
    objects = git("rev-parse", "--git-path", "objects").decode().strip()
    (cache / "objects/info/alternates").write_text(str((upstream / objects).resolve()) + "\n")
    subprocess.run(["git", "-C", str(cache), "remote", "add", "origin", git("remote", "get-url", "origin").decode().strip()], check=True)

entries = []
for entry in git("ls-tree", "-rz", revision).split(b"\0"):
    if not entry: continue
    meta, raw_path = entry.split(b"\t", 1)
    mode, kind, oid = meta.decode().split()
    path = raw_path.decode()
    if kind != "blob": continue
    chosen = (path.startswith("device/common/config/")
              or path in ["LICENSE", "share/font/internal/Noto Sans.ttf", "share/font/internal/Noto-Sans-OFL.txt",
                          "share/language/Portuguese (BR).json", "share/language/English.json", "share/theme/MustardOS/version.txt"]
              or path.startswith(("share/theme/MustardOS/glyph/", "share/theme/MustardOS/scheme/",
                                   "share/theme/MustardOS/640x480/scheme/", "share/theme/MustardOS/sound/")))
    if chosen: entries.append((path, oid))

ids = sorted({oid for _, oid in entries})
checked = subprocess.run(["git", "-C", str(cache), "cat-file", "--batch-check=%(objectname) %(objecttype)"],
                         input="\n".join(ids)+"\n", text=True, capture_output=True, env=env, check=True)
missing = [line.split()[0] for line in checked.stdout.splitlines() if line.endswith(" missing")]
if missing:
    subprocess.run(["git", "-C", str(cache), "fetch", "origin", "--no-tags", "--no-write-fetch-head", "--stdin"],
                   input="\n".join(missing)+"\n", text=True, check=True)

stage = work / "staging/opt/muos"
stage.mkdir(parents=True, exist_ok=True)
for path, oid in entries:
    destination = stage / ("device/config/" + path.removeprefix("device/common/config/") if path.startswith("device/common/config/") else path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(git("cat-file", "blob", oid, cwd=cache))

config = json.loads((repo / "port/device/rk-r35s-p0/staging-config.json").read_text())
for namespace, prefix in [("device", "device/config"), ("global", "config")]:
    for name, value in config[namespace].items():
        destination = stage / prefix / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(value + "\n")
for directory in ["kiosk", "config/system", "share/info/gamecontrollerdb"]:
    (stage / directory).mkdir(parents=True, exist_ok=True)
for layout in ["modern", "retro"]:
    (stage / f"share/info/gamecontrollerdb/{layout}.txt").write_text("# Board mapping is generated from the actual virtual SDL joystick at runtime.\n")
(work / "asset-manifest.json").write_text(json.dumps({"revision": revision, "blobs": dict(entries), "note": "Schemes, glyphs, Noto font, language and sounds only; no scripts, videos or emulators."}, indent=2)+"\n")
print(f"Prepared {len(entries)} pinned blobs in {stage}")
