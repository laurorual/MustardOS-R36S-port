#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C115 offline source/routing checks with local ROM reads and SSH prohibited."""
from pathlib import Path
import ast,json,os,subprocess,sys,tempfile
import phase4_resident_session as s
from phase4_backup_core import write_new,sync_dir

def main():
 os.umask(0o077);s.AREA.mkdir(mode=0o700,exist_ok=True);cases=[]
 def audit(event,args):
  if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
   s.require('/port/roms/' not in os.fsdecode(args[0]),'C115 checks must not read local ROM')
  if event=='socket.connect':raise AssertionError('Network forbidden')
  if event=='subprocess.Popen':
   cmd=args[1];s.require(cmd[:3]==['git','check-ignore','--quiet'] or cmd[:2]==['sh','-n'],'Only git-ignore and shell parsing allowed')
 sys.addaudithook(audit)
 def reject(name,fn):
  try:fn()
  except (ValueError,KeyError,AssertionError,TypeError):cases.append(name)
  else:raise AssertionError(name)
 _,r,meta,_=s.qualified();boot=r['boot_sequence'];cases.append('closed-C112-C113-C114-native-provenance')
 for label,b in [('old',boot-1),('new',boot+1),('bool',True),('string',str(boot))]:reject('wrong-boot-'+label,lambda b=b:s.current_common('',0,b))
 guard=s.current_common('',0,boot)
 assert guard.splitlines().count('c25_ready')==1
 assert guard.count(' | sha256sum -c - >/dev/null')==191
 subprocess.run(['sh','-n'],input=guard,text=True,check=True);cases.append('191-current-hashes-and-original-readiness')
 ctx,prior_stage,prior,provider_stage,provider,online=s.historical()
 assert ctx['nr']['ROM_sha256']==r['ROM_sha256'] and ctx['identity']==s.assets.qualified()[1]['private_identity']
 cases.append('historical-identity-from-native-p3-receipt-with-local-ROM-open-forbidden')
 observation={'passed':True,'experiment':'C77_OBSERVED_BOOT','boot_sequence':boot,'kernel_boot_id':meta['kernel_boot_id'],
 'prior_analysis_sha256':s.sha(prior_stage/'analysis.json'),'provider_analysis_sha256':s.sha(provider_stage/'analysis.json'),
 'C66_analysis_sha256':s.sha(s.WORK/'frontend-libs-session/load.o2agwm0q/analysis.json'),
 'C67_analysis_sha256':s.sha(ctx['C67_stage']/'analysis.json'),
 'C72_analysis_sha256':s.sha(s.WORK/'provider-upgrade-native/install.otw0lflu/install-analysis.json'),
 'C76_analysis_sha256':s.sha(s.WORK/'gambatte-install/install.ucdyhb4b/install-analysis.json'),
 'C113_analysis_sha256':s.sha(s.qualified()[0]/'analysis.json'),
 'C113_proof_sha256':s.sha(s.proof('internal-rom-imported')/'SHA256SUMS'),
 'root_RO_installed_payload_and_foundation_verified':True,'agent_requested_reboot':False,'infrastructure':'fixture'}
 assert s.bind(prior,provider,observation,boot,meta['kernel_boot_id'])==ctx['C66_report']['libraries'];cases.append('observed-boot-and-existing-snapshot-source-bound')
 for key in ['C113_analysis_sha256','C113_proof_sha256']:
  bad={**observation,key:'0'*64};reject('bad-'+key,lambda bad=bad:s.bind(prior,provider,bad,boot,meta['kernel_boot_id']))
 reject('missing-source',lambda:s.bind(prior,provider,{},boot,meta['kernel_boot_id']))
 reject('wrong-UUID',lambda:s.bind(prior,provider,observation,boot,'00000000-0000-4000-8000-000000000115'))
 rendered=s.render_online(online);ast.parse(rendered)
 assert '/usr/libexec/muos-resident/load.sh prepare {directory}' in rendered and 'C112_RESIDENT_PREPARED_ZERO_UPLOADS' in rendered
 assert 'mkdir -m 700 {directory}/inputs' not in rendered and 'C112_RESIDENT_INPUTS_READY_ROM_P3' in rendered
 assert '/usr/libexec/muos-caller/caller.sh run' in rendered
 cases.append('installed-loader-empty-capsule-resident-marker-and-original-caller')
 loops=[n for n in ast.parse(rendered).body if isinstance(n,ast.For) and ast.unparse(n.target)=='(n, f)' and ast.unparse(n.iter)=='files.items()']
 assert len(loops)==1
 class Forbidden:
  def read_bytes(self):raise AssertionError('No input bytes may be read')
 class NoTransport:
  def run(self,*args,**kw):raise AssertionError('No input upload may occur')
 env={'files':{'private.gb':Forbidden(),'runner':Forbidden(),'lib/libmuxmod.so':Forbidden()},'prepared_inputs':{},'subprocess':NoTransport()}
 exec(compile(ast.Module(body=loops,type_ignores=[]),'C115-zero-upload-loop','exec'),env)
 cases.append('executed-upload-loop-reads-and-sends-zero-files-including-ROM')
 runner=s.rendered_runner();ast.parse(runner)
 assert 'prepared_inputs={}' in runner and "'runtime_input_uploads':0" in runner and "'ROM_source_internal_p3':True" in runner
 assert "'Quick Save (hotkey)' not in game" in runner and 'C106_INSTALLED_WORKER_CMDLINE_CONFIRMED' in runner
 cases.append('zero-input-runtime-preserves-load-only-map-worker-and-cleanup-contract')
 old=s.proof('installed-host-session')/'source/port/scripts/run-phase4-installed-host-session.py'
 reject('changed-legacy-ROM-boundary',lambda:s.resident_offline(old.read_text().replace('assert rom.is_file()','changed_boundary')))
 paths=[Path(__file__),Path(s.__file__),s.REPO/'port/scripts/run-phase4-resident-session.py',s.REPO/'port/scripts/finish-phase4-resident-session.py',s.REPO/'port/scripts/analyze-phase4-resident-session.py']
 for p in paths:ast.parse(p.read_text())
 target=Path(tempfile.mkdtemp(prefix='checks.',dir=s.AREA));report={'passed':True,'schema':115,'case_count':len(cases),'cases':cases,
 'source_sha256':{str(p.relative_to(s.REPO)):s.sha(p) for p in paths},'local_ROM_reads_prohibited':True,
 'device_network_GUI_core_or_reboot_executed':False,'physical_test_pending':True}
 write_new(target/'analysis.json',(json.dumps(report,indent=2)+'\n').encode());sync_dir(target)
 (s.AREA/'latest-checks').write_text(str(target)+'\n');sync_dir(s.AREA)
 print('C115',len(cases),'resident source/routing checks passed; physical test pending:',target)
if __name__=='__main__':main()
