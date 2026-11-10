# SPDX-License-Identifier: MIT
"""C122 exact C120 bundle residency; C121 graphical proof stays frozen."""
import ast,json,re
from pathlib import Path
import phase4_batch_graphics as graphics
import phase4_resident_assets as old_install
from phase4_candidate import sha
from phase4_root_migration import require
REPO,WORK=graphics.REPO,graphics.WORK
AREA=WORK/'resident-batch';PREFIX='usr/libexec/muos-batch-v1'
NATIVE=REPO/'port/device/rk-r35s-p0/resident-batch'
NAMES=[*graphics.contract.NAMES,'resident-functions.sh','resident.sha256','load.sh']
base=graphics

def qualified():
    graphics.qualified();root=graphics.proof('batch-graphics')
    stage=Path((graphics.AREA/'latest-load').read_text().strip())
    require(stage.resolve().is_relative_to(graphics.AREA),'Known C121 cycle')
    r=json.loads((stage/'analysis.json').read_text());p=json.loads((root/'analysis.json').read_text())
    require(r['passed'] is p['passed'] is True and r['schema']==121 and
      p['native_graphical_dispatch_qualified'] is p['image_input_audio_restore_and_return_physically_confirmed'] is True,'Qualified C121 cycle')
    for n in ['physical-observation.json','technical-analysis.json']:
        row=json.loads((stage/n).read_text());require(row['passed'] is True and row['session_analysis_sha256']==sha(stage/'analysis.json'),'Bound C121 confirmation')
    final=json.loads((stage/'final-audit.json').read_text());require(final['passed'] is True,'C121 closed')
    for n,h in final['recorded_receipts_sha256'].items():require(sha(stage/n)==h,'C121 receipt changed')
    for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'Frozen C121 source')
    require(r['bundle_sha256']=={n:graphics.contract.hashlib.sha256(b).hexdigest() for n,b in graphics.contract.bundle().items()},'Exact C120 bundle')
    return stage,r

def current_observation():
    _,r=qualified();observed=Path((graphics.AREA/'latest-observation').read_text().strip())
    require(observed.resolve().is_relative_to(graphics.AREA),'Known C121 observation')
    row=json.loads((observed/'observation.json').read_text())
    require(row['passed'] is True and row['boot_sequence']==r['boot_sequence'] and row['kernel_boot_id']==r['kernel_boot_id'],'Same qualified current boot')
    return row

def common():
    b=current_observation();return graphics.current_common('',0,b['boot_sequence'],b['kernel_boot_id'])

def payload():
    qualified();data=graphics.contract.bundle();data['resident-functions.sh']=(NATIVE/'functions.sh').read_bytes()
    data['resident.sha256']=''.join(graphics.contract.hashlib.sha256(data[n]).hexdigest()+' '+n+'\n' for n in NAMES[:-2]).encode()
    old=graphics.proof('manual-caller-installed')/'payload'
    text=(NATIVE/'load.in.sh').read_text()
    for token,value in [('@RESIDENT_MANIFEST_SHA@',graphics.contract.hashlib.sha256(data['resident.sha256']).hexdigest()),
      ('@CALLER_MANIFEST_SHA@',sha(old/'payload.sha256')),('@CALLER_FUNCTIONS_SHA@',sha(old/'functions.sh')),
      ('@RESIDENT_FUNCTIONS_SHA@',graphics.contract.hashlib.sha256(data['resident-functions.sh']).hexdigest())]:
        text=graphics.session.change(text,token,value)
    data['load.sh']=text.encode();require(list(data)==NAMES,'Nine exact package files')
    return data

def sources():
    return [Path(__file__),*sorted(NATIVE.glob('*.sh')),*[REPO/'port/scripts'/n for n in
      ['prepare-phase4-resident-batch.py','check-phase4-resident-batch.py','run-phase4-resident-batch-install.py']],
      REPO/'port/diagnostics/phase4-resident-batch-fixture.py',*sorted((REPO/'port/buildroot-batch').rglob('*.*'))]

def rendered_installer():
    text=old_install.rendered_installer()
    text=graphics.session.change(text,'from phase4_resident_assets import *','from phase4_resident_batch import *')
    text=text.replace('C112','C122').replace('c112','c122').replace("'schema':112","'schema':122")
    for a,b in [('len(rows)==178','len(rows)==191'),(' = 13 ]',' = 9 ]'),("'files_added':13","'files_added':9"),
                ('C109_analysis_sha256','C121_analysis_sha256'),('C122_RESIDENT_CHECK_OK_NO_UI','C122_RESIDENT_BATCH_CHECK_OK_NO_UI'),
                ('load.sh prepare {demo}','load.sh adopt {demo}')]:
        require(a in text,'Finite C122 installer '+a);text=text.replace(a,b)
    text=text.replace('C122_EMPTY_PREPARATION_REFUSED_NO_MUTATION','C122_EMPTY_ADOPTION_REFUSED_NO_MUTATION')
    ast.parse(text);return text
