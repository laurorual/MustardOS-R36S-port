#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze the five-file C12 power update against the installed one-shot baseline."""
from pathlib import Path
import hashlib, json, shutil, subprocess, tarfile, tempfile

repo = Path(__file__).resolve().parents[2]
work = repo/'build/phase4'; area = work/'boot-order'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
baseline = area/'boot-test.mp19ei2w'
old = json.loads((baseline/'manifest.json').read_text())
assert json.loads((baseline/'boot-analysis.json').read_text())['passed']
coordinator = Path((area/'latest-coordinator').read_text().strip())
meta = json.loads((coordinator/'manifest.json').read_text())
assert meta['host_passed'] and meta['checks']['power']['passed']
for name, digest in meta['source_sha256'].items():
    assert sha(repo/name) == digest, ('stale coordinator', name)
stage = Path(tempfile.mkdtemp(prefix='power-test.', dir=area))
payload = stage/'payload'; new = payload/'new'; new.mkdir(parents=True)
names = ['power-functions.sh', 'order.sh', 'native-functions.sh', 'diagnostic-save.sh', 'service.sh']
updated = {**old['installed_files']}
for name in names:
    source = coordinator/'package/boot'/name
    shutil.copyfile(source, new/name); (new/name).chmod(0o755)
    updated['usr/libexec/muos-boot/'+name] = {'sha256': sha(new/name), 'mode': '755'}
(payload/'new.sha256').write_text(''.join(sha(new/n)+'  '+n+'\n' for n in names))
def sums(files):
    return ''.join(v['sha256']+'  '+n+'\n' for n, v in sorted(files.items()))
(payload/'installed-before.sha256').write_text(sums(old['installed_files']))
changed = {'usr/libexec/muos-boot/'+n for n in names}
(payload/'unchanged.sha256').write_text(sums({n:v for n,v in old['installed_files'].items() if n not in changed}))
(payload/'installed-after.sha256').write_text(sums(updated))
scripts = ['install-functions.sh', 'power-update-functions.sh', 'power-update.sh']
for name in scripts:
    shutil.copyfile(repo/'port/device/rk-r35s-p0/boot-diagnostic'/name, stage/name)
root = work/'linux-diagnostic/network-recovery.zz7sq2ve/extracted'
rel = lambda p: '/work/'+str(p.relative_to(work))
code = 'set -eu\n'+''.join(
    f'qemu-aarch64 -cpu cortex-a35 -L {rel(root)} {rel(root/"bin/busybox")} sh -n {rel(p)}\n'
    for p in [*sorted(new.iterdir()), *(stage/n for n in scripts)])
command = ['podman', 'run', '--rm', '--network=none', '--read-only', '--cap-drop=all',
           '--security-opt=no-new-privileges', '--userns=keep-id', '--tmpfs', '/tmp:rw,nosuid,nodev',
           '-v', f'{work}:/work:rw,z', (work/'rootfs-container.iid').read_text().strip(), 'sh', '-c', code]
r = subprocess.run(command, capture_output=True, text=True, timeout=30)
(stage/'shell.stdout').write_text(r.stdout); (stage/'shell.stderr').write_text(r.stderr)
assert r.returncode == 0, r.stderr
with tarfile.open(stage/'deployment.tar', 'w') as archive:
    for p in [payload, *(stage/n for n in scripts)]: archive.add(p, arcname=p.name)
sources = [Path(__file__), *(repo/'port/device/rk-r35s-p0/boot-diagnostic'/n for n in scripts)]
report = {'host_passed': True, 'experiment': 'MUOS-R35S-DURABLE-POWER-P4-C12',
          'baseline_stage': str(baseline), 'coordinator_stage': str(coordinator),
          'coordinator_manifest_sha256': sha(coordinator/'manifest.json'),
          'installed_files': updated, 'updated_public_files': names,
          'checks': meta['checks'], 'default_power_enabled': False,
          'token_armed_by_update': False, 'reboot_requested_by_update': False,
          'hardware_power_tested': False, 'deployment_sha256': sha(stage/'deployment.tar'),
          'source_sha256': {str(p.relative_to(repo)): sha(p) for p in sources}}
(stage/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
(area/'latest-power-test').write_text(str(stage)+'\n')
print('C12 directed durable-power candidate prepared:', stage)
