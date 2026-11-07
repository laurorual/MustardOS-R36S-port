#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C53 selective GB persistence; real writes limited to the owned save store."""
from pathlib import Path
import argparse,hashlib,io,json,ipaddress,re,subprocess,tarfile,tempfile
from phase4_candidate import sha,sums
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True,type=ipaddress.IPv4Address);p.add_argument('--mode',required=True,choices=['prepare','save','load']);p.add_argument('--boot',required=True,type=int);args=p.parse_args();assert 65 <= args.boot <= 999999
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'retro-session'
baseline=repo/'dist/phase4/muxretro-native-cpu'
for n,h in sums(baseline/'SHA256SUMS').items():assert sha(baseline/n)==h
common,infra=(baseline/'preflight.sh').read_text().split('for name in udevd',1);infra='for name in udevd'+infra
common=common.replace('= 65 ]', '= '+str(args.boot)+' ]')
area=work/'gb-core'
oldarea=work/'retro-session'
build=Path((work/'gb-exit/latest-host').read_text().strip());br=json.loads((build/'analysis.json').read_text());assert br['passed']
runner=Path((oldarea/'latest-runner').read_text().strip());rr=json.loads((runner/'analysis.json').read_text());assert rr['passed']
library=Path((work/'app-selection/latest-build').read_text().strip());lr=json.loads((library/'analysis.json').read_text());assert lr['passed']
checks=Path((work/'gb-exit/latest-checks').read_text().strip());cr=json.loads((checks/'analysis.json').read_text());assert cr['passed'] and cr['build_stage']==str(build)
for report in [br,rr,lr,cr]:
 for n,h in report['source_sha256'].items():assert sha(repo/n)==h
worker=repo/'port/device/rk-r35s-p0/app-selection/worker.sh'
parent_worker=repo/'port/device/rk-r35s-p0/launcher-cycle/worker.sh'
assert worker.read_text()==parent_worker.read_text().replace('"$dir/runner" 150','"$dir/runner" 210');cycle=repo/'port/device/rk-r35s-p0/gb-persist/session.sh'
# C45's unchanged worker/process-owner rollback is already qualified. Verify
# immutable receipts; do not replay services merely because the board rebooted.
proof=repo/'dist/phase4/launcher-retro-cycle'
for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h
for mode in ['prepare-failure','signal-test']:
 r=json.loads((proof/mode/'analysis.json').read_text())
 assert r['passed'] and r['cleanup_passed'] and r['worker_sha256']==sha(parent_worker) and r['runner_sha256']==rr['native_sha256']
extra=repo/'port/device/rk-r35s-p0/gb-persist'
adapter=repo/'port/device/rk-r35s-p0/app-selection/adapter.sh'
nes=Path((area/'latest').read_text().strip());nr=json.loads((nes/'analysis.json').read_text());assert nr['passed']
api=Path((area/'latest-api').read_text().strip());ar=json.loads((api/'analysis.json').read_text());assert ar['passed'] and ar['build_stage']==str(nes)
for report in [nr,ar]:
 for n,h in report['source_sha256'].items():assert sha(repo/n)==h
cycle=extra/'session.sh'
fixed=repo/'dist/phase4/native-app-selection/source'
for p in [worker,adapter]:assert sha(p)==sha(fixed/p.relative_to(repo))
rom=repo/'port/roms/gb/Super Mario Land (World) (Rev 1).gb'
assert rom.is_file() and not rom.is_symlink() and rom.stat().st_size==65536
subprocess.run(['git','check-ignore','--quiet',str(rom)],check=True)
nr['ROM_sha256']=ar['ROM_sha256'];assert sha(rom)==nr['ROM_sha256']
local_checks=Path((work/'gb-exit/latest-dispatch-checks').read_text().strip());lcr=json.loads((local_checks/'analysis.json').read_text());assert lcr['passed']
for n,h in lcr['source_sha256'].items():assert sha(repo/n)==h
dispatch_checks=local_checks
# The existing CPU/API and physical GB results are reused for unchanged assets.
previous=json.loads((Path((area/'latest-cycle').read_text().strip())/'analysis.json').read_text())
assert previous['passed'] and previous['cleanup_passed'] and previous['core_sha256']==nr['core_sha256'] and previous['ROM_sha256']==nr['ROM_sha256']
state_checks=Path((work/'gb-state/latest-checks').read_text().strip());scr=json.loads((state_checks/'analysis.json').read_text());assert scr['passed']
for n,h in scr['source_sha256'].items():assert sha(repo/n)==h
state_dispatch=Path((work/'gb-state/latest-dispatch-checks').read_text().strip());sdr=json.loads((state_dispatch/'analysis.json').read_text());assert sdr['passed']
for n,h in sdr['source_sha256'].items():assert sha(repo/n)==h
# Reuse C50's qualified deadline/exit for this exact unchanged executable.
for proof_mode in ['deadline','observe']:
 prior=json.loads((repo/'dist/phase4/gameboy-hotkey-exit'/proof_mode/'analysis.json').read_text())
 assert prior['passed'] and prior['cleanup_passed'] and prior['host_binary_sha256']==br['binary_sha256']
