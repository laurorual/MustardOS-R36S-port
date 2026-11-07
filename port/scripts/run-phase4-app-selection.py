#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C46 native application selection and fixed request adapter, RAM-only."""
from pathlib import Path
import argparse,io,json,ipaddress,re,subprocess,tarfile,tempfile
from phase4_candidate import sha,sums
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True,type=ipaddress.IPv4Address);p.add_argument('--mode',required=True,choices=['cycle','observe']);p.add_argument('--boot',required=True,type=int);args=p.parse_args();assert 65 <= args.boot <= 999999
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'retro-session'
baseline=repo/'dist/phase4/muxretro-native-cpu'
for n,h in sums(baseline/'SHA256SUMS').items():assert sha(baseline/n)==h
common,infra=(baseline/'preflight.sh').read_text().split('for name in udevd',1);infra='for name in udevd'+infra
common=common.replace('= 65 ]', '= '+str(args.boot)+' ]')
area=work/'app-selection'
oldarea=work/'retro-session'
build=Path((oldarea/'latest').read_text().strip());br=json.loads((build/'analysis.json').read_text());assert br['passed']
runner=Path((oldarea/'latest-runner').read_text().strip());rr=json.loads((runner/'analysis.json').read_text());assert rr['passed']
library=Path((area/'latest-build').read_text().strip());lr=json.loads((library/'analysis.json').read_text());assert lr['passed']
checks=Path((area/'latest-checks').read_text().strip());cr=json.loads((checks/'analysis.json').read_text());assert cr['passed'] and cr['build_stage']==str(library)
for report in [br,rr,lr,cr]:
 for n,h in report['source_sha256'].items():assert sha(repo/n)==h
worker=repo/'port/device/rk-r35s-p0/app-selection/worker.sh'
parent_worker=repo/'port/device/rk-r35s-p0/launcher-cycle/worker.sh'
assert worker.read_text()==parent_worker.read_text().replace('"$dir/runner" 150','"$dir/runner" 210');cycle=repo/'port/device/rk-r35s-p0/app-selection/select.sh'
# C45's unchanged worker/process-owner rollback is already qualified. Verify
# immutable receipts; do not replay services merely because the board rebooted.
proof=repo/'dist/phase4/launcher-retro-cycle'
for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h
for mode in ['prepare-failure','signal-test']:
 r=json.loads((proof/mode/'analysis.json').read_text())
 assert r['passed'] and r['cleanup_passed'] and r['worker_sha256']==sha(parent_worker) and r['runner_sha256']==rr['native_sha256']
if args.mode=='observe':
 old=Path((area/'latest-cycle').read_text().strip());r=json.loads((old/'analysis.json').read_text())
 assert r['passed'] and r['outcome']=='native-guards-only' and r['worker_sha256']==sha(worker) and r['cycle_sha256']==sha(cycle) and r['library_sha256']==lr['binary_sha256'] and r['boot_sequence']==args.boot
extra=repo/'port/device/rk-r35s-p0/app-selection'
smoke=Path((work/'libretro-smoke/latest').read_text().strip());sr=json.loads((smoke/'analysis.json').read_text());assert sr['passed']
files={'muxretro':build/'source/bin/muxretro','runner':runner/'muos-retro-runner','core.so':smoke/'r35s_smoke_libretro.so','lib/libmuxmod.so':library/'frontend-bin/lib/libmuxmod.so','cycle.sh':cycle,'adapter.sh':extra/'adapter.sh','app-launch.sh':extra/'app-launch.sh'}
expected={'muxretro':br['binary_sha256'],'runner':rr['native_sha256'],'core.so':sr['binary_sha256']['r35s_smoke_libretro.so'],'lib/libmuxmod.so':lr['binary_sha256'],'cycle.sh':sha(cycle),'adapter.sh':sha(extra/'adapter.sh'),'app-launch.sh':sha(extra/'app-launch.sh')}
for n,f in files.items():assert sha(f)==expected[n]
stage=Path(tempfile.mkdtemp(prefix=args.mode+'.',dir=area));(area/'latest-session-attempt').write_text(str(stage)+'\n')
ssh=['ssh','-p','2222','-i',str(work/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(work/'private/c07-known_hosts'),'-oBatchMode=yes','-oConnectTimeout=6','root@'+str(args.host)]
def remote(label,code,timeout=35,required=True):
 (stage/(label+'.sh')).write_text(code)
 r=subprocess.run(ssh+['sh -s'],input=code,capture_output=True,text=True,timeout=timeout)
 for e,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/(label+'.'+e)).write_text(v)
 if required:assert r.returncode==0,(stage,label,r.stdout[-2000:],r.stderr)
 return r
before=remote('preflight',common+infra).stdout
directory=remote('allocate',common+'''if [ ! -e /run/muos/session ] && [ ! -L /run/muos/session ];then mkdir -m 700 /run/muos/session;fi
[ -d /run/muos/session ] && [ ! -L /run/muos/session ] && [ "$(stat -c '%u:%g:%a' /run/muos/session)" = 0:0:700 ]
mktemp -d /run/muos-prefs-data.XXXXXX
''').stdout.strip()
assert re.fullmatch('/run/muos-prefs-data[.][a-zA-Z0-9]{6}',directory)
(stage/'intent.json').write_text(json.dumps({'mode':args.mode,'boot_sequence':args.boot,'directory':directory,'binary_sha256':expected,'worker_sha256':sha(worker),'reboot':False,'rootfs_write':False},indent=2)+'\n')
remote('subdirs',common+f'mkdir -m 700 {directory}/lib\n')
for n,f in files.items():
 r=subprocess.run(ssh+['cat > '+directory+'/'+n],input=f.read_bytes(),capture_output=True,timeout=30);assert r.returncode==0
