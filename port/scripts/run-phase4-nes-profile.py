#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C48 automated NES profiling, existing C47 core/content and C46 cleanup."""
from pathlib import Path
import argparse,io,json,ipaddress,re,subprocess,tarfile,tempfile
from phase4_candidate import sha,sums
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True,type=ipaddress.IPv4Address);p.add_argument('--mode',required=True,choices=['profile','observe']);p.add_argument('--boot',required=True,type=int);p.add_argument('--profile-host',type=Path);p.add_argument('--core-build',type=Path);args=p.parse_args();assert 65 <= args.boot <= 999999
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'retro-session'
baseline=repo/'dist/phase4/muxretro-native-cpu'
for n,h in sums(baseline/'SHA256SUMS').items():assert sha(baseline/n)==h
common,infra=(baseline/'preflight.sh').read_text().split('for name in udevd',1);infra='for name in udevd'+infra
common=common.replace('= 65 ]', '= '+str(args.boot)+' ]')
area=work/'nes-core'
oldarea=work/'retro-session'
build=Path((area/'latest-host').read_text().strip());br=json.loads((build/'analysis.json').read_text());assert br['passed']
runner=Path((oldarea/'latest-runner').read_text().strip());rr=json.loads((runner/'analysis.json').read_text());assert rr['passed']
library=Path((work/'app-selection/latest-build').read_text().strip());lr=json.loads((library/'analysis.json').read_text());assert lr['passed']
checks=Path((area/'latest-checks').read_text().strip());cr=json.loads((checks/'analysis.json').read_text());assert cr['passed'] and cr['build_stage']==str(build)
for report in [br,rr,lr,cr]:
 for n,h in report['source_sha256'].items():assert sha(repo/n)==h
worker=repo/'port/device/rk-r35s-p0/app-selection/worker.sh'
parent_worker=repo/'port/device/rk-r35s-p0/launcher-cycle/worker.sh'
assert worker.read_text()==parent_worker.read_text().replace('"$dir/runner" 150','"$dir/runner" 210');cycle=repo/'port/device/rk-r35s-p0/nes-profile/profile.sh'
# C45's unchanged worker/process-owner rollback is already qualified. Verify
# immutable receipts; do not replay services merely because the board rebooted.
proof=repo/'dist/phase4/launcher-retro-cycle'
for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h
for mode in ['prepare-failure','signal-test']:
 r=json.loads((proof/mode/'analysis.json').read_text())
 assert r['passed'] and r['cleanup_passed'] and r['worker_sha256']==sha(parent_worker) and r['runner_sha256']==rr['native_sha256']
extra=repo/'port/device/rk-r35s-p0/nes-core'
profile=repo/'port/device/rk-r35s-p0/nes-profile'
adapter=repo/'port/device/rk-r35s-p0/app-selection/adapter.sh'
nes=Path((area/'latest').read_text().strip());nr=json.loads((nes/'analysis.json').read_text());assert nr['passed']
api=Path((area/'latest-api').read_text().strip());ar=json.loads((api/'analysis.json').read_text());assert ar['passed'] and ar['build_stage']==str(nes)
for report in [nr,ar]:
 for n,h in report['source_sha256'].items():assert sha(repo/n)==h
if args.core_build:
 parent=nes;parent_core=nr
 nes=args.core_build.resolve();nr=json.loads((nes/'analysis.json').read_text())
 assert nr['passed'] and nr['API_passed'] and nr['parent_core_stage']==str(parent)
 assert nr['ROM_sha256']==parent_core['ROM_sha256'] and nr['parent_core_sha256']==parent_core['core_sha256']
 for n,h in nr['source_sha256'].items():assert sha(repo/n)==h
cycle=profile/'profile.sh'
fixed=repo/'dist/phase4/native-app-selection/source'
for p in [worker,adapter]:assert sha(p)==sha(fixed/p.relative_to(repo))
# A new host must prove its unchanged C47 parent and pass its own loader checks.
if args.profile_host:
 parent=build;parent_report=br
 build=args.profile_host.resolve();br=json.loads((build/'analysis.json').read_text())
 assert br['passed'] and br['parent_stage']==str(parent) and br['loader_checked']
 for n,h in br['source_sha256'].items():assert sha(repo/n)==h
 assert sha(parent/'source/bin/muxretro')==parent_report['binary_sha256']
if args.mode=='observe':
 previous_stage=Path((work/'nes-profile/latest-profile').read_text().strip())
 previous=json.loads((previous_stage/'analysis.json').read_text())
 measured=json.loads((previous_stage/'performance-analysis.json').read_text())
 assert previous['passed'] and previous['cleanup_passed'] and previous['boot_sequence']==args.boot
 assert previous['core_sha256']==nr['core_sha256'] and previous['ROM_sha256']==nr['ROM_sha256']
 assert previous['host_binary_sha256']==br['binary_sha256'] and measured['approximate_frames_per_second']>=59
