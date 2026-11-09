#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C120 real shell adoption/run-once contracts offline; no console/host-ROM input."""
import ast,hashlib,json,os,re,subprocess,sys,tempfile
from pathlib import Path
import phase4_batch_run as m
from phase4_backup_core import write_new,sync_dir

def main():
    os.umask(0o077);m.AREA.mkdir(mode=0o700,exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='checks.',dir=m.AREA));cases=[]
    def audit(event,args):
        if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            m.require('/port/roms/' not in os.fsdecode(args[0]),'Host ROM input forbidden')
        if event=='socket.connect':raise AssertionError('Network forbidden')
    sys.addaudithook(audit);m.qualified();data=m.bundle()
    for n,b in data.items():
        write_new(stage/n,b)
        if n.endswith('.sh'):subprocess.run(['sh','-n'],input=b,check=True)
    assert json.loads(data['contract.json'])['run_enabled'] is True and len(data)==6
    cases.append('version120-six-source-files-and-bounded-observe-only')
    # Exact original callback, including outer subreaper/namespace/installed worker.
    callback=re.search(r'^ run\) (.+) ;;$',data['caller.sh'].decode(),re.M)[1]
    old=(m.proof('manual-caller-installed')/'payload/caller.sh').read_text()
    assert callback in old
    cases.append('exec-argv-byte-exact-original-worker-namespace-and240s-bound')
    # Extend C119's real fixtures without editing their qualified source.
    fixture=(m.REPO/'port/diagnostics/phase4-batch-caller-fixture.py').read_text()
    fixture=fixture[:fixture.index("for args in [['run'")]
    fixture=fixture.replace('c119','c120').replace('C119','C120').replace('v2','v3')
    fixture=m.session.change(fixture,'. /port/device/rk-r35s-p0/batch-caller/functions.sh','. {out}/functions.sh')
    fixture=m.session.change(fixture,"    put(legacy/'assets.tsv',", "    put(cap/'runner',plan['runner'],0o700)\n    put(legacy/'assets.tsv',")
    fixture=m.session.change(fixture,' staged) return 0;;',' staged) return 0;;\n run) '+callback+' ;;')
    fixture+='''
reset();assert invoke('c120_adopt "$v3_cap"').returncode==0
r=invoke('c120_run "$v3_cap" observe');assert r.returncode==0,(r.stdout,r.stderr)
args=(cap/'run-dispatch').read_text().splitlines()
assert args==['240',str(cap/'watchdog'),'/usr/libexec/muos-session/mount-namespace','/bin/sh',str(legacy/'worker.sh'),str(cap),'observe']
assert (cap/'caller-v3-stage/run.once').is_dir() and (cap/'caller-v3-stage/run.once').stat().st_mode&0o777==0o700
before=snapshot();assert invoke('c120_run "$v3_cap" observe').returncode!=0 and before==snapshot()
cases.append('real-run-exec-exact-argv-and-second-dispatch-refused')
reset();before=snapshot();assert invoke('c120_run "$v3_cap" observe').returncode!=0 and before==snapshot();cases.append('run-before-adopt-refused')
for command in ['c120_run "$v3_cap" save','c120_run "$v3_cap"','c120_run "$v3_cap" observe extra','c120_run /run/muos-prefs-data.OTHER1 observe']:
 reset();assert invoke('c120_adopt "$v3_cap"').returncode==0;before=snapshot()
 assert invoke(command).returncode!=0 and before==snapshot() and not (cap/'run-dispatch').exists()
 cases.append('wrong-mode-arity-or-capsule-refused-before-claim')
for mode in ['boot','platform','host','asset','reservation']:
 reset();assert invoke('c120_adopt "$v3_cap"').returncode==0;extra=''
 if mode=='boot':extra='FIXTURE_BOOT=84'
 elif mode=='platform':extra='FAIL_PLATFORM=1'
 elif mode=='host':put(cap/'installed-host.sh','bad',0o700)
 elif mode=='asset':put(cap/'runner','bad',0o700)
 else:put(cap/'caller-stage/run.once/adopted-by-c120','bad',0o600)
 before=snapshot();assert invoke('c120_run "$v3_cap" observe',extra).returncode!=0 and before==snapshot()
 assert not (cap/'caller-v3-stage/run.once').exists();cases.append('run-refuses-invalid-'+mode+'-without-claim')
reset();assert invoke('c120_adopt "$v3_cap"').returncode==0
r=invoke('c120_run "$v3_cap" observe','export RUN_RC=74');assert r.returncode==74 and (cap/'caller-v3-stage/run.once').is_dir()
before=snapshot();assert invoke('c120_run "$v3_cap" observe').returncode!=0 and before==snapshot();cases.append('exec-failure-retains-once-no-redispatch')
(out/'fixture-results.json').write_text(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,'uid':os.getuid()},indent=2)+'\\n')
print('C120',len(cases),'real shell contract cases passed')
'''
    write_new(stage/'fixture.py',fixture.encode())
    runner='#!/bin/sh\nprintf "%s\\n" "$@" > /run/muos-prefs-data.ABC123/run-dispatch\nexit "${RUN_RC:-0}"\n'
    write_new(stage/'fixture-plan.json',(json.dumps({'bundle':{n:b.decode() for n,b in data.items()},'scripts':m.caller.SCRIPTS,'runner':runner},indent=2)+'\n').encode())
    rel=lambda p:'/work/'+str(p.relative_to(m.WORK))
    cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--cap-add=CHOWN',
      '--security-opt=no-new-privileges','--userns=keep-id:uid=0,gid=0','--user=0',
      '--tmpfs','/tmp:rw,nosuid,nodev,size=32m','--tmpfs','/run:rw,nosuid,nodev,size=32m',
      '-v',str(m.REPO/'port')+':/port:ro,z','-v',str(stage)+':'+rel(stage)+':rw,z',
      (m.WORK/'rootfs-container.iid').read_text().strip(),'python3',rel(stage/'fixture.py'),rel(stage/'fixture-plan.json'),rel(stage)]
    r=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
    for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:write_new(stage/('fixture.'+n),v.encode())
    m.require(r.returncode==0,'C120 fixtures failed: '+str(stage))
    fixture_result=json.loads((stage/'fixture-results.json').read_text());assert fixture_result['passed'];cases+=fixture_result['cases']
    _,_,_,_,_,online=m.historical();ast.parse(m.render_online(online));ast.parse(m.rendered_runner())
    cases.append('graphical-harness-new-entry-stage-host-witness-and-zero-input-routing-parse')
    d='/run/muos-prefs-data.Abc123'
    guard=m.current_common('',0,84,'00000000-0000-4000-8000-000000000120')
    for code in [m.upload_commands(d),m.bundle_guard(d),m.validation_commands(d,guard,84,'00000000-0000-4000-8000-000000000120'),
                 m.adopted_validation(d,guard,84,'00000000-0000-4000-8000-000000000120'),m.refusal_commands(d),m.profile_commands(d)]:
        subprocess.run(['sh','-n'],input=code,text=True,check=True)
    ast.parse(m.native_runner())
    cases.append('bounded-source-upload-and-exact-bundle-guard-parse')
    paths=[Path(__file__),Path(m.__file__),m.REPO/'port/scripts/run-phase4-batch-run.py',
      m.REPO/'port/scripts/check-native-phase4-batch-run.py',m.REPO/'port/scripts/package-phase4-batch-run.py']
    report={'passed':True,'schema':120,'case_count':len(cases),'cases':cases,'real_contract_cases':fixture_result['case_count'],
      'bundle_sha256':{n:hashlib.sha256(b).hexdigest() for n,b in data.items()},
      'source_sha256':{str(p.relative_to(m.REPO)):m.sha(p) for p in paths},'device_or_GUI_executed':False,'local_ROM_reads_prohibited':True}
    write_new(stage/'analysis.json',(json.dumps(report,indent=2)+'\n').encode());sync_dir(stage)
    (m.AREA/'latest-checks').write_text(str(stage)+'\n');sync_dir(m.AREA)
    print('C120',len(cases),'offline cases passed:',stage)
if __name__=='__main__':main()
