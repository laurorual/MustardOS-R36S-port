#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C30 integrity/semantic checks on one disposable factory tree; no device."""
from pathlib import Path
import json, shutil, subprocess, tempfile
from phase4_candidate import sha,sums,validate
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/rootfs-candidate'
old=Path((area/'latest-update').read_text().strip());plan=json.loads((old/'plan.json').read_text())
assert plan['experiment']=='C27_VOLUME_CALIBRATION'
stage=Path(tempfile.mkdtemp(prefix='irq-candidate-checks.',dir=area));root=stage/'target'
shutil.copytree(Path(plan['candidate_stage'])/'target',root,symlinks=True)
config=root/'opt/muos/device/control/wireplumber.conf';foundation=root/'usr/libexec/muos-session/prerequisites.sha256'
original=config.read_bytes();records=sums(foundation);assert len(records)==96
assert validate(root)['foundation_files']==96
cases=['legacy_C27_96_contract_retained']
config.write_text(original.decode().replace('      api.alsa.period-size = 1024\n','      api.alsa.disable-tsched = true\n      api.alsa.period-size = 1024\n'))
name='/opt/muos/device/control/wireplumber.conf';records[name]=sha(config)
def refresh():foundation.write_text(''.join(sha(root/n.lstrip('/'))+'  '+n+'\n' for n in records))
refresh();assert validate(root)['foundation_files']==97;cases.append('IRQ_config_and_97_foundation_accepted')
native=bytes(config.read_bytes());manifest=foundation.read_bytes()
def refuse(label,change):
 try:
  change()
  try:validate(root)
  except (AssertionError,OSError,ValueError):pass
  else:raise AssertionError('Unexpected validation: '+label)
  cases.append(label)
 finally:
  if config.is_symlink():config.unlink()
  config.write_bytes(native);foundation.write_bytes(manifest)
refuse('IRQ_without_foundation_coverage_refused',lambda:foundation.write_text(''.join(d+'  '+n+'\n' for n,d in records.items() if n!=name)))
def no_irq():config.write_bytes(original);refresh()
refuse('97_with_timer_config_even_fresh_hash_refused',no_irq)
def conflict():config.write_text(native.decode()+'      api.alsa.disable-tsched = false\n');refresh()
refuse('conflicting_setting_with_fresh_hash_refused',conflict)
def linked():
 copy=stage/'config-link-target';copy.write_bytes(native);config.unlink();config.symlink_to(copy)
refuse('symlink_policy_refused',linked)
refuse('stale_config_digest_refused',lambda:config.write_bytes(native+b'#changed\n'))
library=root/'usr/libexec/muos-candidate-boot-checks'
def gate():return subprocess.run(['sh','-c','. "$1"; candidate_boot_check "$2"','fixture',str(library),str(root)],capture_output=True,text=True).returncode
assert gate()==0;cases.append('installed_native_gate_accepts_97_without_code_change')
config.write_bytes(native+b'#corrupt\n');assert gate()!=0;cases.append('native_gate_rejects_changed_IRQ_policy');config.write_bytes(native)
sources=[Path(__file__),repo/'port/scripts/phase4_candidate.py']
(stage/'analysis.json').write_text(json.dumps({'passed':True,'cases':cases,'hardware_accessed':False,'native_code_changed':False,'sources':{str(p.relative_to(repo)):sha(p) for p in sources}},indent=2)+'\n')
(area/'latest-irq-candidate-checks').write_text(str(stage)+'\n')
print('IRQ candidate checks passed:',len(cases),stage)