files={'muxretro':build/'source/bin/muxretro','runner':runner/'muos-retro-runner','core.so':Path(nr['source_stage'])/'fceumm_libretro.so','lib/libmuxmod.so':library/'frontend-bin/lib/libmuxmod.so','cycle.sh':cycle,'adapter.sh':adapter,'app-launch.sh':extra/'app-launch.sh','r35s-flight.nes':nes/'r35s-flight.nes','core-check':api/'check'}
expected={'muxretro':br['binary_sha256'],'runner':rr['native_sha256'],'core.so':nr['core_sha256'],'lib/libmuxmod.so':lr['binary_sha256'],'cycle.sh':sha(cycle),'adapter.sh':sha(adapter),'app-launch.sh':sha(extra/'app-launch.sh'),'r35s-flight.nes':nr['ROM_sha256'],'core-check':sha(api/'check')}
if args.mode=='observe':
 files['select.sh']=extra/'select.sh';expected['select.sh']=sha(extra/'select.sh')
for n,f in files.items():assert sha(f)==expected[n]
area=work/'nes-profile';area.mkdir(exist_ok=True)
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
code=common+f"printf '%s\\n' {sha(extra/'app-launch.sh')} > {directory}/launcher.sha256\ncat > {directory}/worker.sh <<'C47_WORKER'\n"+worker.read_text()+'C47_WORKER\n'+f'mkdir -m 700 {directory}/state {directory}/owner {directory}/watchdog\n'
for n,f in {**files,'worker.sh':worker}.items():code+=f"chmod 700 {directory}/{n}\nprintf '%s  %s\\n' {sha(f)} {directory}/{n} | sha256sum -c -\n"
code+=f"printf '%s  %s\\n%s  %s\\n' {nr['core_sha256']} core.so {nr['ROM_sha256']} r35s-flight.nes > {directory}/nes-assets.sha256\n"
if args.mode=='observe':code+=f"printf 'C48_PHYSICAL\\n' > {directory}/physical.once\nchmod 600 {directory}/physical.once\n"
remote('prepare',code)
(stage/'dispatch.json').write_text(json.dumps({'dispatched':True,'mode':args.mode,'directory':directory})+'\n')
r=remote('native',common+f'cat /proc/1/mountinfo > {directory}/global-before.txt\n{directory}/runner 240 {directory}/watchdog /usr/libexec/muos-session/mount-namespace /bin/sh {directory}/worker.sh {directory} observe\n',timeout=255,required=False)
health=remote('postflight',common+infra,required=False)
assert health.returncode==0,('Inspect owned session; do not redispatch',stage,health.stderr)
assert health.stdout==before
remote('mount-health',common+f'cmp /proc/1/mountinfo {directory}/global-before.txt\necho C47_GLOBAL_MOUNTS_IDENTICAL\n')
names=['result.txt','done','manager','core.log','prepare.log','start.log','stop.log','restore.log','preferences-loaded.txt','preferences-active.txt','mixer-before.txt','mixer-after.txt','drm-before.txt','drm-after.txt','brightness-before.txt','brightness-after.txt','volume-before.sha256','volume-after.sha256','dispatch.log','return.log','game.log','dispatch-action.txt','return-action.txt','selected-application.txt','selected-action.txt','application-governor.txt','application-controller.txt','wireplumber-before.sha256','wireplumber-after.sha256','nes-api.log','performance.csv']
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
echo C47_RAM_REMOVED_ROOT_RO_FOUNDATION97_NETWORK_OK
'''
remote('cleanup',cleanup)
screen=profile/'stopped-screen.sh'
remote('stopped-screen','set -- '+str(args.boot)+'\n'+screen.read_text())
log=(out/'core.log').read_text()
outcome='profile-complete' if passed and 'C48_PROFILE_COMPLETE' in log else 'profile-failed'
assert outcome=='profile-complete'
assert (out/'performance.csv').is_file()
report={'passed':passed,'experiment':'C48_NES_PROFILE','mode':args.mode,'boot_sequence':args.boot,'native_exit':r.returncode,'worker_sha256':sha(worker),'runner_sha256':sha(runner/'muos-retro-runner'),'cleanup_passed':True,'global_mountinfo_unchanged':True,'preferences_persisted':False,'root_ro':True,'RAM_removed':True,'cycle_sha256':sha(cycle),'library_sha256':lr['binary_sha256'],'core_sha256':nr['core_sha256'],'ROM_sha256':nr['ROM_sha256'],'host_binary_sha256':br['binary_sha256'],'outcome':outcome,'host_checks_stage':str(checks),'host_checks_sha256':sha(checks/'analysis.json'),'source_sha256':{str(f.relative_to(repo)):sha(f) for f in [Path(__file__),worker,cycle,adapter,extra/'app-launch.sh',screen]}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
assert passed,(stage,result,r.stderr)
(area/('latest-'+args.mode)).write_text(str(stage)+'\n');print('C48 profile collected:',args.mode,stage)

