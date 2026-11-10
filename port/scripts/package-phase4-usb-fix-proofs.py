#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze only public C16-C18 and stable Wi-Fi policy evidence, never private runtime."""
from pathlib import Path
import hashlib,json,shutil
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/network-warm'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
control=Path((area/'latest-control').read_text().strip())
shutdown=Path((area/'latest-pre-shutdown').read_text().strip())
bt=Path((area/'latest-bt-isolation').read_text().strip())
policy=Path((area/'latest-wifi-policy').read_text().strip())
for stage in [control,shutdown,bt]:assert json.loads((stage/'cleanup-analysis.json').read_text())['passed']
assert json.loads((policy/'analysis.json').read_text())['passed']
for cycle in [1,2]:
    assert json.loads((bt/f'cycle-{cycle}-analysis.json').read_text())['automatic_network_ready']
    assert not json.loads((bt/f'cycle-{cycle}-user-confirmation.json').read_text())['physical_dongle_reconnected']
assert not json.loads((policy/'user-confirmation.json').read_text())['physical_dongle_reconnected']
assert (repo/'build/phase4/graphics-config/output/.config').read_bytes()==(repo/'build/phase4/network-tools/baseline.config').read_bytes()
entries=[(control,'usb-control-observation'),(shutdown,'usb-pre-shutdown-negative'),(bt,'wifi-bt-isolation'),(policy,'wifi-only-policy')]
assert not any((repo/'dist/phase4'/name).exists() for _,name in entries),'Do not overwrite immutable proofs'
def copy(src,dst):
    assert src.is_file() and not src.is_symlink(),src
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
def tree(src,dst):
    for p in sorted(src.rglob('*')):
        if p.is_file():copy(p,dst/p.relative_to(src))
allowed=['manifest.json','analysis.json','install-analysis.json','cleanup-analysis.json','baseline-analysis.json',
         'baseline.txt','baseline-fat.txt','before.txt','after.txt','replug.txt','initial-report.txt','recovery.txt',
         'user-confirmation.json','pre-shutdown-public.txt','shell.stdout','shell.stderr','btusb-blacklist.conf',
         'cycle-1-analysis.json','cycle-2-analysis.json','cycle-1-user-confirmation.json','cycle-2-user-confirmation.json',
         'cycle-1-initial-report.txt','cycle-2-initial-report.txt','cycle-1-recovery.txt','cycle-2-recovery.txt',
         'verifier-awk-check.stdout','verifier-awk-check.stderr']
labels=['install','installed-health','baseline-read','collection','launch','pre-shutdown-proof','retired-token-cleanup',
        'cleanup','observer-cleanup','cycle-1-collection','cycle-2-collection','cycle-1-boot','cycle-2-boot',
        'boot-request','native-verification','native-verification-fixed']
for stage,name in entries:
    out=repo/'dist/phase4'/name;out.mkdir(parents=True)
    for n in allowed:
        if (stage/n).is_file():copy(stage/n,out/n)
    for label in labels:
        for suffix in ['sh','stdout','stderr','exit']:
            p=stage/(label+'.'+suffix)
            if p.is_file():copy(p,out/p.name)
    for p in stage.glob('*.py'):copy(p,out/'executed-source'/p.name)
    for sub in ['payload','package']:
        if (stage/sub).is_dir():tree(stage/sub,out/('public-'+sub))
    for n in ['phase4-usb-control.md','phase4-resume-checkpoint.md','roadmap.md']:
        copy(repo/'docs/archive/phase4'/n,out/'docs'/n)
    if stage==control:
        m=json.loads((stage/'manifest.json').read_text());build=Path(m['checks_stage'])
        for n in ['manifest.json','elf.txt','loader.txt','usb-control-probe.c','usb-control-probe-test.c','build.stdout','build.stderr']:
            copy(build/n,out/'AArch64-build'/n)
        for p in build.glob('fixture-*.stdout'):copy(p,out/'AArch64-build'/p.name)
        wrapper=Path(m['wrapper_checks_stage'])
        for n in ['manifest.json','fixture.sh','stdout','stderr']:copy(wrapper/n,out/'wrapper-checks'/n)
        copy(repo/'port/LICENSE',out/'public-payload/LICENSE')
    if stage==shutdown:
        checked=Path(json.loads((stage/'manifest.json').read_text())['checks_stage'])
        for n in ['manifest.json','fixture.sh','stdout','stderr']:copy(checked/n,out/'checks'/n)
    if stage==policy:
        build=Path(json.loads((stage/'manifest.json').read_text())['build_stage'])
        for n in ['manifest.json','recipe.mk','recipe.stdout','recipe.stderr','kconfig.stdout','kconfig.stderr']:
            copy(build/n,out/'recipe-checks'/n)
        copy(build/'kconfig/.config',out/'recipe-checks/isolated.config')
        tree(repo/'port/device/rk-r35s-p0/wifi-only',out/'port-source/wifi-only')
        tree(repo/'port/buildroot/package/muos-r35s-wifi-only',out/'port-source/package')
        for p in [repo/'port/buildroot/Config.in',repo/'port/device/rk-r35s-p0/phase4-wifi-only.fragment',
                  repo/'port/scripts/prepare-phase4-wifi-policy.py',repo/'port/scripts/promote-phase4-wifi-policy.py',
                  repo/'port/scripts/finish-phase4-wifi-verification.py',Path(__file__)]:
            copy(p,out/'port-source'/p.name)
    files=sorted(p for p in out.rglob('*') if p.is_file())
    (out/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(out))+'\n' for p in files))
    for line in (out/'SHA256SUMS').read_text().splitlines():
        digest,n=line.split('  ',1);assert sha(out/n)==digest,n
    print('Frozen and hash-verified:',out)
