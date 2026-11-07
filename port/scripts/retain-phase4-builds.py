#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Prune known historical replicas, preserving current dependency leaves.

Default is a dry run. No device, refs, SDK, private backup or dist deletion.
Review the private plan in build/cleanup before --apply.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, os, shutil, stat, subprocess, sys

REPO = Path(__file__).resolve().parents[2]
WORK = REPO / 'build/phase4'
POLICY = REPO / 'port/packaging/storage-retention.json'
SOURCE = Path(__file__).resolve()
TRACE = SOURCE.parents[1]/'diagnostics/phase4-storage-dependencies.py'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()


def signature(path):
    s = path.lstat()
    return [s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size, s.st_mtime_ns]


def replicas():
    patterns = [
        'linux-diagnostic/*/extracted', 'linux-diagnostic/*/rootfs.ext4',
        'foundation/staging.*/rootfs', 'frontend-session/staging.*/rootfs',
        'foundation/staging.*/core-staging.tar.gz', 'foundation/native-storage.*/core-staging.tar.gz',
        'frontend-session/staging.*/core-staging.tar.gz', 'init-services/staging.*/core-staging.tar.gz',
        'menu/staging.*/core-staging.tar.gz',
        'init-services/staging.*/rootfs', 'menu/staging.*/rootfs',
        'rootfs-candidate/*/target', 'rootfs-candidate/*/planned-target',
        'rootfs-candidate/*/images/rootfs.ext4',
        'uboot-sd/probe.*/source', 'uboot-sd/probe.*/output',
        'uboot-sd/probe.*/linux-image.*/*.img',
        'uboot-sd/probe.*/monitor-image.*/*.img',
        'uboot-sd/probe.*/linux-image.*/*.img.gz', 'uboot-sd/probe.*/linux-image.*/boot.fat',
        'rootfs-output/images/rootfs.ext2', 'graphics-config/output/images/rootfs.ext2',
        'card-image/image.*/*.img', 'card-image/image.*/*.img.gz',
        'card-image/image.*/boot.fat', 'card-image/image.*/partition-readback',
        'initial-image/provision.evbj4tey/candidate.ext4',
    ]
    for area in ['save-store-image', 'muxretro-image', 'provider-image', 'gambatte-image',
                 'muxretro-package', 'gambatte-package', 'save-store-package']:
        patterns.extend([area+'/*/target', area+'/*/images/rootfs.ext4'])
    # Composition roots and cloned sysroots were scaffolding for component
    # packaging, not current SDKs. Preserve any exact dependency leaves.
    for area in ['muxretro-provider','muxretro-package','gambatte-package']:
        patterns.extend([area+'/build.*/composition',area+'/build.*/staging'])
    for pattern in patterns:
        yield from WORK.glob(pattern)


def leaves(root):
    if root.is_symlink() or not root.is_dir():
        yield root
        return
    for base, dirs, files in os.walk(root, followlinks=False):
        for n in dirs[:]:
            p = Path(base)/n
            if p.is_symlink(): dirs.remove(n); yield p
        for n in files: yield Path(base)/n


def safe_parents(path, checked=None):
    assert '..' not in path.parts and path.is_relative_to(WORK) and not path.is_relative_to(WORK/'private')
    for p in path.parents:
        if p == WORK.parent: break
        if checked is not None and p in checked: continue
        assert not p.is_symlink(), ('Aliased parent', p)
        if checked is not None: checked.add(p)


def trace():
    r = subprocess.run([sys.executable, '-B', str(TRACE)],
                       check=True, capture_output=True, text=True, cwd=REPO)
    return json.loads(r.stdout)


def make_plan():
    policy = json.loads(POLICY.read_text())
    assert len(policy['firmware_versions']) <= policy['maximum_firmware_versions'] == 5
    dependencies = trace()
    protected = {REPO/n for n in dependencies['read_paths'] if (REPO/n).is_file()}
    protected.update(REPO/n for n in dependencies['metadata_paths'] if (REPO/n).is_file())
    protected.update(WORK/n for rows in policy['firmware_versions'].values() for n in rows)
    protected.update(WORK/n for n in policy['required_files'])
    assert all(p.is_file() for p in protected), 'Missing required input'
    # Protect the inodes too: deleting another hardlink would change nlink.
    inodes = {(p.stat().st_dev, p.stat().st_ino) for p in protected}
    exceptions = [WORK/n for n in policy['exceptions'] if n not in ['dist', 'current-dependency-leaves']]
    victims, roots, checked = {}, set(), set()
    for root in replicas():
        safe_parents(root, checked)
        if any(root == e or root.is_relative_to(e) for e in exceptions): continue
        roots.add(str(root.relative_to(REPO)))
        for p in leaves(root):
            safe_parents(p, checked)
            s = p.lstat()
            assert stat.S_ISREG(s.st_mode) or stat.S_ISLNK(s.st_mode), ('Special file refused', p)
            if p in protected or (s.st_dev, s.st_ino) in inodes: continue
            victims[str(p.relative_to(REPO))] = {'stat': signature(p), 'allocated_bytes': s.st_blocks*512}
    mounts = [line.split()[4] for line in Path('/proc/self/mountinfo').read_text().splitlines()]
    assert not any(m == str(REPO/r) or m.startswith(str(REPO/r)+'/') for m in mounts for r in roots), 'Mounted replica'
    pins = {str(p.relative_to(REPO)): {'sha256': digest(p), 'stat': signature(p)} for p in protected}
    return {'schema': 1, 'policy_sha256': digest(POLICY), 'tool_sha256': digest(SOURCE),
            'trace_sha256': digest(TRACE), 'dependencies': dependencies,
            'protected': pins, 'candidate_roots': sorted(roots), 'remove': victims,
            'estimated_allocated_bytes': sum(r['allocated_bytes'] for r in victims.values()),
            'free_bytes_before': shutil.disk_usage(REPO).free, 'complete': False}


