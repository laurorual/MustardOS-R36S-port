#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check that metadata failures still return to the launcher before teardown."""
from pathlib import Path
import json,subprocess,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/gb-state'
source=repo/'port/device/rk-r35s-p0/gb-state';parent=source.with_name('gb-exit')
assert (source/'app-launch.sh').read_text()==(parent/'app-launch.sh').read_text().replace('C50_PRIVATE','C51_PRIVATE')
for f in source.glob('*.sh'):subprocess.run(['sh','-n',str(f)],check=True)
stage=Path(tempfile.mkdtemp(prefix='dispatch-check.',dir=area))
cases=['valid','inspector_failure','missing_save','missing_load','app_failure']
for name in cases:
 d=stage/name;d.mkdir();(d/'state').mkdir();(d/'runtime').mkdir()
 game='C44_FIRST_PRESENT seconds=45 serial=7\nC50_EXIT reason=hotkey frames=100\nSaved state to private\nLoaded state from private\n'
 if name!='missing_save':game+='Quick Save (hotkey)\n'
 if name!='missing_load':game+='Quick Load (hotkey)\n'
 (d/'game.template').write_text(game)
 (d/'runner').write_text(f'''#!/bin/sh
set -eu
echo "$1" >> {d}/calls
case "$1" in
65) cat {d}/game.template;[ '{name}' != app_failure ] ;;
35) printf 'port-cycle-done\\n' > {d}/runtime/action
printf 'C45_LAUNCHER_PRESENT phase=return serial=20\\nC45_LAUNCHER_EXIT action=port-cycle-done\\n' ;;
*) exit 99;;
esac
''');(d/'runner').chmod(0o700)
 (d/'state-metadata').write_text(f"#!/bin/sh\n[ '{name}' != inspector_failure ]\n");(d/'state-metadata').chmod(0o700)
 text=(source/'select.sh').read_text().split('c46_consume\n',1)[1]
 text=text.replace('/run/muos/',str(d/'runtime')+'/')
 (d/'fixture.sh').write_text(f'set -eu\ncapsule={d}\nappdir={d}\n'+text)
 r=subprocess.run(['sh',str(d/'fixture.sh')],capture_output=True,text=True,timeout=5)
 assert (r.returncode==0)==(name=='valid'),(name,r.returncode,r.stderr)
 assert (d/'calls').read_text()=='65\n35\n',name
 assert ('C51_STATE_CYCLE_COMPLETE' in r.stdout)==(name=='valid')
 (d/'stdout').write_text(r.stdout);(d/'stderr').write_text(r.stderr)
report={'passed':True,'cases':cases,'private_ROM_used':False,'device_accessed':False,
        'return_before_state_failure':True,'source_sha256':{str(f.relative_to(repo)):sha(f) for f in [Path(__file__),*source.glob('*.sh')]}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
(area/'latest-dispatch-checks').write_text(str(stage)+'\n')
print('C51 dispatch failure/return checks passed:',stage)
