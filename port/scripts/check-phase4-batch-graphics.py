#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C121 offline real provider context, C120 binding and zero-upload regression."""
import ast,hashlib,json,os,sys,tempfile
from pathlib import Path
import phase4_batch_graphics as m
from phase4_backup_core import write_new,sync_dir

def main():
    os.umask(0o077);m.AREA.mkdir(mode=0o700,exist_ok=True);cases=[]
    def audit(event,args):
        if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            m.require('/port/roms/' not in os.fsdecode(args[0]),'No host ROM input')
        if event=='socket.connect':raise AssertionError('Network forbidden')
    sys.addaudithook(audit)
    native,r=m.qualified();ctx,_,_,provider_stage,_,online=m.historical()
    assert len(m.NAMES)==4 and len(m.contract.NAMES)==6 and set(m.NAMES).isdisjoint(m.contract.NAMES)
    cases.append('four-provider-library-names-separated-from-six-bundle-files')
    text=m.rendered_runner();tree=ast.parse(text)
    start=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='(files, expected)')
    end=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='online')
    # Execute the actual generated preparation loops with real qualified paths.
    observation=json.loads((m.session.AREA/'observe.a8wgi4yu/observation.json').read_text())
    _,prior_stage,prior,provider_stage,provider,_=m.historical()
    libraries=m.bind(prior,provider,observation,observation['boot_sequence'],observation['kernel_boot_id'])
    ctx['files']=dict(ctx['files']);ctx['expected']=dict(ctx['expected'])
    env={'context':ctx,'NATIVE':m.NATIVE,'NAMES':m.NAMES,'provider_stage':provider_stage,'digests':libraries,'sha':m.sha}
    exec(compile(ast.Module(body=tree.body[start:end],type_ignores=[]),'C121-actual-provider-context','exec'),env)
    files,expected=env['files'],env['expected']
    assert all(files['provider-lib/'+n].is_file() and m.sha(files['provider-lib/'+n])==expected['provider-lib/'+n] for n in m.NAMES)
    assert not any('provider-lib/'+n in files for n in m.contract.NAMES)
    assert 'provider-probe' in files and not {'muxretro','save-store','core.so','core-check'}&set(files)
    cases.append('actual-generated-context-loops-execute-with-four-real-provider-libraries')
    rendered=m.render_online(online);online_tree=ast.parse(rendered)
    loops=[n for n in online_tree.body if isinstance(n,ast.For) and ast.unparse(n.target)=='(n, f)' and ast.unparse(n.iter)=='files.items()']
    assert len(loops)==1
    class Forbidden:
        def read_bytes(self):raise AssertionError('Unexpected asset input read')
        def run(self,*a,**kw):raise AssertionError('Unexpected input transport')
    exec(compile(ast.Module(body=loops,type_ignores=[]),'C121-zero-upload','exec'),{'files':{n:Forbidden() for n in files},'prepared_inputs':{},'subprocess':Forbidden()})
    cases.append('actual-upload-loop-executes-zero-input-reads-or-transfers')
    gates=[n for n in tree.body if isinstance(n,ast.Assert) and isinstance(n.test,ast.Compare) and
           any(ast.unparse(n.test.left)=="observation['"+key+"']" for key in ['C120_native_analysis_sha256','C120_proof_sha256'])]
    assert len(gates)==2
    admit=compile(ast.Module(body=gates,type_ignores=[]),'C121-native-proof-admission','exec')
    valid={'C120_native_analysis_sha256':m.sha(native/'analysis.json'),'C120_proof_sha256':m.sha(m.proof('batch-run')/'SHA256SUMS')}
    def admission(row):exec(admit,{'observation':row,'sha':m.sha,'native_stage':native,'proof':m.proof})
    admission(valid);cases.append('actual-observation-native-proof-admission-passes')
    for key in valid:
        try:admission({**valid,key:'wrong'})
        except AssertionError:cases.append('actual-observation-admission-refuses-'+key)
        else:raise AssertionError('Unbound observation accepted')
    for fragment in ["'C120_native_analysis_sha256'","'C120_proof_sha256'","check_report['bundle_sha256']",'prepared_inputs={}',"'C121_graphical_provider_routing':True"]:
        assert fragment in text
    cases.append('frozen-native-contract-proof-checks-and-bundle-bindings-retained')
    assert 'import phase4_batch_run as batch' in text and 'from phase4_batch_graphics import historical' in text
    assert m.contract.NAMES==m.contract.previous.NAMES
    cases.append('original-contract-module-remains-unmodified-and-keeps-bundle-namespace')
    stage=Path(tempfile.mkdtemp(prefix='checks.',dir=m.AREA))
    paths=[Path(__file__),Path(m.__file__),m.REPO/'port/scripts/run-phase4-batch-graphics.py']
    report={'passed':True,'schema':121,'case_count':len(cases),'cases':cases,'C120_native_analysis_sha256':m.sha(native/'analysis.json'),
      'C120_proof_sha256':m.sha(m.proof('batch-run')/'SHA256SUMS'),'bundle_sha256':r['bundle_sha256'],
      'source_sha256':{str(p.relative_to(m.REPO)):m.sha(p) for p in paths},'device_or_GUI_executed':False,
      'local_ROM_reads_prohibited':True,'physical_confirmation_pending':True}
    write_new(stage/'analysis.json',(json.dumps(report,indent=2)+'\n').encode());sync_dir(stage)
    (m.AREA/'latest-checks').write_text(str(stage)+'\n');sync_dir(m.AREA)
    print('C121',len(cases),'offline routing checks passed:',stage)
if __name__=='__main__':main()