code=common+f"printf '%s\\n' {sha(extra/'app-launch.sh')} > {directory}/launcher.sha256\ncat > {directory}/worker.sh <<'C46_WORKER'\n"+worker.read_text()+'C46_WORKER\n'+f'mkdir -m 700 {directory}/state {directory}/owner {directory}/watchdog\n'
for n,f in {**files,'worker.sh':worker}.items():code+=f"chmod 700 {directory}/{n}\nprintf '%s  %s\\n' {sha(f)} {directory}/{n} | sha256sum -c -\n"
remote('prepare',code)
(stage/'dispatch.json').write_text(json.dumps({'dispatched':True,'mode':args.mode,'directory':directory})+'\n')
r=remote('native',common+f'cat /proc/1/mountinfo > {directory}/global-before.txt\n{directory}/runner 240 {directory}/watchdog /usr/libexec/muos-session/mount-namespace /bin/sh {directory}/worker.sh {directory} {args.mode}\n',timeout=255,required=False)
health=remote('postflight',common+infra,required=False)
assert health.returncode==0,('Inspect owned session; do not redispatch',stage,health.stderr)
assert health.stdout==before
remote('mount-health',common+f'cmp /proc/1/mountinfo {directory}/global-before.txt\necho C46_GLOBAL_MOUNTS_IDENTICAL\n')
names=['result.txt','done','manager','core.log','prepare.log','start.log','stop.log','restore.log','preferences-loaded.txt','preferences-active.txt','mixer-before.txt','mixer-after.txt','drm-before.txt','drm-after.txt','brightness-before.txt','brightness-after.txt','volume-before.sha256','volume-after.sha256','dispatch.log','return.log','game.log','dispatch-action.txt','return-action.txt','selected-application.txt','selected-action.txt','application-governor.txt','application-controller.txt','wireplumber-before.sha256','wireplumber-after.sha256']
code=common+f'cd {directory}/state\nset --;for n in '+' '.join(names)+';do [ ! -f "$n" ] || set -- "$@" "$n";done\ntar -cf - "$@"\n'
raw=subprocess.run(ssh+['sh -s'],input=code.encode(),capture_output=True,timeout=35);assert raw.returncode==0
out=stage/'collected';out.mkdir()
with tarfile.open(fileobj=io.BytesIO(raw.stdout)) as archive:
 for m in archive.getmembers():
  assert m.isfile() and m.name in names and m.size<1048576
  (out/m.name).write_bytes(archive.extractfile(m).read())
result=dict(line.split('=',1) for line in (out/'result.txt').read_text().splitlines())
assert result['CLEANUP']=='0',result
want=0
passed=r.returncode==want and result['OPERATION']==str(want)
for stem,suffix in [('mixer','.txt'),('drm','.txt'),('volume','.sha256'),('wireplumber','.sha256')]:
 a=out/(stem+'-before'+suffix);b=out/(stem+'-after'+suffix)
 if a.exists():assert b.exists() and a.read_bytes()==b.read_bytes(),stem
cleanup=common+f'''for info in /proc/[0-9]*/mountinfo;do
 [ -r "$info" ] || continue
 if awk -v prefix={directory}/ '$5 ~ "^"prefix {{f=1}} END{{exit !f}}' "$info" 2>/dev/null;then exit 64;fi
done
[ ! -L {directory} ];[ "$(stat -c '%u:%g:%a' {directory})" = 0:0:700 ]
rm -rf {directory}
c25_ready
echo C46_RAM_REMOVED_ROOT_RO_FOUNDATION97_NETWORK_OK
'''
remote('cleanup',cleanup)
screen=extra/'stopped-screen.sh'
remote('stopped-screen','set -- '+str(args.boot)+'\n'+screen.read_text())
log=(out/'core.log').read_text()
if args.mode=='cycle':
 outcome='native-guards-only' if passed and 'C46_NATIVE_GUARDS_OK cases=6 no_ui=1 no_app_execution=1' in log else 'native-guards-failed'
elif 'C46_CANCELLED kind=cancel' in log:outcome='cancelled'
elif 'C46_CANCELLED kind=timeout' in log:outcome='timed-out'
elif 'C46_SELECTION_COMPLETE app_status=0' in log:outcome='selected-app-returned'
elif re.search(r'C46_SELECTION_COMPLETE app_status=[1-9]',log):outcome='app-failed-returned'
else:outcome='unexpected-exit'
report={'passed':passed,'mode':args.mode,'boot_sequence':args.boot,'native_exit':r.returncode,'worker_sha256':sha(worker),'runner_sha256':sha(runner/'muos-retro-runner'),'cleanup_passed':True,'global_mountinfo_unchanged':True,'preferences_persisted':False,'root_ro':True,'RAM_removed':True,'cycle_sha256':sha(cycle),'library_sha256':lr['binary_sha256'],'outcome':outcome,'host_checks_stage':str(checks),'host_checks_sha256':sha(checks/'analysis.json'),'source_sha256':{str(f.relative_to(repo)):sha(f) for f in [Path(__file__),worker,cycle,extra/'adapter.sh',extra/'app-launch.sh',screen]}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
assert passed,(stage,result,r.stderr)
(area/('latest-'+args.mode)).write_text(str(stage)+'\n');print('C46 native session collected:',args.mode,stage)

