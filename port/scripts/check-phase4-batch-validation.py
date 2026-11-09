#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C118 finite adapters and real metadata/hash equivalence in a rootless container."""
import ast,hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
import phase4_batch_validation as m
from phase4_backup_core import write_new,sync_dir

def main():
    os.umask(0o077);m.AREA.mkdir(mode=0o700,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='checks.',dir=m.AREA));cases=[]
    def audit(event,args):
        if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            m.require('/port/roms/' not in os.fsdecode(args[0]),'No host ROM input')
        if event=='socket.connect':raise AssertionError('No network')
    sys.addaudithook(audit);m.qualified();cases.append('frozen-C116-C117-source-proof-and-native-profile')
    plan={}
    for kind in ['host','provider']:
        original,block,header,tag,rows=m.original(kind)
        files=[];fake=[]
        for i,(_,mode,n) in enumerate(rows):
            content='' if i==0 else 'C118 fixture '+n
            files.append({'name':n,'mode':mode,'content':content})
            fake.append((hashlib.sha256(content.encode()).hexdigest(),mode,n))
        prefix=''
        if kind=='provider':prefix=original[original.index('for path in "$capsule"'):original.index('while read -r digest')]
        fields='\n'.join(h+' '+(format(mode,'o')+' ' if kind=='host' else '')+n for h,mode,n in fake)
        old=prefix+header+"done <<'"+tag+"'\n"+fields+'\n'+tag+'\n'
        fragment=m.fragment(fake,'${root%/}' if kind=='host' else '$capsule',kind=='host')
        batch=prefix+fragment
        plan[kind]={'files':files,'original':old,'batch':batch}
        script=m.rendered(kind);subprocess.run(['sh','-n'],input=script,text=True,check=True)
        refused=subprocess.run(['sh','-c',script,'C118','/run/muos-prefs-data.ABC123','launch'],capture_output=True,text=True)
        assert refused.returncode==64
        cases.append(kind+'-prototype-refuses-launch-before-device-access')
        assert original.count(block)==1 and fragment.count('sha256sum -c -')==1 and fragment.count('stat -c')==1
        restored=script.replace(m.fragment(rows,'${root%/}' if kind=='host' else '$capsule',kind=='host'),block)
        restored=restored.replace('check:2)','check:2|launch:2)')
        restored=restored.replace('C118_BATCH_HOST_VALID','C77_INSTALLED_HOST_CORE_VALID').replace('C118_BATCH_PROVIDER_VALID','C77_PROVIDER_VALID')
        restored=restored.replace('/bin/sh "$capsule/batch-provider.sh"','/bin/sh "$capsule/frontend-libs.sh"')
        assert restored==original
        cases.append(kind+'-one-stat-one-SHA-and-original-header-retained')
        write_new(stage/(kind+'.sh'),script.encode())
    for label,rows in [('duplicate',[('0'*64,0o644,'x')]*2),('escape',[('0'*64,0o644,'../x')]),
                       ('path-injection',[('0'*64,0o644,'x;echo')]),('bad-mode',[('0'*64,0o777,'x')]),('bad-digest',[('bad',0o644,'x')])]:
        try:m.fragment(rows,'${root%/}',True)
        except ValueError:cases.append('refuse-model-'+label)
        else:raise AssertionError(label)
    write_new(stage/'fixture-plan.json',(json.dumps(plan,indent=2)+'\n').encode())
    rel=lambda p:'/work/'+str(p.relative_to(m.WORK))
    cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--cap-add=CHOWN',
         '--security-opt=no-new-privileges','--userns=keep-id:uid=0,gid=0','--user=0',
         '--tmpfs','/tmp:rw,nosuid,nodev,size=32m','--tmpfs','/run:rw,nosuid,nodev,size=16m',
         '-v',str(m.REPO/'port')+':/port:ro,z','-v',str(stage)+':'+rel(stage)+':rw,z',
         (m.WORK/'rootfs-container.iid').read_text().strip(),'python3','/port/diagnostics/phase4-batch-fixture.py',rel(stage/'fixture-plan.json'),rel(stage)]
    result=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
    for n,v in [('stdout',result.stdout),('stderr',result.stderr),('exit',str(result.returncode)+'\n')]:write_new(stage/('fixture.'+n),v.encode())
    m.require(result.returncode==0,'C118 fixture failed; inspect '+str(stage))
    fixture=json.loads((stage/'fixture-results.json').read_text());assert fixture['passed'] and fixture['real_container_uid']==0
    cases+=fixture['cases']
    events=[];tick=100
    for i in range(1,4):
        events+=['C77_INSTALLED_HOST_CORE_VALID files=40 operation=check','C118_BATCH_HOST_VALID files=40 operation=check',
                 'C77_PROVIDER_VALID files=7 operation=check']*1
        events+=['C77_PROVIDER_VALID files=7 operation=check']
        events+=['C118_BATCH_PROVIDER_VALID files=7 operation=check']*2
        for phase in (m.PHASES if i%2 else ('batch_host','original_host','batch_provider','original_provider')):
            events.append(f'C118_PHASE iteration={i} phase={phase} start={tick}.00 end={tick}.25');tick+=1
    text='\n'.join(events)+'\nC118_BATCH_PROFILE_COMPLETE_NO_UI\n'
    assert all(x['median_ms']==250 for x in m.metrics(text).values());cases.append('alternating-profile-timing-metrics')
    for label,bad in [('missing',text.replace(events[6]+'\n','')),('clock-backwards',text.replace('end=100.25','end=99.00')),
                      ('missing-witness',text.replace('files=40 operation=check','files=39 operation=check')),('launch',text+'operation=launch\n')]:
        try:m.metrics(bad)
        except ValueError:cases.append('refuse-profile-'+label)
        else:raise AssertionError(label)
    ast.parse(m.rendered_runner())
    paths=[Path(__file__),Path(m.__file__),m.REPO/'port/diagnostics/phase4-batch-fixture.py',
           m.REPO/'port/scripts/run-phase4-batch-validation.py',m.REPO/'port/scripts/package-phase4-batch-validation.py']
    for p in paths:ast.parse(p.read_text())
    r={'passed':True,'schema':118,'case_count':len(cases),'cases':cases,'real_equivalence_cases':fixture['case_count'],
       'source_sha256':{str(p.relative_to(m.REPO)):m.sha(p) for p in paths},'generated_sha256':{k:m.sha(stage/(k+'.sh')) for k in ['host','provider']},
       'device_or_GUI_executed':False,'local_ROM_reads_prohibited':True}
    write_new(stage/'analysis.json',(json.dumps(r,indent=2)+'\n').encode());sync_dir(stage)
    (m.AREA/'latest-checks').write_text(str(stage)+'\n');sync_dir(m.AREA)
    print('C118',len(cases),'offline cases passed:',stage)
if __name__=='__main__':main()
