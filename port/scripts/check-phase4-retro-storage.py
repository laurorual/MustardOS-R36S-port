#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C43 fail-closed guards and exact cleanup ordering, without mounts or hardware."""
from pathlib import Path
import json
import subprocess
import tempfile
from phase4_candidate import sha

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/muxretro'
source=repo/'port/device/rk-r35s-p0/muxretro-cpu/storage-capsule.sh';text=source.read_text()
stage=Path(tempfile.mkdtemp(prefix='storage-checks.',dir=area));cases=[]
for name in ['invalid_path','wrong_mode','symlink','same_namespace','missing_argument']:
    d=stage/name;d.mkdir();target=d/'capsule';target.mkdir(mode=0o700)
    if name=='wrong_mode':target.chmod(0o755)
    if name=='symlink':target.rmdir();target.symlink_to(d,target_is_directory=True)
    fixture=text.replace('/run/muos-prefs-data.??????',str(target))
    (d/'probe.sh').write_text(fixture)
    # Model ownership only; retain real directory type/mode and rejection logic.
    stub='''stat() { printf '0:0:%s\\n' "$(command stat -c %a "$3")"; }
readlink() { echo SAME; }
mount() { echo UNEXPECTED_MOUNT; return 99; }
'''
    arg='/wrong' if name=='invalid_path' else str(target)
    code=stub+('set --\n' if name=='missing_argument' else 'set -- "'+arg+'"\n')+'. "'+str(d/'probe.sh')+'"\n'
    r=subprocess.run(['sh','-c',code],capture_output=True,text=True)
    assert r.returncode!=0 and 'UNEXPECTED_MOUNT' not in r.stdout,(name,r.stdout,r.stderr)
    assert '/usr/libexec/muos-session/card-guard.sh' not in r.stderr,'Guard reached package before refusing'
    cases.append(name)
cleanup=text[text.index('cleanup() {'):text.index('trap cleanup EXIT')]
for name,flags,failure,want in [
    ('all_resources',[1,1,1,1],'',0),('no_resources',[0,0,0,0],'',0),
    ('partial_start',[0,0,0,1],'',0),('failed_config_unmount',[1,1,1,1],'/etc/default/muos-storage',1),
    ('changed_original_preferences',[1,1,1,1],'changed',1),
]:
    d=stage/name;d.mkdir();(d/'data/MUOS/preferences').mkdir(parents=True)
    (d/'preferences-before.sha256').write_text('')
    if failure=='changed':(d/'data/MUOS/preferences/changed').write_text('fixture')
    calls=d/'calls';mounted_data,mounted_userdata,mounted_config,storage_attempted=flags
    body=cleanup.replace('/etc/init.d/S90muos-storage','fixture_storage')
    code=f'''dir={d};prefs_mount=$dir/data
mounted_data={mounted_data};mounted_userdata={mounted_userdata};mounted_config={mounted_config};storage_attempted={storage_attempted}
fixture_storage() {{ echo storage-stop >> {calls}; }}
umount() {{ echo "umount $1" >> {calls}; [ "$1" != "{failure}" ]; }}
'''+body+'\ntrue\ncleanup\n'
    r=subprocess.run(['sh','-c',code],capture_output=True,text=True);assert r.returncode==want,(name,r.stdout,r.stderr)
    expected=[]
    if storage_attempted:expected.append('storage-stop')
    if mounted_config:expected.append('umount /etc/default/muos-storage')
    if mounted_userdata:expected.append('umount /userdata')
    if mounted_data:expected.append('umount '+str(d/'data'))
    assert (calls.read_text().splitlines() if calls.exists() else [])==expected,name
    (d/'fixture.sh').write_text(code);cases.append(name)
report={'passed':True,'cases':cases,'hardware_accessed':False,'real_mounts_performed':False,
        'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),source]}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-storage-checks').write_text(str(stage)+'\n')
print('C43 storage guard/cleanup checks passed:',len(cases),stage)