persist_checks=Path((work/'gb-persist/latest-checks').read_text().strip());pcr=json.loads((persist_checks/'analysis.json').read_text());assert pcr['passed']
for n,h in pcr['source_sha256'].items():assert sha(repo/n)==h
store_checks=Path((work/'save-store/latest-checks').read_text().strip());strr=json.loads((store_checks/'analysis.json').read_text());assert strr['passed']
for n,h in strr['source_sha256'].items():assert sha(repo/n)==h
identity=hashlib.sha256(b'MUOS-R35S-GB-SNAPSHOT-V1\0'+bytes.fromhex(nr['core_sha256'])+bytes.fromhex(nr['ROM_sha256'])).hexdigest()
if args.mode!='prepare':
 dependency=Path((work/'gb-persist'/('latest-prepare' if args.mode=='save' else 'latest-save')).read_text().strip())
 dpr=json.loads((dependency/'analysis.json').read_text())
 assert dpr['passed'] and dpr['cleanup_passed'] and dpr['private_identity']==identity and dpr['boot_sequence']==args.boot
files={'muxretro':build/'source/bin/muxretro','runner':runner/'muos-retro-runner','core.so':Path(nr['source_stage'])/'gambatte_libretro.so','lib/libmuxmod.so':library/'frontend-bin/lib/libmuxmod.so','cycle.sh':cycle,'adapter.sh':adapter,'app-launch.sh':extra/'app-launch.sh','private.gb':rom,'core-check':api/'check','select.sh':extra/'select.sh'}
expected={'muxretro':br['binary_sha256'],'runner':rr['native_sha256'],'core.so':nr['core_sha256'],'lib/libmuxmod.so':lr['binary_sha256'],'cycle.sh':sha(cycle),'adapter.sh':sha(adapter),'app-launch.sh':sha(extra/'app-launch.sh'),'private.gb':nr['ROM_sha256'],'core-check':sha(api/'check'),'select.sh':sha(extra/'select.sh')}
files['state-metadata']=state_checks/'state-metadata';expected['state-metadata']=scr['binary_sha256']
files.update({'save-store':store_checks/'muos-save-store','save-directory':persist_checks/'save-directory','store.sh':extra/'store.sh','prepare.sh':extra/'prepare.sh'})
expected.update({'save-store':strr['binary_sha256'],'save-directory':pcr['directory_binary_sha256'],'store.sh':sha(extra/'store.sh'),'prepare.sh':sha(extra/'prepare.sh')})
if args.mode=='prepare':
 keep={'runner','save-store','save-directory','store.sh','prepare.sh'}
 files={n:f for n,f in files.items() if n in keep};expected={n:h for n,h in expected.items() if n in keep}

for n,f in files.items():assert sha(f)==expected[n]
area=work/'gb-persist'
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
(stage/'intent.json').write_text(json.dumps({'private_identity':identity,'mode':args.mode,'boot_sequence':args.boot,'directory':directory,'binary_sha256':expected,'worker_sha256':sha(worker),'reboot':False,'rootfs_write':False},indent=2)+'\n')
remote('subdirs',common+f'mkdir -m 700 {directory}/lib\n')
for n,f in files.items():
 r=subprocess.run(ssh+['cat > '+directory+'/'+n],input=f.read_bytes(),capture_output=True,timeout=30);assert r.returncode==0
