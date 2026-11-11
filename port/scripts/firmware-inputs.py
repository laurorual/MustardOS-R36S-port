#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Pinned prebuilt inputs of the M3a firmware (port/packaging/firmware-inputs.json).

  firmware-inputs.py store    MANIFEST STORE          copy (reflink) each origin into STORE/<sha256>
  firmware-inputs.py verify   MANIFEST STORE          every stored blob present and matching
  firmware-inputs.py install  MANIFEST STORE TARGET   Buildroot post-build: install into TARGET
  firmware-inputs.py generate INVENTORY TARGET OVERLAY HOSTMATCH PULLED MANIFEST REPORT
      write MANIFEST from a live p2 inventory (device `find` + sha256) and a
      fresh Buildroot TARGET: every live path is identical, overlay, rebuilt,
      an input (origin: HOSTMATCH sha256 -> host file, else PULLED/<path>
      copied from the device) or dropped (DROP below, with its reason).

Manifest entries: {"path", "type": file|link|dir, "mode", "sha256", "origin"}
for files, {"target"} for links; "remove" lists Buildroot paths the live
system doesn't carry. Origins are relative to the repo and only read by
`store`; the build reads the store, so old build outputs can be retired.
"""
import hashlib, json, os, shutil, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def load(manifest):
    with open(manifest) as f:
        return json.load(f)


def files(m):
    return [e for e in m['entries'] if e['type'] == 'file']


def store(manifest, dest):
    os.makedirs(dest, exist_ok=True)
    added = 0
    for e in files(load(manifest)):
        blob = os.path.join(dest, e['sha256'])
        if os.path.exists(blob):
            continue
        src = os.path.join(REPO, e['origin'])
        tmp = blob + '.tmp'
        subprocess.run(['cp', '--reflink=auto', src, tmp], check=True)
        if sha(tmp) != e['sha256']:
            os.unlink(tmp)
            sys.exit(f'origin changed: {e["origin"]} for {e["path"]}')
        os.chmod(tmp, 0o444)
        os.rename(tmp, blob)
        added += 1
    print(f'store: {added} added, {len(os.listdir(dest))} blobs')


def verify(manifest, dest):
    bad = [e['path'] for e in files(load(manifest))
           if not os.path.exists(os.path.join(dest, e['sha256']))
           or sha(os.path.join(dest, e['sha256'])) != e['sha256']]
    if bad:
        sys.exit('missing or corrupt inputs: ' + ', '.join(bad[:10]))
    print(f'verify: {len(files(load(manifest)))} inputs OK')


def inside(target, path):
    p = os.path.normpath(target + '/' + path)
    if not p.startswith(os.path.normpath(target) + '/'):
        sys.exit(f'path escapes target: {path}')
    return p


def install(manifest, dest, target):
    m = load(manifest)
    for path in m.get('remove', []):
        p = inside(target, path)
        if os.path.isdir(p) and not os.path.islink(p):
            shutil.rmtree(p)
        elif os.path.lexists(p):
            os.unlink(p)
    for e in sorted(m['entries'], key=lambda e: e['path']):
        p = inside(target, e['path'])
        if e['type'] == 'dir':
            os.makedirs(p, exist_ok=True)
            os.chmod(p, int(e['mode'], 8))
            continue
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if os.path.lexists(p) and (os.path.islink(p) or not os.path.isdir(p)):
            os.unlink(p)
        if e['type'] == 'link':
            os.symlink(e['target'], p)
        else:
            blob = os.path.join(dest, e['sha256'])
            shutil.copyfile(blob, p)
            if sha(p) != e['sha256']:
                sys.exit(f'bad copy {e["path"]}')
            os.chmod(p, int(e['mode'], 8))
    print(f'install: {len(m["entries"])} entries, {len(m.get("remove", []))} removed')


def read_inventory(path):
    """device inventory: type|mode|uid|gid|size|sha256 or ->target|path"""
    inv = {}
    with open(path) as f:
        for line in f:
            t, mode, uid, gid, size, h, p = line.rstrip('\n').split('|', 6)
            kind = {'directory': 'dir', 'symbolic link': 'link'}.get(t, 'file' if 'regular' in t else t)
            inv[p] = {'type': kind, 'mode': mode, 'uid': uid, 'gid': gid, 'size': int(size),
                      'sha256': h if kind == 'file' else None,
                      'target': h[2:] if kind == 'link' else None}
    return inv


def tree(root):
    """the same view of a host directory (a Buildroot target or the overlay)"""
    out = {}
    for d, dirs, names in os.walk(root):
        for n in dirs + names:
            p = os.path.join(d, n)
            rel = '/' + os.path.relpath(p, root)
            if os.path.islink(p):
                out[rel] = {'type': 'link', 'target': os.readlink(p)}
            elif os.path.isdir(p):
                out[rel] = {'type': 'dir', 'mode': '%o' % (os.stat(p).st_mode & 0o7777)}
            else:
                out[rel] = {'type': 'file', 'mode': '%o' % (os.stat(p).st_mode & 0o7777),
                            'sha256': sha(p), 'size': os.path.getsize(p)}
    return out


# Live p2 paths that the firmware deliberately doesn't carry.
DROP = [
    ('/var/lib/muos-m1-backup', 'install-rootfs.sh originals of the in-place M1/M2 updates'),
    ('/usr/libexec/muos-session', 'legacy C21 session package (S91 import is guarded)'),
    ('/usr/share/muos-save-store', 'legacy MUOSSAV1 save store'),
    ('/usr/share/licenses/muos-save-store', 'legacy MUOSSAV1 save store'),
    ('/usr/share/licenses/muos-r35s-session', 'legacy C21 session package'),
    ('/usr/libexec/muos-audio-functions', 'C-step audio probe library'),
    ('/usr/libexec/muos-audio-probe', 'C-step audio probe'),
    ('/usr/libexec/muos-core-lifecycle', 'C-step lifecycle probe'),
    ('/usr/libexec/muos-drm-mode-probe', 'C-step DRM probe'),
    ('/usr/libexec/muos-egl-context', 'C-step EGL probe'),
    ('/usr/libexec/muos-root-writers', 'C-step root writer audit'),
    ('/usr/libexec/muos-sdl-video-probe', 'C-step SDL probe'),
    ('/etc/inittab.fallback', 'trial-boot artifact, written when a trial is armed'),
    ('/var/lib/muos-seedrng', 'per-card seed, created at first boot (M1)'),
    ('/var/lib/muos-network', 'device identity: added by the image stage from the base p2'),
    ('/etc/muos-network-authorized_key', 'device identity: added by the image stage'),
    ('/run', 'runtime tmpfs mount point content'),
    ('/crond.reboot', 'BusyBox crond runtime marker'),
]

# Rebuilt paths where the live (tuned, T3-confirmed) content wins over the
# package default: the muOS config/device trees and service defaults.
PIN_LIVE = ('/opt/muos/', '/etc/default/')

# Buildroot output the live system doesn't carry, removed post-build.
REMOVE = {
    '/etc/init.d/S50dropbear': 'second SSH server on :22; S41muos-network runs dropbear on :2222',
    '/etc/dropbear': 'stock dropbear key dir (S50dropbear)',
    '/etc/network/if-up.d/wpasupplicant': 'ifupdown hook; S41muos-network drives wpa_supplicant',
    '/etc/network/if-down.d/wpasupplicant': 'ifupdown hook',
    '/etc/wpa_supplicant.conf': 'stock config; network.conf is used',
    '/etc/udev/hwdb.d': 'hwdb sources; the compiled hwdb.bin is kept',
    '/lib/udev/usb_modeswitch': 'udev dispatcher not on the live system (Wi-Fi bring-up is S41)',
    '/usr/sbin/usb_modeswitch_dispatcher': 'udev dispatcher not on the live system',
    '/etc/usb_modeswitch.conf': 'dispatcher config',
    '/var/lib/usb_modeswitch': 'dispatcher state',
    '/usr/lib/pipewire-0.3/libpipewire-module-raop-sink.so': 'AirPlay sink, not on the live system',
    '/usr/lib/spa-0.2/ffmpeg': 'SPA ffmpeg plugin, not on the live system',
}


def dropped(path):
    for prefix, why in DROP:
        if path == prefix or path.startswith(prefix + '/'):
            return why
    return None


def generate(live, target, overlay, hostmatch, pulled, manifest, report):
    entries, notes = [], {}
    def note(kind, path, extra=''):
        notes.setdefault(kind, []).append(path + (f'  {extra}' if extra else ''))
    for path in sorted(live):
        e = live[path]
        why = dropped(path)
        if why:
            note('dropped: ' + why, path)
            continue
        if path in overlay:
            o = overlay[path]
            if o['type'] == 'file' and e['type'] == 'file' and o['sha256'] != e['sha256']:
                note('overlay differs from live (live not updated?)', path)
            elif o['type'] == 'file' and o['mode'] != e['mode'] and e['type'] == 'file':
                note('overlay mode differs', path, f'{e["mode"]} -> {o["mode"]}')
            else:
                note('overlay', path)
            continue
        t = target.get(path)
        if t and t['type'] == e['type']:
            if e['type'] == 'dir' or (e['type'] == 'link' and t['target'] == e['target']) \
                    or (e['type'] == 'file' and t['sha256'] == e['sha256']):
                note('identical' if e['type'] != 'file' or t['mode'] == e['mode'] else 'identical, mode differs', path)
                continue
            if e['type'] == 'file' and not path.startswith(PIN_LIVE):
                note('rebuilt (content differs)', path)
                continue
        if t and t['type'] != e['type']:
            note('type differs (target wins)', path, f'{e["type"]} -> {t["type"]}')
            continue
        if e['type'] == 'dir':
            entries.append({'path': path, 'type': 'dir', 'mode': e['mode']})
            note('input dir', path)
        elif e['type'] == 'link':
            entries.append({'path': path, 'type': 'link', 'target': e['target']})
            note('input link', path)
        elif e['type'] == 'file':
            origin = hostmatch.get(e['sha256'])
            if not origin and os.path.isfile(pulled + path) and sha(pulled + path) == e['sha256']:
                origin = os.path.relpath(pulled + path, REPO)
            if not origin:
                note('UNRESOLVED (no origin)', path)
                continue
            entries.append({'path': path, 'type': 'file', 'mode': e['mode'], 'sha256': e['sha256'],
                            'origin': os.path.relpath(os.path.join(REPO, origin), REPO)})
            note('input file (live wins over the package default)' if t else 'input file', path, origin)
        else:
            note('UNRESOLVED (special file)', path, e['type'])
    for path in sorted(set(target) - set(live)):
        if path in overlay:
            continue
        why = next((w for r, w in REMOVE.items() if path == r or path.startswith(r + '/')), None)
        if why:
            note('removed: ' + why, path)
        else:
            note('new in the build (not on live p2)', path)
    with open(manifest, 'w') as f:
        json.dump({'note': 'M3a prebuilt inputs, generated by firmware-inputs.py generate from the '
                   'live M2.1 p2 inventory; origins are host build outputs (see firmware-inputs.py).',
                   'entries': entries, 'remove': sorted(REMOVE)}, f, indent=1)
        f.write('\n')
    with open(report, 'w') as f:
        for kind in sorted(notes):
            f.write(f'## {kind}: {len(notes[kind])}\n')
            f.writelines(p + '\n' for p in notes[kind])
    for kind in sorted(notes):
        print(f'{len(notes[kind]):5d}  {kind}')


if __name__ == '__main__':
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == 'store':
        store(*args)
    elif cmd == 'verify':
        verify(*args)
    elif cmd == 'install':
        install(*args)
    elif cmd == 'generate':
        generate(read_inventory(args[0]), tree(args[1]), tree(args[2]), json.load(open(args[3])), *args[4:])
    else:
        sys.exit(__doc__)
