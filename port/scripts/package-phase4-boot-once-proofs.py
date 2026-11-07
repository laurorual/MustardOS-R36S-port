#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze public C12 one-shot boot, fallback and negative preflight evidence."""
from pathlib import Path
import hashlib,json,shutil
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/boot-order'
stage=Path((area/'latest-boot-test').read_text().strip());meta=json.loads((stage/'manifest.json').read_text());analysis=json.loads((stage/'boot-analysis.json').read_text())
assert analysis['passed'] and analysis['C07_fallback_next_boot_tested'] and analysis['public_FAT_reports_survived_reboot']
assert analysis['boot_sequence']==27 and analysis['fallback_boot_sequence']==28
assert json.loads((stage/'install-analysis.json').read_text())['passed']
assert json.loads((stage/'user-confirmation.json').read_text())['audio_reported_low']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,digest in meta['source_sha256'].items():assert sha(repo/name)==digest,name
assert sha(repo/'port/scripts/collect-phase4-boot-once.py')==analysis['collector_sha256']
assert (repo/'build/phase4/graphics-config/output/.config').read_bytes()==(repo/'build/phase4/network-tools/baseline.config').read_bytes()
coordinator=Path(meta['coordinator_stage']);negative=area/'boot-test.zw07_f5k'
names=['boot-once-preflight','boot-once-native','boot-once-root-path-preflight-failure']
outputs=[repo/'dist/phase4'/name for name in names];assert not any(out.exists() for out in outputs),'Never overwrite immutable proofs'
for out in outputs:out.mkdir(parents=True)
pre,native,failed=outputs
def copy(src,dst):
 assert src.is_file() and not src.is_symlink(),src
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
def tree(src,dst):
 for p in sorted(src.rglob('*')):
  if p.is_file():copy(p,dst/p.relative_to(src))
for name in ['manifest.json','install-analysis.json','install.sh','install-functions.sh','shell.stdout','shell.stderr']:
 copy(stage/name,pre/name)
tree(stage/'payload',pre/'payload')
for label,pointer in [('order','latest-checks'),('adapters','latest-adapter-checks'),('diagnostic','latest-diagnostic-checks')]:
 checked=Path((area/pointer).read_text().strip());r=json.loads((checked/'report.json').read_text());assert r['passed']
 for name in ['report.json','fixture.sh','stdout','stderr']:
  if (checked/name).is_file():copy(checked/name,pre/'checks'/label/name)
for name in ['recipe.mk','recipe.stdout','recipe.stderr','bounded-loader.txt','bounded-elf.txt','manifest.json']:
 copy(coordinator/name,pre/'coordinator'/name)
tree(stage/'native',native/'native')
for name in ['manifest.json','install-analysis.json','boot-analysis.json','user-confirmation.json','fallback-user-confirmation.json','installed.sha256','boot-ssh-probes.json','fallback-ssh-probes.json']:
 copy(stage/name,native/name)
for label in ['preflight','install','verify','infrastructure-before','infrastructure-after','native-health','installed-checksums','fallback-preflight','fallback-health','first-online','reboot-request','fallback-reboot']:
 for suffix in ['stdout','stderr','exit']:
  p=stage/(label+'.'+suffix)
  if p.is_file():copy(p,native/p.name)
for name in ['manifest.json','install.sh','install-functions.sh','install.stdout','install.stderr','install.exit','negative-cleanup.stdout','negative-cleanup.stderr']:
 copy(negative/name,failed/name)
(failed/'STATE.txt').write_text('First installer stuck in parent traversal for // during read-only preflight.\nPID5644 terminated with TERM; rootRO, no new targets/token, C07 still online.\nRAM removed after read-only health checks. Fixed // termination, regression included.\nNo installer root write or boot was performed in this failed attempt.\n')
source_files=[*sorted((repo/'port/device/rk-r35s-p0/boot').iterdir()),*sorted((repo/'port/device/rk-r35s-p0/boot-diagnostic').iterdir()),*sorted((repo/'port/buildroot/package/muos-r35s-boot').iterdir())]
source_files += [repo/'port/scripts'/name for name in ['check-phase4-boot-order.py','check-phase4-boot-adapters.py','check-phase4-boot-diagnostic.py','prepare-phase4-boot-coordinator.py','prepare-phase4-boot-diagnostic.py','install-phase4-boot-once.py','collect-phase4-boot-once.py',Path(__file__).name]]
for p in source_files:copy(p,pre/'port-source'/p.relative_to(repo/'port'))
for out in outputs:
 for name in ['phase4-boot-once.md','phase4-boot-coordinator.md','phase4-resume-checkpoint.md','roadmap.md']:copy(repo/'docs/analysis'/name,out/'docs'/name)
 if out!=failed:
  (out/'STATE.txt').write_text('C12 boot27 and C07 one-shot fallback boot28 passed.88 host cases20+33+35.\nTargeted install only; no kernel/DTB/bootloader/partitions/libs/modules changes.\nWarm boot network required physical dongle reconnect in both27 and28.\nC12 recovered daemons have PID/starttime/exe ownership; saved seed bootstrap once.\nMenu90s/Dpad/A/B/Fn confirmed; audio present but reported low at SPK_HP157/software100.\n21 profile+21 originals, mixer/brightness/DRM/volume-store restored;55 prerequisites passed.\nRootRO/FAT unmounted/taint0; public FAT reports survived subsequent reboot.\nSelector remains installed, pending token consumed, defaultC07, allow_power0.\nFull power/shutdown qualification, settings persistence, loudness and warm Wi-Fi unresolved.\nNo saved seed/private key/credential material exported; no offline fsck after21.\n')
 files=sorted(p for p in out.rglob('*') if p.is_file());(out/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(out))+'\n' for p in files))
 for line in (out/'SHA256SUMS').read_text().splitlines():digest,name=line.split('  ',1);assert sha(out/name)==digest,name
 print('Frozen and hash-verified:',out)
