#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C119 local real-contract adoption tests; no device/network/host-ROM input."""
import ast,hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
import phase4_batch_caller as m
from phase4_backup_core import write_new,sync_dir

def main():
    os.umask(0o077);m.AREA.mkdir(mode=0o700,exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='checks.',dir=m.AREA));cases=[]
    def audit(event,args):
        if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            m.require('/port/roms/' not in os.fsdecode(args[0]),'No host ROM reads')
        if event=='socket.connect':raise AssertionError('Network forbidden')
    sys.addaudithook(audit);m.qualified();data=m.bundle()
    original,block,_,_,rows=m.batch.original('host')
    restored=m.host_source().replace(m.batch.fragment(rows,'${root%/}',True),block).replace('C119_HOST_BATCH_VALID','C77_INSTALLED_HOST_CORE_VALID')
    assert restored==original and '/bin/sh "$capsule/frontend-libs.sh"' in m.host_source()
    cases.append('full-host-check-launch-provider-and-content-tail-preserved-except-batch-and-marker')
    for n,b in data.items():
        write_new(stage/n,b)
        if n.endswith('.sh'):subprocess.run(['sh','-n'],input=b,check=True)
    assert set(data)==set(m.NAMES) and len(data)==6 and json.loads(data['contract.json'])['run_enabled'] is False
    cases.append('six-source-only-files-no-ELF-ROM-and-run-disabled')
    d='/run/muos-prefs-data.Abc123';boot=84;uid='00000000-0000-4000-8000-000000000119'
    guard=m.session.current_common('',0,boot,uid)
    old=m.validation_commands(d,guard,boot,uid);adopted=m.adopted_validation(d,guard,boot,uid)
    assert old.startswith(guard) and adopted.startswith(guard)
    assert f'cmp {d}/contract-v2/host.sh {d}/installed-host.sh' in adopted
    assert f'{boot} {uid} | cmp -s - {d}/caller-stage/boot' in adopted
    for code in [old,adopted,m.upload_commands(d),m.refusal_commands(d),m.profile_commands(d)]:subprocess.run(['sh','-n'],input=code,text=True,check=True)
    ast.parse(m.rendered_runner());cases.append('fresh-boot-guard191-originals-before-adopt-new-host-after-and-source-upload-parse')
    plan={'bundle':{n:b.decode() for n,b in data.items()},'scripts':m.session.caller.SCRIPTS}
    write_new(stage/'fixture-plan.json',(json.dumps(plan,indent=2)+'\n').encode())
    rel=lambda p:'/work/'+str(p.relative_to(m.WORK))
    cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--cap-add=CHOWN',
         '--security-opt=no-new-privileges','--userns=keep-id:uid=0,gid=0','--user=0',
         '--tmpfs','/tmp:rw,nosuid,nodev,size=32m','--tmpfs','/run:rw,nosuid,nodev,size=32m',
         '-v',str(m.REPO/'port')+':/port:ro,z','-v',str(stage)+':'+rel(stage)+':rw,z',
         (m.WORK/'rootfs-container.iid').read_text().strip(),'python3','/port/diagnostics/phase4-batch-caller-fixture.py',rel(stage/'fixture-plan.json'),rel(stage)]
    r=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
    for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:write_new(stage/('fixture.'+n),v.encode())
    m.require(r.returncode==0,'C119 fixtures failed: '+str(stage))
    fixture=json.loads((stage/'fixture-results.json').read_text());assert fixture['passed'] and fixture['uid']==0;cases+=fixture['cases']
    text='C119_HOST_BATCH_VALID files=40 operation=check\nC77_PROVIDER_VALID files=7 operation=check\nC119_HOST_CHECK start=100.00 end=101.17\nC119_ADOPTED_CONTRACT_VERIFIED_NO_UI\n'
    assert m.metrics(text)['adopted_host_check_ms']==1170;cases.append('native-adopted-check-clock-and-witnesses')
    for bad in [text.replace('end=101.17','end=99.00'),text.replace('files=40','files=39'),text+'C119_HOST_CHECK start=100.00 end=101.17\n']:
        try:m.metrics(bad)
        except ValueError:cases.append('invalid-native-metric-refused')
        else:raise AssertionError('Invalid metric accepted')
    paths=[Path(__file__),Path(m.__file__),*m.NATIVE.glob('*.sh'),m.REPO/'port/diagnostics/phase4-batch-caller-fixture.py',
           m.REPO/'port/scripts/run-phase4-batch-caller.py',m.REPO/'port/scripts/package-phase4-batch-caller.py']
    for p in paths:
        if p.suffix=='.py':ast.parse(p.read_text())
    report={'passed':True,'schema':119,'case_count':len(cases),'cases':cases,'real_contract_cases':fixture['case_count'],
      'source_sha256':{str(p.relative_to(m.REPO)):m.sha(p) for p in paths},
      'bundle_sha256':{n:hashlib.sha256(b).hexdigest() for n,b in data.items()},'local_ROM_reads_prohibited':True,'device_or_GUI_executed':False}
    write_new(stage/'analysis.json',(json.dumps(report,indent=2)+'\n').encode());sync_dir(stage)
    (m.AREA/'latest-checks').write_text(str(stage)+'\n');sync_dir(m.AREA)
    print('C119',len(cases),'offline cases passed:',stage)
if __name__=='__main__':main()
