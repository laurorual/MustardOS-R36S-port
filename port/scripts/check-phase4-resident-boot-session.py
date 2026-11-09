#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C116 offline postboot binding and zero-upload routing regression checks."""
import ast,json,os,subprocess,sys,tempfile
from pathlib import Path
import phase4_resident_boot_session as s
from phase4_backup_core import write_new,sync_dir

def main():
    os.umask(0o077);s.AREA.mkdir(mode=0o700,exist_ok=True);cases=[]
    def audit(event,args):
        if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            s.require('/port/roms/' not in os.fsdecode(args[0]),'No local ROM input')
        if event=='socket.connect':raise AssertionError('Network forbidden')
        if event=='subprocess.Popen':
            cmd=args[1];s.require(cmd[:3]==['git','check-ignore','--quiet'] or cmd[:2]==['sh','-n'],'Only git-ignore and shell syntax')
    sys.addaudithook(audit)
    def reject(name,fn):
        try:fn()
        except (ValueError,KeyError,AssertionError,TypeError):cases.append(name)
        else:raise AssertionError(name)
    source,r,meta,_=s.qualified();old=r['boot_sequence'];boot=old+1
    uid='00000000-0000-4000-8000-000000000116'
    for name,b,u in [('past',old-1,uid),('bool',True,uid),('string',str(boot),uid),('overflow',1000000,uid),
                     ('old-counter-new-UUID',old,uid),('new-counter-old-UUID',boot,meta['kernel_boot_id']),
                     ('missing-UUID',boot,None),('malformed-UUID',boot,'bad; exit 0'),
                     ('noncanonical-UUID',boot,uid.replace('-',''))]:
        reject('refuse-'+name,lambda b=b,u=u:s.current_common('',0,b,u))
    for b,u in [(old,meta['kernel_boot_id']),(boot,uid)]:
        code=s.current_common('',0,b,u)
        assert code.count(' | sha256sum -c - >/dev/null')==191 and code.splitlines().count('c25_ready')==1
        assert f'= {u} ]' in code
        subprocess.run(['sh','-n'],input=code,text=True,check=True)
    cases.append('constructs-same-or-new-boot-with-191-hashes-global-readiness-no-history-rewrite')
    ctx,prior_stage,prior,provider_stage,provider,online=s.historical()
    assert ctx['nr']['ROM_sha256']==r['ROM_sha256'];cases.append('qualified-history-with-local-ROM-open-forbidden')
    observation={'passed':True,'experiment':'C77_OBSERVED_BOOT','boot_sequence':boot,'kernel_boot_id':uid,
        'prior_analysis_sha256':s.sha(prior_stage/'analysis.json'),'provider_analysis_sha256':s.sha(provider_stage/'analysis.json'),
        'C66_analysis_sha256':s.sha(s.WORK/'frontend-libs-session/load.o2agwm0q/analysis.json'),
        'C67_analysis_sha256':s.sha(ctx['C67_stage']/'analysis.json'),
        'C72_analysis_sha256':s.sha(s.WORK/'provider-upgrade-native/install.otw0lflu/install-analysis.json'),
        'C76_analysis_sha256':s.sha(s.WORK/'gambatte-install/install.ucdyhb4b/install-analysis.json'),
        'C113_analysis_sha256':s.sha(source/'analysis.json'),
        'C113_proof_sha256':s.sha(s.proof('internal-rom-imported')/'SHA256SUMS'),
        'root_RO_installed_payload_and_foundation_verified':True,'agent_requested_reboot':False,'infrastructure':'fixture'}
    assert s.bind(prior,provider,observation,boot,uid)==ctx['C66_report']['libraries']
    cases.append('new-observation-retains-C113-import-and-existing-snapshot-provider')
    for key in ['boot_sequence','kernel_boot_id','C113_analysis_sha256','C113_proof_sha256']:
        bad={**observation,key:'invalid'}
        reject('refuse-observation-'+key,lambda bad=bad:s.bind(prior,provider,bad,boot,uid))
    reject('refuse-missing-observation',lambda:s.bind(prior,provider,{},boot,uid))
    rendered=s.render_online(online);ast.parse(rendered)
    assert 'sh /usr/libexec/muos-resident/load.sh prepare {directory}' in rendered
    assert 'C112_RESIDENT_PREPARED_ZERO_UPLOADS' in rendered and 'C112_RESIDENT_INPUTS_READY_ROM_P3' in rendered
    cases.append('original-resident-prepare-markers-and-installed-caller')
    loops=[n for n in ast.parse(rendered).body if isinstance(n,ast.For) and ast.unparse(n.target)=='(n, f)' and ast.unparse(n.iter)=='files.items()']
    assert len(loops)==1
    class Forbidden:
        def read_bytes(self):raise AssertionError('Input read forbidden')
        def run(self,*a,**kw):raise AssertionError('Input transport forbidden')
    exec(compile(ast.Module(body=loops,type_ignores=[]),'C116-zero-upload-loop','exec'),
         {'files':{'private.gb':Forbidden(),'runner':Forbidden()},'prepared_inputs':{},'subprocess':Forbidden()})
    cases.append('upload-loop-executed-with-zero-input-reads-or-transport')
    runner=s.rendered_runner();ast.parse(runner)
    for text in ["'runtime_input_uploads':0","'ROM_source_internal_p3':True",'prepared_inputs={}',
                 "'Quick Save (hotkey)' not in game",'C106_INSTALLED_WORKER_CMDLINE_CONFIRMED',
                 "args.boot, args.boot_id)","group.add_argument('--observation', type=Path)"]:
        assert text in runner,text
    cases.append('explicit-UUID-new-guard-load-only-worker-maps-and-bounded-lifecycle-retained')
    reject('finite-adapter-refuses-changed-source',lambda:s.change('changed','original','new'))
    paths=[Path(__file__),Path(s.__file__),s.REPO/'port/scripts/phase4_resident_session.py',
           *[s.REPO/'port/scripts'/f'{name}-phase4-resident-boot-session.py' for name in ['run','analyze','finish','package']],
           s.REPO/'port/scripts/package-phase4-resident-session.py']
    for p in paths:ast.parse(p.read_text())
    target=Path(tempfile.mkdtemp(prefix='checks.',dir=s.AREA))
    report={'passed':True,'schema':116,'case_count':len(cases),'cases':cases,
        'source_sha256':{str(p.relative_to(s.REPO)):s.sha(p) for p in paths},'local_ROM_reads_prohibited':True,
        'device_network_GUI_core_or_reboot_executed':False,'physical_test_pending':True}
    write_new(target/'analysis.json',(json.dumps(report,indent=2)+'\n').encode());sync_dir(target)
    (s.AREA/'latest-checks').write_text(str(target)+'\n');sync_dir(s.AREA)
    print('C116',len(cases),'offline checks passed:',target)
if __name__=='__main__':main()
