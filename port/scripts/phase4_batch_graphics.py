# SPDX-License-Identifier: MIT
"""C121 graphical preparation: separate provider names from the C120 bundle."""
import ast,json
from pathlib import Path
import phase4_batch_run as contract
from phase4_candidate import sha
from phase4_root_migration import require
REPO,WORK,session=contract.REPO,contract.WORK,contract.session
AREA=WORK/'batch-graphics'
# Provider libraries belong to the graphical context; the six bundle names
# remain private to contract.bundle(). Never mutate the frozen module globals.
NAMES=session.NAMES
historical,current_common,bind,watch_script=contract.historical,contract.current_common,contract.bind,contract.watch_script
render_online,NATIVE,caller,prep,proof=contract.render_online,contract.NATIVE,contract.caller,contract.prep,contract.proof

def qualified():
    contract.qualified();root=proof('batch-run')
    stage=Path((contract.AREA/'latest-complete').read_text().strip())
    require(stage.resolve().is_relative_to(contract.AREA),'Known C120 native stage')
    r=json.loads((stage/'analysis.json').read_text());p=json.loads((root/'analysis.json').read_text())
    require(r['passed'] is p['passed'] is True and r['schema']==120 and r['metrics']==p['metrics'] and
      r['run_enabled'] is True and r['native_graphical_dispatch_qualified'] is False,'C120 contract qualification; graphics still pending')
    for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'Frozen C120 source')
    checked=Path((contract.AREA/'latest-checks').read_text().strip())
    require(checked.resolve().is_relative_to(contract.AREA) and sha(checked/'analysis.json')==r['checks_analysis_sha256'],'Bound C120 checks')
    for n,b in contract.bundle().items():require(contract.hashlib.sha256(b).hexdigest()==r['bundle_sha256'][n],'Same C120 bundle')
    require(r['metrics']==contract.metrics((stage/'profile.stdout').read_text()),'Authentic native host check')
    for label in ['before','mounts-before','allocate','prepare','bundle','contract-check','validate','adopt','refusals','profile','validate-after','after','mounts-after','cleanup','post-cleanup-health']:
        require((stage/(label+'.exit')).read_text()=='0\n','C120 closed native receipt')
    return stage,r

def rendered_runner():
    text=contract.rendered_runner()
    require(text.count('from phase4_batch_run import ')==2,'Two C120 import boundaries')
    text=text.replace('from phase4_batch_run import ','from phase4_batch_graphics import ')
    text=session.change(text,'qualified()\nqualification_stage,','native_stage, native_report = qualified()\nqualification_stage,')
    text=session.change(text,"sources = [REPO/'port/scripts/phase4_batch_run.py',", "sources = [REPO/'port/scripts/phase4_batch_graphics.py', REPO/'port/scripts/check-phase4-batch-graphics.py', REPO/'port/scripts/phase4_batch_run.py',")
    require(text.count("'C113_analysis_sha256':")==2,'Observation and session source binding')
    text=text.replace("'C113_analysis_sha256':", "'C120_native_analysis_sha256':sha(native_stage/'analysis.json'), 'C120_proof_sha256':sha(proof('batch-run')/'SHA256SUMS'), 'C113_analysis_sha256':")
    text=session.change(text,"'schema':120, 'C120_batch_run_runtime_validation':True", "'schema':121, 'C120_batch_run_runtime_validation':True, 'C121_graphical_provider_routing':True")
    anchor="digests = bind(prior, provider, observation, args.boot, observation['kernel_boot_id'])"
    text=session.change(text,anchor,"assert observation['C120_native_analysis_sha256']==sha(native_stage/'analysis.json')\nassert observation['C120_proof_sha256']==sha(proof('batch-run')/'SHA256SUMS')\n"+anchor)
    text=text.replace('C120 batch caller observed boot','C121 batch graphics observed boot').replace('C120 batch caller session collected:','C121 batch graphics session collected:')
    ast.parse(text);return text
