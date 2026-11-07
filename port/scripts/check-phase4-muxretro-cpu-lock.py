#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Exercise the native RAM lock guard on disposable directories and real flock."""
from pathlib import Path
import fcntl
import json
import subprocess
import tempfile
from phase4_candidate import sha

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/muxretro'
source=repo/'port/device/rk-r35s-p0/muxretro-cpu/session-lock.sh'
stage=Path(tempfile.mkdtemp(prefix='cpu-lock-checks.',dir=area));cases=[]
for name in ['cold_directory','existing_directory','symlink','wrong_mode','wrong_owner','busy_lock']:
    root=stage/name;root.mkdir();target=root/'session';held=None
    if name not in ['cold_directory','symlink']:target.mkdir(mode=0o700)
    if name=='symlink':
        (root/'destination').mkdir(mode=0o700);target.symlink_to(root/'destination',target_is_directory=True)
    if name=='wrong_mode':target.chmod(0o755)
    if name=='busy_lock':
        held=(target/'lifetime.lock').open('w');fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
    # Ownership is translated for the unprivileged fixture; real modes/flock remain live.
    stub='''stat() {
 mode=$(command stat -c %a "$3") || return 1
 printf '%s:%s:%s\\n' OWNER 0 "$mode"
}
'''.replace('OWNER','1' if name=='wrong_owner' else '0')
    code='set -eu\numask 077\n'+stub+source.read_text().replace('/run/muos/session',str(target))+'\necho ACQUIRED\n'
    result=subprocess.run(['sh','-c',code],capture_output=True,text=True)
    if held:held.close()
    assert (result.returncode==0)==(name in ['cold_directory','existing_directory']),(name,result.stderr)
    if name in ['symlink','wrong_mode','wrong_owner']:assert not (target/'lifetime.lock').exists()
    if name=='cold_directory':assert (target.stat().st_mode&0o777)==0o700
    (root/'fixture.sh').write_text(code);cases.append(name)
report={'passed':True,'cases':cases,'hardware_accessed':False,'real_flock_exercised':True,
        'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),source]}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
(area/'latest-cpu-lock-checks').write_text(str(stage)+'\n')
print('C42 CPU lock cases passed:',len(cases),stage)
