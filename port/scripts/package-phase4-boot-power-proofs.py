#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze only public C12 power qualification and rollback evidence, never private state."""
from pathlib import Path
import hashlib, json, shutil

repo = Path(__file__).resolve().parents[2]; area = repo/'build/phase4/boot-order'
stage = Path((area/'latest-power-test').read_text().strip())
meta = json.loads((stage/'manifest.json').read_text())
assert json.loads((stage/'power-analysis.json').read_text())['passed']
assert json.loads((stage/'install-analysis.json').read_text())['passed']
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
for n in meta['updated_public_files']:
    assert sha(repo/'port/device/rk-r35s-p0/boot'/n) == meta['installed_files']['usr/libexec/muos-boot/'+n]['sha256']
assert (repo/'build/phase4/graphics-config/output/.config').read_bytes() == (repo/'build/phase4/network-tools/baseline.config').read_bytes()
outputs = [repo/'dist/phase4'/n for n in ['boot-power-preflight', 'boot-power-native', 'boot-power-update-rollback']]
assert not any(p.exists() for p in outputs), 'Never overwrite immutable proofs'
for p in outputs: p.mkdir(parents=True)
pre, native, negative = outputs
def copy(src, dst):
    assert src.is_file() and not src.is_symlink(), src
    dst.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(src, dst)
def tree(src, dst):
    for p in sorted(src.rglob('*')):
        if p.is_file(): copy(p, dst/p.relative_to(src))
for n in ['manifest.json','install-analysis.json','shell.stdout','shell.stderr','power-update.sh','power-update-functions.sh','install-functions.sh']:
    copy(stage/n, pre/n)
tree(stage/'payload', pre/'payload')
for label, pointer in [('order','latest-checks'),('adapters','latest-adapter-checks'),('power','latest-power-checks'),('diagnostic','latest-diagnostic-checks')]:
    checked = Path((area/pointer).read_text().strip())
    report = json.loads((checked/'report.json').read_text()); assert report['passed']
    if label != 'diagnostic': assert report == meta['checks'][label]
    for n in ['report.json','fixture.sh','stdout','stderr']:
        if (checked/n).is_file(): copy(checked/n, pre/'checks'/label/n)
coordinator = Path(meta['coordinator_stage'])
for n in ['manifest.json','recipe.mk','recipe.stdout','recipe.stderr','bounded-loader.txt','bounded-elf.txt']:
    copy(coordinator/n, pre/'coordinator'/n)
tree(stage/'native', native/'native')
for n in ['manifest.json','install-analysis.json','boot-analysis.json','power-analysis.json','installed.sha256',
          'durable-START.txt','durable-FINAL.txt','durable-PBEGIN.txt','durable-PREADY.txt','user-confirmation.json','fallback-user-confirmation.json']:
    copy(stage/n, native/n)
for label in ['install','verify','infrastructure-before','infrastructure-after','infrastructure-after-refusal',
              'C07-power-refusal','C12-active-refusal','arm','boot-request','power-request','return-health','native-health','installed-checksums']:
    for suffix in ['sh','stdout','stderr','exit']:
        p = stage/(label+'.'+suffix)
        if p.is_file(): copy(p,native/p.name)
failed = area/'power-test.9ac7v5on'
for n in ['manifest.json','power-update.sh','power-update-functions.sh','install-functions.sh',
          'install.stdout','install.stderr','install.exit','rollback-health.stdout','rollback-health.stderr']:
    copy(failed/n, negative/n)
(negative/'STATE.txt').write_text('First public-file update failed at the final relative-path checksum verification.\nRollback0 restored all original installed hashes, rootRO, C07 network and no pending token.\nNo reboot in this attempt. Fixed cd / and added actual-wrapper cwd regression.\n')
sources = [*sorted((repo/'port/device/rk-r35s-p0/boot').iterdir()),
           *sorted((repo/'port/device/rk-r35s-p0/boot-diagnostic').iterdir()),
           *sorted((repo/'port/buildroot/package/muos-r35s-boot').iterdir())]
sources += [repo/'port/scripts'/n for n in ['check-phase4-boot-order.py','check-phase4-boot-adapters.py',
            'check-phase4-boot-diagnostic.py','check-phase4-boot-power.py','prepare-phase4-boot-coordinator.py',
            'prepare-phase4-boot-power.py','install-phase4-boot-power.py','audit-phase4-boot-power.py',
            'collect-phase4-boot-once.py',Path(__file__).name]]
for p in sources: copy(p, pre/'port-source'/p.relative_to(repo/'port'))
for out in outputs:
    for n in ['phase4-boot-power.md','phase4-resume-checkpoint.md','roadmap.md']:
        copy(repo/'docs/archive/phase4'/n, out/'docs'/n)
    files = sorted(p for p in out.rglob('*') if p.is_file())
    (out/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(out))+'\n' for p in files))
    for line in (out/'SHA256SUMS').read_text().splitlines():
        digest, n = line.split('  ',1); assert sha(out/n) == digest,n
    print('Frozen and hash-verified:',out)
