#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Exercise C06 partial-bind cleanup/atomic config saves without real mounts/audio."""
from pathlib import Path
import json,os,subprocess,sys,tempfile

repo=Path(__file__).resolve().parents[2]
stage=Path(sys.argv[1]).resolve()
source=(repo/'port/device/rk-r35s-p0/frontend-audio-diagnostic/session.sh').read_text()
results={}
scenarios=[(mode,adjusted,case) for mode,adjusted,count in [('0','0',7),('0','1',8),('1','0',10)] for case in ['success',*[f'mount-{i}' for i in range(1,count+1)],'audio-stop-failure']]
for mode,adjusted,case in scenarios:
    f=Path(tempfile.mkdtemp(prefix='hooks-'+mode+adjusted+'-'+case+'.',dir=stage));root=f/'root';state=f/'state';state.mkdir();binpath=f/'bin';binpath.mkdir()
    initial={
      'opt/muos/device/config/audio/path':'SPK\n','opt/muos/config/settings/general/volume':'35\n',
      'opt/muos/config/settings/general/sound':'0\n','opt/muos/config/system/debug_mode':'1\n',
      'opt/muos/config/settings/advanced/volume':'2\n',
      'opt/muos/config/settings/power/idle_display':'0\n','opt/muos/config/settings/power/idle_sleep':'0\n',
      'opt/muos/device/control/asound.state':'original-profile\n','etc/default/muos-core':'audio=0\ninput=1\n',
      'etc/default/muos-ui':'enabled=0\nhotkeys=0\n',
      'opt/muos/share/theme/MustardOS/sound/confirm.wav':'known-confirm\n',
      'opt/muos/share/theme/MustardOS/sound/back.wav':'original-back\n',
      'opt/muos/share/theme/MustardOS/sound/navigate.wav':'original-navigate\n',
      'usr/share/muos-diagnostic/c06-control-tone.wav':'known-control-tone\n',
      'usr/share/muos-diagnostic/c06-navigate-normalized.wav':'known-normalized-wave\n',
      'opt/muos/share/theme/MustardOS/sound/info_open.wav':'original-open\n',
      'opt/muos/share/theme/MustardOS/sound/info_close.wav':'original-close\n'}
    for name,text in initial.items():
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    # Relocate fixed paths only in the fixture copy. The actual shell policy
    # runs unchanged otherwise; fake binds retain atomic-rename behavior.
    local=source
    for prefix in ['/opt/muos','/usr/libexec','/usr/share/muos-diagnostic','/etc/default','/etc/init.d']:
        local=local.replace(prefix,str(root)+prefix)
    (f/'session.sh').write_text(local)
    command=r'''#!/usr/bin/env python3
from pathlib import Path
import json,os,sys
f=Path(os.environ['FIXTURE']);root=f/'root';case=os.environ['CASE'];name=Path(sys.argv[0]).name;a=sys.argv[1:]
if name=='mount':
 p=f/'mount-count';n=int(p.read_text())+1 if p.exists() else 1;p.write_text(str(n))
 if case=='mount-'+str(n):sys.exit(1)
 src,dst=map(Path,a[-2:]);backup=Path(str(dst)+'.fixture-original')
 assert not backup.exists() and not dst.is_symlink()
 dst.rename(backup);dst.symlink_to(src,target_is_directory=src.is_dir())
elif name=='umount':
 dst=Path(a[-1]);backup=Path(str(dst)+'.fixture-original')
 assert dst.is_symlink() and backup.exists(),str(dst)
 dst.unlink();backup.rename(dst)
elif name=='pidof':sys.exit(1)
elif name=='alsactl':
 if a[-1]=='store':Path(a[a.index('-f')+1]).write_text('fixture-alsa\n')
elif name=='amixer':print('fixture mixer contents')
elif name=='muos-ui-supervisor':sys.exit(3)
elif name=='S80pipewire.sh':sys.exit(1 if case=='audio-stop-failure' else 0)
elif name=='S99muos-ui':pass
elif name=='muvarctl':
 if a[0]=='get':
  directory=root/('opt/muos/device/config' if a[1]=='device' else 'opt/muos/config')
  print((directory/a[2]).read_text().strip(),end='')
'''
    for name in ['mount','umount','pidof','alsactl','amixer']:
        p=binpath/name;p.write_text(command);p.chmod(0o755)
    for name in ['usr/libexec/muos-ui-supervisor','etc/init.d/S99muos-ui','opt/muos/script/init/S80pipewire.sh','opt/muos/frontend/muvarctl']:
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(command);p.chmod(0o755)
    p=root/'usr/libexec/muos-run-bounded';p.write_text('#!/bin/sh\nshift\nexec "$@"\n');p.chmod(0o755)
    test=r'''. "$FIXTURE/session.sh"
state=$FIXTURE/state
c06_control_effects=$CONTROL_MODE
c06_nav_adjusted=$NAV_ADJUSTED
c06_before_core
setup=$?
if [ "$setup" = 0 ]; then c06_help_start; setup=$?; fi
if [ "$setup" = 0 ]; then
 printf 'enabled=1\nhotkeys=0\n' > "$state/ui.conf"
 mount --bind "$state/ui.conf" "$ROOT/etc/default/muos-ui"
 setup=$?
 [ "$setup" != 0 ] || ui_config_bound=1
fi
if [ "$setup" = 0 ]; then
 # Model the native atomic file save while directory binds are active.
 printf '42\n' > "$ROOT/opt/muos/config/settings/general/volume.tmp"
 mv "$ROOT/opt/muos/config/settings/general/volume.tmp" "$ROOT/opt/muos/config/settings/general/volume"
 printf 'HP\n' > "$ROOT/opt/muos/device/config/audio/path.tmp"
 mv "$ROOT/opt/muos/device/config/audio/path.tmp" "$ROOT/opt/muos/device/config/audio/path"
fi
printf '%s\n' "$setup" > "$FIXTURE/setup-status"
c06_audio_cleanup
rc=$?
echo "$rc" > "$FIXTURE/cleanup-status"
exit "$rc"
'''
    x=subprocess.run(['sh','-c',test],env={**os.environ,'PATH':str(binpath)+':'+os.environ['PATH'],'CASE':case,'CONTROL_MODE':mode,'NAV_ADJUSTED':adjusted,'FIXTURE':str(f),'ROOT':str(root)},capture_output=True,text=True)
    (f/'stdout').write_text(x.stdout);(f/'stderr').write_text(x.stderr)
    assert x.returncode==(1 if case=='audio-stop-failure' else 0),(case,x.stdout,x.stderr)
    assert int((f/'setup-status').read_text())==(1 if case.startswith('mount-') else 0),case
    assert not list(root.rglob('*.fixture-original')),case
    for name,text in initial.items():assert (root/name).read_text()==text,(case,name)
    assert 'C06_RESTORED_CACHE_PATH=SPK' in (state/'cache-restored.txt').read_text()
    assert 'C06_RESTORED_CACHE_VOLUME=35' in (state/'cache-restored.txt').read_text()
    assert 'C06_RESTORED_CACHE_BOOT_VOLUME=2' in (state/'cache-restored.txt').read_text()
    results[mode+adjusted+'-'+case]={'expected_outcome_passed':True,'control_effects':mode=='1','navigation_adjusted':adjusted=='1','cleanup_exit':x.returncode,'all_original_config_profile_waves_preserved':True,'simulated_binds_released':True,'real_mounts_devices_or_seed_accessed':False}
(stage/'hook-fixtures.json').write_text(json.dumps(results,indent=2)+'\n')
print('C06 hook fixtures passed:',len(results))
