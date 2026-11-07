#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check prior-boot binding and the read-only operation gate, without hardware."""
from pathlib import Path
import copy,json,os,subprocess,tempfile
from phase4_candidate import sha,sums
from phase4_gb_reboot import bind_source
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/gb-reboot';area.mkdir(exist_ok=True)
stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area));cases=[]
identity='ab'*32;assets={'core_sha256':'cd'*32,'ROM_sha256':'ef'*32,'host_binary_sha256':'01'*32}
base=dict(experiment='C53_SELECTIVE_GB_PERSISTENCE',passed=True,cleanup_passed=True,RAM_removed=True,root_ro=True,
          global_mountinfo_unchanged=True,private_identity=identity,boot_sequence=68,**assets)
save=dict(base,mode='save',outcome='save-returned');load=dict(base,mode='load',outcome='load-returned')
assert bind_source(save,load,69,identity,assets)==68;cases.append('next-boot-bound')
for label,mutate in [
 ('same-boot',lambda s,l,a:a.update(boot=68)),('skipped-boot',lambda s,l,a:a.update(boot=70)),
 ('bool-counter',lambda s,l,a:a.update(boot=True)),('different-source-boots',lambda s,l,a:l.update(boot_sequence=67)),
 ('failed-save',lambda s,l,a:s.update(passed=False)),('failed-cleanup',lambda s,l,a:l.update(cleanup_passed=False)),
 ('RAM-not-removed',lambda s,l,a:l.update(RAM_removed=False)),('root-not-ro',lambda s,l,a:s.update(root_ro=False)),
 ('mounts-changed',lambda s,l,a:l.update(global_mountinfo_unchanged=False)),
 ('wrong-role',lambda s,l,a:s.update(mode='load')),('wrong-outcome',lambda s,l,a:l.update(outcome='failed')),
 ('wrong-experiment',lambda s,l,a:l.update(experiment='other')),('identity-mismatch',lambda s,l,a:l.update(private_identity='00'*32)),
 ('core-mismatch',lambda s,l,a:s.update(core_sha256='00'*32)),('ROM-mismatch',lambda s,l,a:l.update(ROM_sha256='00'*32)),
 ('host-mismatch',lambda s,l,a:l.update(host_binary_sha256='00'*32))]:
 s,l=copy.deepcopy(save),copy.deepcopy(load);a={'boot':69};mutate(s,l,a)
 try:bind_source(s,l,a['boot'],identity,assets)
 except AssertionError:pass
 else:raise AssertionError(label)
 cases.append(label)
gate=repo/'port/device/rk-r35s-p0/gb-reboot/store.sh'
for label in ['seed','verify','prepare','commit','save-role','role-extra-line','wrong-digest','backend-symlink','backend-hardlink']:
 d=stage/label;d.mkdir(mode=0o700)
 def put(name,text,mode):p=d/name;p.write_text(text);p.chmod(mode)
 put('role','save\n' if label=='save-role' else 'load\nextra\n' if label=='role-extra-line' else 'load\n',0o600)
 put('store-base.sh',f'printf "%s\\n" "$2" > {d}/called\n',0o700)
 put('store-base.sha256',('00'*32 if label=='wrong-digest' else sha(d/'store-base.sh'))+'\n',0o600)
 if label=='backend-symlink':(d/'store-base.sh').rename(d/'real');(d/'store-base.sh').symlink_to('real')
 if label=='backend-hardlink':os.link(d/'store-base.sh',d/'alias')
 text=gate.read_text().replace('/run/muos-prefs-data.??????',str(d)).replace('0:0:',f'{os.getuid()}:{os.getgid()}:')
 put('fixture.sh',text,0o700)
 op=label if label in {'seed','verify','prepare','commit'} else 'seed'
 r=subprocess.run(['sh',str(d/'fixture.sh'),str(d),op],capture_output=True,text=True,timeout=5)
 good=label in {'seed','verify'}
 assert (r.returncode==0)==good,(label,r.returncode,r.stderr)
 assert (d/'called').exists()==good,label
 cases.append('gate-'+label)
parent=repo/'dist/phase4/gameboy-selective-persistence'
for n,h in sums(parent/'SHA256SUMS').items():assert sha(parent/n)==h
report={'passed':True,'experiment':'C54_PRIOR_BOOT_LOAD_CHECKS','case_count':len(cases),'cases':cases,
        'device_accessed':False,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/scripts/phase4_gb_reboot.py',gate]}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-checks').write_text(str(stage)+'\n')
print('C54 source-binding/read-only gate checks passed:',len(cases),stage)
