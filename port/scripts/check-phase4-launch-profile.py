#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C117 offline checks: strict timing receipts, current identity and check-only scope."""
import ast,json,os,subprocess,sys,tempfile
from pathlib import Path
import phase4_launch_profile as m
from phase4_backup_core import write_new,sync_dir

def main():
    os.umask(0o077);m.AREA.mkdir(mode=0o700,exist_ok=True);cases=[]
    def audit(event,args):
        if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            m.require('/port/roms/' not in os.fsdecode(args[0]),'No host ROM reads')
        if event=='socket.connect':raise AssertionError('No network')
        if event=='subprocess.Popen':m.require(args[1][:2]==['sh','-n'],'Shell syntax check only')
    sys.addaudithook(audit)
    def reject(name,fn):
        try:fn()
        except (ValueError,AssertionError,KeyError):cases.append(name)
        else:raise AssertionError(name)
    _,r=m.qualified();cases.append('C116-physical-technical-closure-and-frozen-source')
    fixture=[];tick=100
    for i in range(1,4):
        fixture+=['C77_INSTALLED_HOST_CORE_VALID files=40 operation=check',
                  'C77_PROVIDER_VALID files=7 operation=check','C77_PROVIDER_VALID files=7 operation=check']
        for phase in m.PHASES:
            fixture.append(f'C117_PHASE iteration={i} phase={phase} start={tick}.00 end={tick}.25');tick+=1
    fixture.append('C117_PROFILE_COMPLETE_NO_UI');text='\n'.join(fixture)+'\n'
    report=m.metrics(text);assert all(x['median_ms']==250 and len(x['samples_ms'])==3 for x in report.values())
    cases.append('nine-ordered-events-compute-three-independent-phase-samples')
    for name,bad in [
        ('missing-phase',text.replace(fixture[3]+'\n','')),
        ('duplicate-phase',text+fixture[3]+'\n'),
        ('wrong-iteration',text.replace('iteration=2','iteration=1')),
        ('unknown-phase',text.replace('phase=host_check','phase=unknown')),
        ('clock-backwards',text.replace('end=100.25','end=99.00')),
        ('phase-too-long',text.replace('end=100.25','end=999.00')),
        ('missing-completion',text.replace('C117_PROFILE_COMPLETE_NO_UI','')),
        ('malformed-extra-event',text+'C117_PHASE invalid\n'),
        ('incomplete-check',text.replace('files=40 operation=check','files=39 operation=check')),
        ('launch-receipt',text+'operation=launch\n')]:reject('refuse-'+name,lambda bad=bad:m.metrics(bad))
    for d in ['/run/muos-prefs-data.X;echo bad','/tmp/muos-prefs-data.123456','/run/muos-prefs-data.123456/../x']:
        reject('refuse-capsule-'+d,lambda d=d:m.profile_commands(d))
    d='/run/muos-prefs-data.Abc123';script=m.profile_commands(d)
    assert ' operation=launch' not in script and ' launch' not in script and 'run.once' in script
    assert '/mnt/mmc' not in script and '/dev/input' not in script and 'muxretro' not in script
    subprocess.run(['sh','-n'],input=script,text=True,check=True)
    cases.append('unmodified-check-only-invocations-no-UI-core-input-or-mount')
    boot=r['boot_sequence']+1;uid='00000000-0000-4000-8000-000000000117'
    guard=m.session.current_common('',0,boot,uid);validation=m.validation_commands(d,guard,boot,uid)
    assert validation.startswith(guard) and f'{boot} {uid} | cmp -s - {d}/caller-stage/boot' in validation
    assert guard.count(' | sha256sum -c - >/dev/null')==191
    assert 'C117_CURRENT_CAPSULE_VALID_NO_UI' in validation and '[ ! -e '+d+'/caller-stage/run.once ]' in validation
    subprocess.run(['sh','-n'],input=validation,text=True,check=True)
    cases.append('current-UUID-stage-with-original-191-plus-C114-assets-and-metadata-checks')
    paths=[Path(__file__),Path(m.__file__),m.REPO/'port/scripts/run-phase4-launch-profile.py',m.REPO/'port/scripts/package-phase4-launch-profile.py']
    for p in paths:ast.parse(p.read_text())
    stage=Path(tempfile.mkdtemp(prefix='checks.',dir=m.AREA))
    r={'passed':True,'schema':117,'case_count':len(cases),'cases':cases,'local_ROM_reads_prohibited':True,
       'network_device_GUI_core_or_reboot_executed':False,'source_sha256':{str(p.relative_to(m.REPO)):m.sha(p) for p in paths}}
    write_new(stage/'analysis.json',(json.dumps(r,indent=2)+'\n').encode());sync_dir(stage)
    (m.AREA/'latest-checks').write_text(str(stage)+'\n');sync_dir(m.AREA)
    print('C117',len(cases),'offline cases passed:',stage)
if __name__=='__main__':main()
