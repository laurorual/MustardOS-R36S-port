#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Regression: exercise the real C07 writer with inherited umasks and old temp files."""
from pathlib import Path
import json,os,subprocess,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/rootfs-candidate'
source=repo/'port/device/rk-r35s-p0/network-diagnostic/run.sh';text=source.read_text()
assert text.index('umask 077')<text.index('mkdir -p "$state"')
writer=text[text.index('sequence=$(cat "$sequence_dir/boot-seq")'):text.index('archive=$(printf')]
assert 'chmod 600 "$sequence_dir/boot-seq.tmp"' in writer
stage=Path(tempfile.mkdtemp(prefix='counter-checks.',dir=area));cases={}
for label,mask,oldtmp,value,success in [('direct-init-022','022',False,'46',True),('inherited-000','000',False,'46',True),('legacy-077','077',False,'46',True),('existing-temp-666','022',True,'46',True),('invalid-counter','022',False,'bad',False),('counter-exhausted','022',False,'9999',False)]:
 root=stage/label;root.mkdir(mode=0o700);(root/'boot-seq').write_text(value+'\n');(root/'boot-seq').chmod(0o600)
 if oldtmp:(root/'boot-seq.tmp').write_text('stale\n');(root/'boot-seq.tmp').chmod(0o666)
 r=subprocess.run(['sh','-c',f'umask {mask}\numask 077\nsequence_dir=$1\n'+writer,'fixture',str(root)],capture_output=True,text=True)
 assert (r.returncode==0)==success,label
 if success:assert (root/'boot-seq').read_text()=='47\n' and (root/'boot-seq').stat().st_mode&0o777==0o600
 else:assert (root/'boot-seq').read_text()==value+'\n'
 cases[label]=True
# Control: the old C23 runner under direct BusyBox init reproduces mode644.
old=(repo/'build/phase4/rootfs-candidate/composition.rtvw4swv/target/usr/libexec/muos-c07-run').read_text();old_writer=old[old.index('sequence=$(cat "$sequence_dir/boot-seq")'):old.index('archive=$(printf')]
root=stage/'old-control';root.mkdir();(root/'boot-seq').write_text('46\n')
r=subprocess.run(['sh','-c','umask 022\nsequence_dir=$1\n'+old_writer,'fixture',str(root)],capture_output=True);assert r.returncode==0 and (root/'boot-seq').stat().st_mode&0o777==0o644
cases['old-direct-init-control-reproduces-644']=True
report={'passed':True,'cases':cases,'real_counter_writer_exercised':True,'hardware_accessed':False,'source_sha256':{str(source.relative_to(repo)):sha(source),str(Path(__file__).relative_to(repo)):sha(Path(__file__))}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-counter-checks').write_text(str(stage)+'\n');print('C07 umask regression7 cases passed:',stage)
