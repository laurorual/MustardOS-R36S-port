#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Real process tests: deadlines, signals, escaped descendants and state guards."""
from pathlib import Path
import json,os,signal,subprocess,tempfile,time
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/retro-session'
build=Path((area/'latest-runner').read_text().strip());report=json.loads((build/'analysis.json').read_text());assert report['passed']
for n,h in report['source_sha256'].items():assert sha(repo/n)==h
binary=build/'runner-host';stage=Path(tempfile.mkdtemp(prefix='runner-checks.',dir=area));cases=[]
def run(name,args,expected=0,seconds=3,mode=0o700):
 d=stage/name;d.mkdir(mode=mode)
 r=subprocess.run([str(binary),str(seconds),str(d),*args],capture_output=True,text=True,timeout=10)
 assert r.returncode==expected,(name,r.stdout,r.stderr)
 if expected!=125:assert 'CLEAN=1' in r.stdout
 (d/'stdout').write_text(r.stdout);cases.append(name);return d
run('normal',['/bin/true'])
run('child_failure',['/bin/false'],1)
run('timeout',['/bin/sleep','30'],124,1)
run('wrong_mode',['/bin/true'],125,mode=0o755)
run('zero_deadline',['/bin/true'],125,seconds=0)
run('relative_command',['true'],125)
for name,escape in [('descendant',False),('escaped_session',True)]:
 d=stage/name;d.mkdir(mode=0o700);pidfile=d/'descendant.pid'
 command=('setsid ' if escape else '')+'/bin/sleep 30 & echo $! > "'+str(pidfile)+'"; exit 0'
 r=subprocess.run([str(binary),'3',str(d),'/bin/sh','-c',command],capture_output=True,text=True,timeout=10)
 assert r.returncode==0 and 'CLEAN=1' in r.stdout,(name,r.stdout,r.stderr)
 pid=int(pidfile.read_text());assert not Path('/proc',str(pid)).exists(),(name,pid)
 cases.append(name)
d=stage/'signal';d.mkdir(mode=0o700)
p=subprocess.Popen([str(binary),'30',str(d),'/bin/sleep','30'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
deadline=time.monotonic()+3
while not (d/'child.pid').exists():
 assert time.monotonic()<deadline;time.sleep(.02)
pid=int((d/'child.pid').read_text().split()[0]);p.send_signal(signal.SIGTERM);stdout,stderr=p.communicate(timeout=6)
assert p.returncode==143 and 'CLEAN=1' in stdout,(stdout,stderr)
assert not Path('/proc',str(pid)).exists();cases.append('signal_cleanup')
r=subprocess.run([str(binary),'1',str(d),'/bin/true'],capture_output=True,text=True)
assert r.returncode==125;cases.append('duplicate_state_refused')
report={'passed':True,'cases':cases,'real_process_groups_and_subreaper_tested':True,'device_accessed':False,
        'runner_build_stage':str(build),'native_sha256':sha(build/'muos-retro-runner'),
        'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/utils/muos-retro-runner.c']}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-runner-checks').write_text(str(stage)+'\n')
print('C44 real runner tests passed:',len(cases),stage)
