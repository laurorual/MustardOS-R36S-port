# SPDX-License-Identifier: MIT
"""C107 local preparation model and C108 finite additive deployment."""
from pathlib import Path
import ast,json,re
import phase4_installed_caller_session as base
from phase4_candidate import sha,sums
from phase4_root_migration import require

REPO,WORK=base.REPO,base.WORK
AREA=WORK/'capsule-prepare';PREFIX='usr/libexec/muos-capsule'
NATIVE=REPO/'port/device/rk-r35s-p0/capsule-prepare'
NAMES=['functions.sh','assets.tsv','contract.json','LICENSE','payload.sha256','prepare.sh']
INPUTS={'runner':'runner','state-metadata':'state-metadata','lib/libmuxmod.so':'menu-libmuxmod.so','provider-probe':'provider-probe','private.gb':'private.gb'}

def qualified():
    base.qualified();proof=base.proof('installed-caller-session')
    stage=Path((base.AREA/'latest-load').read_text().strip())
    require(stage.resolve().is_relative_to(base.AREA),'Known C106 session')
    r=json.loads((stage/'analysis.json').read_text());public=json.loads((proof/'analysis.json').read_text())
    for key in ['passed','C106_installed_caller_runtime_validation','installed_entrypoint_used',
                'installed_worker_cmdline_confirmed','RAM_removed','root_ro','cleanup_passed','store_byte_identical_to_C63']:
        require(r[key] is True,'Complete C106 cycle')
    require(public['schema']==106 and public['passed'] is True and
        public['image_input_audio_restore_and_return_physically_confirmed'] is True,'Physical C106 qualification')
    for name in ['physical-observation.json','technical-analysis.json']:
        receipt=json.loads((stage/name).read_text());require(receipt['passed'] is True and
            receipt['session_analysis_sha256']==sha(stage/'analysis.json'),'Bound C106 receipt')
    final=json.loads((stage/'final-audit.json').read_text());require(final['passed'] is True,'C106 closure')
    for n,h in final['recorded_receipts_sha256'].items():require(sha(stage/n)==h,'C106 receipt changed')
    for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'Frozen C106 source changed')
    return stage,r

def common():
    _,r=qualified()
    code=base.current_common('',0,r['boot_sequence'])
    require(r['kernel_boot_id'] in code,'Same actual C106 boot')
    return code

def asset_model():
    stage,r=qualified();_,_,_,plan=base.qualified()
    manifest=base.proof('manual-caller-installed')/'payload/assets.tsv'
    expected=dict((n,h) for h,n in (line.split() for line in manifest.read_text().splitlines()))
    ctx,_,_,provider_stage,provider,_=base.historical()
    probe=provider_stage/'load-probe';expected['provider-probe']=sha(probe)
    table=[];guard=common()
    for dest,h in expected.items():
        if dest in INPUTS:mode=0o700;origin='inputs/'+INPUTS[dest]
        else:
            origin='opt/muos/frontend/lib/'+Path(dest).name;mode=0o755
            require(re.search(r'printf [^\n]*'+h+' /'+re.escape(origin)+r' \| sha256sum',guard),
                'Local asset must be in the qualified installed foundation')
        table.append((h,mode,dest,origin))
    require(len(table)==11 and sum(o.startswith('opt/') for _,_,_,o in table)==7,'Seven local and four input public assets')
    return table,ctx['nr']['core_sha256']

def sources():
    return [Path(__file__),*sorted(NATIVE.glob('*.sh')),
        REPO/'port/scripts/prepare-phase4-capsule-prepare.py',REPO/'port/scripts/check-phase4-capsule-prepare.py',
        REPO/'port/diagnostics/phase4-capsule-prepare-fixture.py',
        REPO/'port/scripts/run-phase4-capsule-prepare-install.py']

def rendered_installer():
    source=REPO/'port/scripts/run-phase4-manual-caller-install.py'
    require(source.read_bytes()==(base.proof('manual-caller-installed')/'source'/source.relative_to(REPO)).read_bytes(),
        'Frozen C105 installer')
    text=source.read_text().replace('from phase4_manual_caller import *','from phase4_capsule_prepare import *')
    text=text.replace('C105','C108').replace('c105','c108')
    start=text.index('    prior,previous=qualified()\n');end=text.index("    ssh=['ssh'",start)
    text=text[:start]+'''    prior,boot=qualified();guard=common()
    stage=Path(tempfile.mkdtemp(prefix='install.',dir=AREA)) if a.operation=='prepare' else (
        a.stage.resolve() if a.stage else Path((AREA/'latest-plan').read_text().strip()))
    require(stage.resolve().is_relative_to(AREA),'Known C108 installation')
'''+text[end:]
    changes={
        "require(len(rows)==143,'C104 foundation plus layout guards')":"require(len(rows)==160,'C106 foundation plus installed caller')",
        "'observation_stage':str(observed),'observation_sha256':sha(observed/'observation.json'),\n":'',
        " and\n        plan['observation_sha256']==sha(observed/'observation.json')":'',
        "'C104_analysis_sha256'":"'C106_analysis_sha256'",
        ' = 17 ]':' = 6 ]',"'files_added':17":"'files_added':6",
        "f'sh /{PREFIX}/caller.sh check\\n')=='C108_CALLER_CHECK_OK_NO_UI\\n'":"f'sh /{PREFIX}/prepare.sh check\\n')=='C107_PREPARER_CHECK_OK_NO_UI\\n'",
        "'full_graphical_installed_caller_qualified'":"'full_graphical_preparation_qualified'",
        "'native_package_and_142_public_dependencies_checked'":"'native_preparer_and_C106_foundation_checked'",
        "'native_stage_and_repeat_incomplete_run_refusal_passed'":"'native_empty_preparation_refused_without_mutation'",
    }
    for old,new in changes.items():require(text.count(old)==1,'Finite C108 installer anchor '+old[:60]);text=text.replace(old,new)
    start=text.index("    code=full+f'''sh /{PREFIX}/caller.sh stage {demo}")
    end=text.index("    remote('cleanup-stage'",start)
    text=text[:start]+'''    native=remote('native-stage',full+f\"\"\"if sh /{PREFIX}/prepare.sh prepare {demo};then exit 64;fi
[ -z "$(find {demo} -mindepth 1 -maxdepth 1 -print)" ]
echo C108_EMPTY_PREPARATION_REFUSED_NO_MUTATION
\"\"\")
    require(native=='C108_EMPTY_PREPARATION_REFUSED_NO_MUTATION\\n','Native empty preparation refusal')
'''+text[end:]
    require(text.count("'schema':105")==3,'Three C108 report schemas')
    text=text.replace("'schema':105","'schema':108")
    ast.parse(text);return text
