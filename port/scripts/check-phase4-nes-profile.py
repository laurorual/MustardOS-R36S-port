#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C48 coordinator dispatch guards in disposable paths; no device/network."""
from pathlib import Path
import json, os, subprocess, tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2]
area=repo/'build/phase4/nes-profile'
stage=Path(tempfile.mkdtemp(prefix='dispatch-check.',dir=area))
source=repo/'port/device/rk-r35s-p0/nes-profile/profile.sh'
cases=['automatic','physical','bad_physical_value','symlink_marker','writable_marker',
       'hardlinked_marker','app_failure','missing_trace','symlink_trace','large_trace','repeat']
for name in cases:
    d=stage/name;d.mkdir(mode=0o700);(d/'state').mkdir(mode=0o700)
    trace=d/'input.csv';trace.write_text('stage,parent,scope,mean_ms\nframe,none,cadence,16.7\n')
    marker=d/'physical.once'
    if name in {'physical','bad_physical_value','symlink_marker','writable_marker','hardlinked_marker'}:
        marker.write_text('bad\n' if name=='bad_physical_value' else 'C48_PHYSICAL\n');marker.chmod(0o600)
    if name=='symlink_marker':marker.rename(d/'other');marker.symlink_to(d/'other')
    if name=='writable_marker':marker.chmod(0o666)
    if name=='hardlinked_marker':os.link(marker,d/'other')
    if name=='missing_trace':trace.unlink()
    if name=='symlink_trace':trace.rename(d/'othertrace');trace.symlink_to(d/'othertrace')
    if name=='large_trace':trace.write_bytes(b'x'*131073)
    game="printf 'C44_FIRST_PRESENT seconds=30 serial=1\\nC44_NORMAL_EXIT expired=1 frames=1800\\n'"
    runner=d/'runner'
    runner.write_text('#!/bin/sh\nset -eu\n[ "$MUXRETRO_PERF_CAPTURE" = 1 ]\n'
                      +f'echo call >> {d}/called\n'
                      +('exit 42\n' if name=='app_failure' else game+'\n'))
    runner.chmod(0o700)
    (d/'select.sh').write_text('#!/bin/sh\nset -eu\n[ "$MUXRETRO_PERF_CAPTURE" = 1 ]\n'
                             +f'[ "$1" = {d} ] && [ "$2" = observe ]\n'
                             +f'echo select >> {d}/called\n'+game+f' > {d}/state/game.log\n')
    code=source.read_text().replace('/run/muos-prefs-data.??????',str(d)).replace('/run/muos/storage/pickles/performance.csv',str(trace))
    code=code.replace('0:0:',f'{os.getuid()}:{os.getgid()}:')
    (d/'fixture.sh').write_text(code)
    r=subprocess.run(['sh',str(d/'fixture.sh'),str(d),'observe'],capture_output=True,text=True,timeout=5)
    (d/'stdout').write_text(r.stdout);(d/'stderr').write_text(r.stderr)
    valid=name in {'automatic','physical','repeat'}
    assert (r.returncode==0)==valid,(name,r.returncode,r.stdout,r.stderr)
    assert (d/'state/performance.csv').exists()==valid
    if name in {'bad_physical_value','symlink_marker','writable_marker','hardlinked_marker'}:
        assert not (d/'called').exists()
    if name=='physical':assert (d/'called').read_text()=='select\n' and not marker.exists()
    if name=='repeat':
        repeated=subprocess.run(['sh',str(d/'fixture.sh'),str(d),'observe'],capture_output=True,text=True,timeout=5)
        assert repeated.returncode!=0 and (d/'called').read_text()=='call\n'
report={'passed':True,'cases':cases,'real_core_executed':False,'device_accessed':False,
        'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),source]}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
(area/'latest-dispatch-checks').write_text(str(stage)+'\n')
print('C48 dispatch guards passed:',len(cases),stage)
