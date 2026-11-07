#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C50 source-lineage and owned dispatch checks, without device or private ROM."""
from pathlib import Path
import json,os,subprocess,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/gb-exit'
source=repo/'port/device/rk-r35s-p0/gb-exit';parent=repo/'port/device/rk-r35s-p0/gb-core'
assert (source/'app-launch.sh').read_text()==(parent/'app-launch.sh').read_text().replace('--diagnostic-seconds=45','--diagnostic-seconds=45 --diagnostic-hotkey-exit').replace('C49_PRIVATE_CONTENT_VERIFIED','C50_PRIVATE_CONTENT_VERIFIED')
assert (source/'select.sh').read_text()==(parent/'select.sh').read_text().replace("grep -q '^C44_NORMAL_EXIT expired=1 frames=[1-9]'","grep -Eq '^C50_EXIT reason=(hotkey|deadline) frames=[1-9]'")
for f in source.glob('*.sh'):subprocess.run(['sh','-n',str(f)],check=True)
stage=Path(tempfile.mkdtemp(prefix='dispatch-check.',dir=area))
cases=['deadline','hotkey','unexpected_hotkey','failure','zero_frames','wrong_ready','app_failure','repeat']
for name in cases:
    d=stage/name;d.mkdir(mode=0o700);(d/'state').mkdir();(d/'runtime').mkdir()
    (d/'trace.csv').write_text('stage,parent,scope,mean_ms\nframe,none,cadence,16.7\n')
    reason='hotkey' if name in {'hotkey','unexpected_hotkey'} else 'failure' if name=='failure' else 'deadline'
    frames=0 if name=='zero_frames' else 100
    ready='1' if name=='wrong_ready' else '0'
    game=f"C50_HOTKEY_READY seconds=45 modifier=menu button=start auto_save={ready} timeline=0 sram_flush=0\nC44_FIRST_PRESENT seconds=45 serial=7\nC50_EXIT reason={reason} frames={frames}\n"
    (d/'game.template').write_text(game)
    # Only the new coordinator is executed here. Core/SDL/native UI are fakes.
    runner=d/'runner';runner.write_text(f'''#!/bin/sh
set -eu
echo "$1" >> {d}/called
case "$1" in
65) [ "{name}" != app_failure ] || exit 42;cat {d}/game.template ;;
35) printf 'port-cycle-done\\n' > {d}/runtime/action
printf 'C45_LAUNCHER_PRESENT phase=return serial=20\\nC45_LAUNCHER_EXIT action=port-cycle-done\\n' ;;
*) exit 99 ;;
esac
''');runner.chmod(0o700)
    (d/'select.sh').write_text(f'#!/bin/sh\n[ "$MUXRETRO_PERF_CAPTURE" = 1 ]\ncp {d}/game.template {d}/state/game.log\n')
    code=(source/'session.sh').read_text().replace('/run/muos-prefs-data.??????',str(d)).replace('/run/muos/storage/pickles/performance.csv',str(d/'trace.csv')).replace('/run/muos/',str(d/'runtime')+'/').replace('0:0:',f'{os.getuid()}:{os.getgid()}:')
    (d/'fixture.sh').write_text(code)
    args=['sh',str(d/'fixture.sh'),str(d),'observe' if name=='hotkey' else 'cycle']
    r=subprocess.run(args,text=True,capture_output=True,timeout=5)
    (d/'stdout').write_text(r.stdout);(d/'stderr').write_text(r.stderr)
    good=name in {'deadline','hotkey','repeat'}
    assert (r.returncode==0)==good,(name,r.returncode,r.stderr)
    assert ('C50_CONTENT_COMPLETE' in r.stdout)==good
    if name=='unexpected_hotkey':assert (d/'called').read_text()=='65\n'
    if name=='repeat':
        r=subprocess.run(args,text=True,capture_output=True,timeout=5)
        assert r.returncode!=0 and (d/'called').read_text()=='65\n35\n'
# Real launcher argument forwarding, with only paths/ownership/findmnt translated.
d=stage/'launcher';d.mkdir(mode=0o700);(d/'media').mkdir()
for name in ['core.so','private.gb']:(d/name).write_bytes(b'synthetic, never emulated');(d/name).chmod(0o700)
(d/'gb-assets.sha256').write_text(sha(d/'core.so')+'  core.so\n'+sha(d/'private.gb')+'  private.gb\n');(d/'gb-assets.sha256').chmod(0o600)
(d/'muxretro').write_text(f'#!/bin/sh\nprintf "%s\\n" "$@" > {d}/argv\n');(d/'muxretro').chmod(0o700)
code=(source/'app-launch.sh').read_text().replace('/run/muos-prefs-data.??????',str(d)).replace('/mnt/mmc',str(d/'media')).replace('0:0:',f'{os.getuid()}:{os.getgid()}:')
(d/'fixture.sh').write_text('findmnt() { echo tmpfs; };\n'+code)
r=subprocess.run(['sh',str(d/'fixture.sh'),str(d)],capture_output=True,text=True,timeout=5);assert r.returncode==0,r.stderr
assert (d/'argv').read_text().splitlines()==[str(d/'core.so'),str(d/'media/ROMS/GB/private.gb'),'--fresh','--diagnostic-content','--diagnostic-seconds=45','--diagnostic-hotkey-exit']
files=[Path(__file__),*source.glob('*.sh')]
report={'passed':True,'cases':cases+['launcher_arguments'],'C49_selector_and_launcher_normalized_exact':True,
        'native_hotkey_tested':False,'private_ROM_used':False,'device_accessed':False,
        'source_sha256':{str(p.relative_to(repo)):sha(p) for p in files}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-dispatch-checks').write_text(str(stage)+'\n')
print('C50 dispatch checks passed:',len(report['cases']),stage)
