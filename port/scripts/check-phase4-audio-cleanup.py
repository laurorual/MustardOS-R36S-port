#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Exercise actual C05 hooks with fake mount/ALSA commands, no hardware access."""
from pathlib import Path
import json,os,subprocess,sys,tempfile
r=Path(__file__).resolve().parents[2];out=Path(sys.argv[1]).resolve();source=(r/'port/device/rk-r35s-p0/audio-diagnostic/session.sh').read_text();results={}
for case in ['success','second-bind-fails']:
 f=Path(tempfile.mkdtemp(prefix='cleanup-'+case+'.',dir=out));binpath=f/'bin';binpath.mkdir();(f/'state').mkdir();(f/'profile').write_text('profile fixture\n');(f/'core.conf').write_text('audio=0\ninput=1\n')
 script='''#!/bin/sh
name=${0##*/}
echo "$name $*" >> "$FIXTURE/calls"
case "$name" in
 bounded) shift; exec "$@" ;;
 mount) if [ "$CASE" = second-bind-fails ] && [ "$3" = "$FIXTURE/core.conf" ]; then exit 1; fi ;;
 alsactl) if [ "$4" = store ]; then echo fixture > "$3"; fi ;;
 amixer) echo 'controls fixture' ;;
 pidof) exit 1 ;;
 s80|umount) : ;;
esac
'''
 for n in ['bounded','mount','umount','alsactl','amixer','pidof','s80']:(binpath/n).write_text(script);(binpath/n).chmod(0o755)
 text=source.replace('/usr/libexec/muos-run-bounded',str(binpath/'bounded')).replace('/opt/muos/script/init/S80pipewire.sh',str(binpath/'s80')).replace('/opt/muos/device/control/asound.state',str(f/'profile')).replace('/etc/default/muos-core',str(f/'core.conf'))
 test=text+'\nstate=$FIXTURE/state;core_bound=0;asound_bound=0\nc05_before_core\nstart=$?\nc05_audio_cleanup\nclean=$?\nprintf "start=%s clean=%s\\n" "$start" "$clean"\n'
 x=subprocess.run(['sh','-c',test],env={**os.environ,'PATH':str(binpath)+':'+os.environ['PATH'],'CASE':case,'FIXTURE':str(f)},capture_output=True,text=True)
 expected='start=0 clean=0' if case=='success' else 'start=1 clean=0'
 assert expected in x.stdout,(case,x.stdout,x.stderr)
 calls=(f/'calls').read_text();assert calls.count('umount ')==(2 if case=='success' else 1),calls
 assert (f/'profile').read_text()=='profile fixture\n'
 assert 'alsa-before.state restore' in calls and 'amixer -c 0 contents' in calls
 results[case]={'expected_outcome_passed':True,'result':expected,'temporary_binds_cleanup_observed':True}
(out/'cleanup-fixtures.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
