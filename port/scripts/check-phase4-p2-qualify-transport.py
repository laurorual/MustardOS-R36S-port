#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C87 sealed bootstrap / receipt faults; no SSH, sudo or block devices."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import ast,importlib,json,os,tempfile
from phase4_backup_core import sha
from phase4_root_migration import ROOT_OFFSET,ROOT_BYTES

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/p2-writer'
os.umask(0o077);stage=Path(tempfile.mkdtemp(prefix='transport-checks.',dir=area));cases=[]
helper=importlib.import_module('phase4-p2-qualify');collector=importlib.import_module('collect-phase4-p2-qualify')
def reject(name,call):
    try:call()
    except (ValueError,RuntimeError,OSError):cases.append(name)
    else:raise AssertionError(name)
manifest={'files':{'fixture.py':'a'*64}}
report={'passed':True,'schema':87,'operation':'qualify-loop-only','source_sha256':manifest['files'],
    'kernel':'fixture','loop_case_count':4,'cases':['one','two','three','four']}
for n in ['physical_card_payload_written','physical_card_SETRO0','physical_card_writer_entrypoint_available',
    'candidate_provisioned','boot_handoff_authorized','seed_generated_or_loaded']:report[n]=False
for n in ['physical_card_all_four_aliases_readonly','physical_card_p2_unchanged_since_C86',
    'physical_card_automount_guard_unchanged','loop_detached_and_large_fixture_files_removed']:report[n]=True
unlock={'kind':'P2_UNLOCK_MAY_HAVE_STARTED','source_sha256':'1'*64,'previous_sha256':'2'*64,
    'protected_sha256':['3'*64,'4'*64],'offset':ROOT_OFFSET,'bytes':ROOT_BYTES}
intent={k:v for k,v in unlock.items() if k!='protected_sha256'};intent['kind']='P2_WRITE_MAY_HAVE_STARTED'
done={'kind':'P2_WRITE_VERIFIED','sha256':'1'*64,'offset':ROOT_OFFSET,'bytes':ROOT_BYTES,
    'all_four_aliases_kernel_readonly':True,'alias_cache_synchronized':True,'protected_complement_verified':True,'boot_handoff_authorized':False}
journals={'success':{'unlock-intent':unlock,'write-intent':intent,'complete':done},
    'short-write':{'unlock-intent':{**unlock,'previous_sha256':'1'*64},'write-intent':{**intent,'previous_sha256':'1'*64}}}
collector.validate(report,manifest,journals);cases.append('bound-native-report-and-both-exclusive-journals')
for key,value in [('schema',86),('operation','apply'),('source_sha256',{}),('physical_card_SETRO0',True),
    ('physical_card_payload_written',True),('physical_card_all_four_aliases_readonly',False),
    ('physical_card_p2_unchanged_since_C86',False),('physical_card_automount_guard_unchanged',False),
    ('loop_detached_and_large_fixture_files_removed',False),('boot_handoff_authorized',True),
    ('seed_generated_or_loaded',True),('loop_case_count',True),('cases',['one']*4)]:
    bad=deepcopy(report);bad[key]=value;reject('receipt-'+key,lambda:collector.validate(bad,manifest,journals))
for name,change in [('short-falsely-complete',lambda j:j['short-write'].update({'complete':done})),
    ('source-mismatch',lambda j:j['success']['write-intent'].update({'source_sha256':'9'*64})),
    ('protected-missing',lambda j:j['success']['unlock-intent'].update({'protected_sha256':[]})),
    ('out-of-p2-extent',lambda j:j['success']['complete'].update({'offset':0})),
    ('completion-before-RO',lambda j:j['success']['complete'].update({'all_four_aliases_kernel_readonly':False})),
    ('short-fixture-wrong-baseline',lambda j:j['short-write']['unlock-intent'].update({'previous_sha256':'9'*64}))]:
    bad=deepcopy(journals);change(bad);reject('journal-'+name,lambda:collector.validate(report,manifest,bad))

bundle=stage/'bundle';bundle.mkdir(mode=0o700)
for n in helper.SOURCES:(bundle/n).write_bytes(b'fixture-not-executable')
package={'operation':'qualify-loop-only','files':{n:sha(bundle/n) for n in helper.SOURCES}}
(bundle/'package.json').write_text(json.dumps(package))
roots=[];execs=[];original_read=Path.read_text;mkdtemp=tempfile.mkdtemp
def read(path,*a,**kw):return 'Jupiter' if str(path)=='/sys/class/dmi/id/product_name' else original_read(path,*a,**kw)
def make_root(**kwargs):p=Path(mkdtemp(prefix='sealed.',dir=stage));roots.append(p);return str(p)
class ExecStopped(Exception):pass
def execute(*args):execs.append(args);raise ExecStopped()
with patch.object(helper,'__file__',str(bundle/'phase4-p2-qualify.py')),patch.object(helper.os,'geteuid',return_value=0),patch.object(helper.platform,'machine',return_value='x86_64'),patch.object(Path,'read_text',read),patch.object(helper.tempfile,'mkdtemp',make_root),patch.object(helper.os,'execve',execute):
    try:helper.bootstrap()
    except ExecStopped:pass
    assert execs[0][1][-1]=='_qualify' and execs[0][2]['PYTHONDONTWRITEBYTECODE']=='1'
    assert {p.name for p in roots[-1].iterdir()}==helper.SOURCES and all(p.stat().st_mode&0o777==0o400 for p in roots[-1].iterdir())
    cases.append('bootstrap-exact-source-hashes-sealed-root400-and-clean-env')
    package['operation']='apply';(bundle/'package.json').write_text(json.dumps(package));reject('bootstrap-no-card-writer-operation',helper.bootstrap)
    package['operation']='qualify-loop-only';package['files']['extra.py']='0'*64;(bundle/'package.json').write_text(json.dumps(package));reject('bootstrap-extra-source',helper.bootstrap)
    package['files'].pop('extra.py');(bundle/'package.json').write_text(json.dumps(package));(bundle/'context.json').write_bytes(b'changed')
    reject('bootstrap-modified-leaf',helper.bootstrap)
sources=[Path(__file__),repo/'port/scripts/collect-phase4-p2-qualify.py',repo/'port/scripts/prepare-phase4-p2-qualify.py',repo/'port/scripts/phase4-p2-qualify.py']
for path in sources:ast.parse(path.read_text())
(stage/'analysis.json').write_text(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,
    'physical_device_or_network_contacted':False,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}},indent=2)+'\n')
(area/'latest-transport-checks').write_text(str(stage)+'\n');print('C87 transport:',len(cases),'cases passed:',stage)