def apply(plan, report):
    assert plan['policy_sha256'] == digest(POLICY)
    assert plan['tool_sha256'] == digest(SOURCE) and plan['trace_sha256'] == digest(TRACE)
    mounts = [line.split()[4] for line in Path('/proc/self/mountinfo').read_text().splitlines()]
    assert not any(m == str(REPO/r) or m.startswith(str(REPO/r)+'/')
                   for m in mounts for r in plan['candidate_roots']), 'Mounted replica'
    # Refuse open files or changed content. Do not guess about other processes.
    victims = plan['remove']; target_inodes, checked = set(), set()
    for n, row in victims.items():
        p = REPO/n; safe_parents(p, checked)
        assert signature(p) == row['stat'], ('Changed candidate', n)
        target_inodes.add(tuple(row['stat'][:2]))
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            if proc.stat().st_uid != os.getuid(): continue
            for fd in (proc/'fd').iterdir():
                try: s = fd.stat()
                except PermissionError:
                    # Non-dumpable desktop services can share our UID. Refuse
                    # if their command references this checkout; otherwise skip.
                    command = (proc/'cmdline').read_bytes()
                    assert not any(x in command for x in [str(REPO).encode(), b'muos-r35s-port', b'phase4']), ('Uninspectable workspace process', proc.name)
                    continue
                except FileNotFoundError: continue
                assert (s.st_dev, s.st_ino) not in target_inodes, ('Open candidate', proc.name)
        except PermissionError:
            command = (proc/'cmdline').read_bytes()
            assert not any(x in command for x in [str(REPO).encode(), b'muos-r35s-port', b'phase4']), ('Uninspectable workspace process', proc.name)
        except (FileNotFoundError, ProcessLookupError): continue
    for n, row in plan['protected'].items():
        assert signature(REPO/n) == row['stat'] and digest(REPO/n) == row['sha256'], ('Changed pin', n)
    report.write_text(json.dumps(plan, indent=2)+'\n')
    for n in victims: (REPO/n).unlink()
    # Remove empty replica directories only; required ancestors are retained.
    for n in plan['candidate_roots']:
        root = REPO/n
        if root.is_dir() and not root.is_symlink():
            for base, dirs, files in os.walk(root, topdown=False, followlinks=False):
                if not any(Path(base).iterdir()): Path(base).rmdir()
    for n, row in plan['protected'].items():
        assert signature(REPO/n) == row['stat'] and digest(REPO/n) == row['sha256'], ('Protected input changed', n)
    after = trace()
    assert after == plan['dependencies'], 'Dependency closure changed'
    os.sync()
    plan.update(complete=True, protected_hashes_and_metadata_unchanged=True,
                offline_dependency_closure_unchanged=True,
                free_bytes_after=shutil.disk_usage(REPO).free)
    plan['reclaimed_bytes'] = plan['free_bytes_after'] - plan['free_bytes_before']
    report.write_text(json.dumps(plan, indent=2)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', type=Path, metavar='REVIEWED_PLAN')
    args = parser.parse_args()
    area = REPO/'build/cleanup'; area.mkdir(exist_ok=True)
    if args.apply:
        report = args.apply.resolve()
        assert report.parent == area.resolve() and not args.apply.is_symlink()
        plan = json.loads(report.read_text()); assert not plan['complete']
        apply(plan, report)
        print('Cleanup verified; physical reclaimed bytes:', plan['reclaimed_bytes'])
    else:
        plan = make_plan()
        report = area/('retention-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json')
        report.write_text(json.dumps(plan, indent=2)+'\n')
        print('Dry run:', len(plan['remove']), 'files;', plan['estimated_allocated_bytes'], 'allocated bytes;', report)


if __name__ == '__main__': main()