code=common+f"printf '%s\\n' {sha(extra/'app-launch.sh')} > {directory}/launcher.sha256\ncat > {directory}/worker.sh <<'C47_WORKER'\n"+worker.read_text()+'C47_WORKER\n'+f'mkdir -m 700 {directory}/state {directory}/owner {directory}/watchdog\n'
for n,f in {**files,'worker.sh':worker}.items():code+=f"chmod 700 {directory}/{n}\nprintf '%s  %s\\n' {sha(f)} {directory}/{n} | sha256sum -c -\n"
code+=f"printf '%s  %s\\n%s  %s\\n' {nr['core_sha256']} core.so {nr['ROM_sha256']} private.gb > {directory}/gb-assets.sha256\n"
code+=f"printf '%s\\n' {identity} > {directory}/identity\nprintf '%s\\n' {args.mode} > {directory}/role\n"
remote('prepare',code)
(stage/'dispatch.json').write_text(json.dumps({'dispatched':True,'mode':args.mode,'directory':directory})+'\n')
native_mode='observe'
entry=f'/bin/sh {directory}/prepare.sh {directory}' if args.mode=='prepare' else f'/bin/sh {directory}/worker.sh {directory} {native_mode}'
r=remote('native',common+f'cat /proc/1/mountinfo > {directory}/global-before.txt\n{directory}/runner 240 {directory}/watchdog /usr/libexec/muos-session/mount-namespace {entry}\n',timeout=255,required=False)
health=remote('postflight',common+infra,required=False)
assert health.returncode==0,('Inspect owned session; do not redispatch',stage,health.stderr)
assert health.stdout==before
remote('mount-health',common+f'cmp /proc/1/mountinfo {directory}/global-before.txt\necho C47_GLOBAL_MOUNTS_IDENTICAL\n')
names=['result.txt','done','manager','core.log','prepare.log','start.log','stop.log','restore.log','preferences-loaded.txt','preferences-active.txt','mixer-before.txt','mixer-after.txt','drm-before.txt','drm-after.txt','brightness-before.txt','brightness-after.txt','volume-before.sha256','volume-after.sha256','dispatch.log','return.log','game.log','dispatch-action.txt','return-action.txt','selected-application.txt','selected-action.txt','application-governor.txt','application-controller.txt','wireplumber-before.sha256','wireplumber-after.sha256','gb-api.log','performance.csv','state-metadata.txt','seed-metadata.txt','commit-metadata.txt','store-prepare.log','store-seed.log','store-commit.log','store-verify.log','store-initial.txt','store-seed-status.txt','store-export-status.txt','store-before-commit.txt','store-commit-status.txt','store-verify-status.txt','store-readonly-before.sha256','store-readonly-after.sha256']
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
screen=extra/'stopped-screen.sh'
remote('stopped-screen','set -- '+str(args.boot)+'\n'+screen.read_text())
log=(out/'core.log').read_text() if (out/'core.log').exists() else ''
game=(out/'game.log').read_text() if (out/'game.log').exists() else ''
if args.mode=='prepare':
 outcome='store-prepared' if passed and 'C53_PREPARE_COMPLETE' in log else 'failed'
else:
 match=re.search(r'^C50_EXIT reason=hotkey frames=([1-9][0-9]*)$',game,re.M)
 outcome=args.mode+'-returned' if passed and match and 'C53_CONTENT_COMPLETE' in log else 'failed'
 if passed:assert (out/'performance.csv').is_file()
 passed=passed and 'C53_STATE_CYCLE_COMPLETE' in log and re.fullmatch(r'C51_STATE_VALID version=1 core_bytes=[1-9][0-9]* core_crc_valid=1 manifest_valid=1 thumbnail_signature_valid=1 tmpfs=1\n',(out/'state-metadata.txt').read_text()) is not None
 if args.mode=='save':passed=passed and 'C53_COMMITTED current=1 source_tmpfs=1' in (out/'store-commit.log').read_text()
 if args.mode=='load':passed=passed and 'C53_SEEDED_FROM_EXT4 current=1' in (out/'store-seed.log').read_text() and 'C53_STORE_READONLY_BYTE_EXACT current=1' in (out/'store-verify.log').read_text()
passed=passed and outcome!='failed'
report={'passed':passed,'experiment':'C53_SELECTIVE_GB_PERSISTENCE','private_identity':identity,'mode':args.mode,'boot_sequence':args.boot,'native_exit':r.returncode,'worker_sha256':sha(worker),'runner_sha256':sha(runner/'muos-retro-runner'),'cleanup_passed':True,'global_mountinfo_unchanged':True,'preferences_persisted':False,'root_ro':True,'RAM_removed':True,'cycle_sha256':sha(cycle),'library_sha256':lr['binary_sha256'],'core_sha256':nr['core_sha256'],'ROM_sha256':nr['ROM_sha256'],'host_binary_sha256':br['binary_sha256'],'outcome':outcome,'private_content':True,'API_stage':str(api),'API_analysis_sha256':sha(api/'analysis.json'),'GB_checks_stage':str(local_checks),'GB_checks_sha256':sha(local_checks/'analysis.json'),'GB_dispatch_checks_stage':str(dispatch_checks),'GB_dispatch_checks_sha256':sha(dispatch_checks/'analysis.json'),'host_checks_stage':str(checks),'host_checks_sha256':sha(checks/'analysis.json'),'state_inspector_sha256':scr['binary_sha256'],'state_checks_stage':str(state_checks),'state_checks_analysis_sha256':sha(state_checks/'analysis.json'),'save_store_binary_sha256':strr['binary_sha256'],'directory_binary_sha256':pcr['directory_binary_sha256'],'integration_checks_stage':str(persist_checks),'integration_checks_analysis_sha256':sha(persist_checks/'analysis.json'),'source_sha256':{str(f.relative_to(repo)):sha(f) for f in [Path(__file__),worker,cycle,adapter,extra/'app-launch.sh',extra/'select.sh',extra/'store.sh',extra/'prepare.sh',screen]}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
assert passed,(stage,result,r.stderr)
(area/('latest-'+args.mode)).write_text(str(stage)+'\n');print('C53 selective persistence session collected:',args.mode,stage)

