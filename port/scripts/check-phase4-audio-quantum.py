#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Exercise the real S95 quantum hook with only pw-metadata replaced."""
from pathlib import Path
import json, subprocess, tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2]; area=repo/'build/phase4/audio-buffers'
s=Path(tempfile.mkdtemp(prefix='quantum-checks.',dir=area))
source=repo/'port/device/rk-r35s-p0/S95muos-core'; text=source.read_text()
prefix=text.split('case "${1:-}" in',1)[0]
cases=[]
for label,quantum,mode,want in [('disabled',0,'ok',0),('set_and_readback',1024,'ok',0),('set_failure',1024,'set-fail',1),('read_failure',1024,'get-fail',1),('wrong_readback',1024,'wrong',1),('invalid_value',512,'ok',64)]:
 d=s/label; d.mkdir()
 stub='''pw-metadata() {
 echo "$*" >> "$state/calls"
 if [ "$#" = 5 ]; then [ "$fixture_mode" != set-fail ]; return $?; fi
 [ "$fixture_mode" != get-fail ] || return 1
 if [ "$fixture_mode" = wrong ]; then echo "update: id:0 key:'clock.force-quantum' value:'0' type:''"
 else echo "update: id:0 key:'clock.force-quantum' value:'1024' type:''"; fi
}
'''
 code=prefix+f'\nstate={d}; audio_quantum={quantum}; fixture_mode={mode}\n'+stub+'audio_set_quantum\n'
 r=subprocess.run(['sh','-c',code],capture_output=True,text=True)
 assert r.returncode==want,(label,r.stdout,r.stderr)
 if quantum in [0,512]: assert not (d/'calls').exists()
 if label=='set_and_readback': assert len((d/'calls').read_text().splitlines())==2
 (d/'fixture.sh').write_text(code); cases.append(label)
report={'passed':True,'cases':cases,'device_accessed':False,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),source]}}
(s/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-quantum-checks').write_text(str(s)+'\n')
print('S95 quantum6 guards passed',s)
