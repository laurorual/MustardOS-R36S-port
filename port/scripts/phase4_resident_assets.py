# SPDX-License-Identifier: MIT
"""C112 finite resident assets package; C109/C111 remain frozen."""
from pathlib import Path
import ast,json,re
import phase4_prepared_capsule_session as parent
from phase4_candidate import sha
from phase4_root_migration import require
REPO,WORK=parent.REPO,parent.WORK
base=parent.base
AREA=WORK/'resident-assets';PREFIX='usr/libexec/muos-resident'
NATIVE=REPO/'port/device/rk-r35s-p0/resident'
NAMES=['functions.sh','assets.tsv','dependencies.tsv','contract.json','LICENSE','LICENSE.frontend',
       'runner','state-metadata','menu-libmuxmod.so','provider-probe','sync-path','payload.sha256','load.sh']
ASSETS={'runner':'runner','state-metadata':'state-metadata','lib/libmuxmod.so':'menu-libmuxmod.so','provider-probe':'provider-probe'}

def qualified():
    parent.qualified();root=parent.proof('prepared-capsule-session')
    stage=Path((parent.AREA/'latest-load').read_text().strip())
    require(stage.resolve().is_relative_to(parent.AREA),'Known C109 stage')
    r=json.loads((stage/'analysis.json').read_text());public=json.loads((root/'analysis.json').read_text())
    require(r['passed'] is public['passed'] is True and r['schema']==109 and
        public['image_input_audio_restore_and_return_physically_confirmed'] is True,'C109 qualification')
    for name in ['physical-observation.json','technical-analysis.json']:
        rec=json.loads((stage/name).read_text());require(rec['passed'] is True and rec['session_analysis_sha256']==sha(stage/'analysis.json'),'Bound C109 receipts')
    final=json.loads((stage/'final-audit.json').read_text());require(final['passed'] is True,'Closed C109')
    for n,h in final['recorded_receipts_sha256'].items():require(sha(stage/n)==h,'Authentic C109 closure')
    for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'C109 source frozen')
    return stage,r

def observed_guard(boot,boot_id):
    import uuid
    _,prior=qualified()
    require(type(boot) is int and boot>=prior['boot_sequence'] and str(uuid.UUID(boot_id))==boot_id,'Valid current boot identity')
    require((boot==prior['boot_sequence'])==(boot_id==prior['kernel_boot_id']),'Counter and UUID transition agree')
    code=parent.caller.observed_common(boot,boot_id)
    modules=[parent.caller,parent.prep.old.old,parent.prep.old,parent.prep]
    for mod in modules:
        stage=Path((mod.AREA/'latest-complete').read_text().strip())
        require(stage.resolve().is_relative_to(mod.AREA),'Known installed stage')
        r=json.loads((stage/'analysis.json').read_text());plan=json.loads((stage/'plan.json').read_text())
        require(r['passed'] is True and r['plan_sha256']==sha(stage/'plan.json'),'Installed plan binding')
        for n,h in plan['files'].items():
            code+=f"""[ -f /{mod.PREFIX}/{n} ];[ ! -L /{mod.PREFIX}/{n} ]
[ "$(stat -c '%u:%g:%a:%h' /{mod.PREFIX}/{n})" = 0:0:644:1 ]
printf '%s  %s\\n' {h} /{mod.PREFIX}/{n} | sha256sum -c - >/dev/null
"""
        code+=f"""[ ! -L /{mod.PREFIX} ];[ "$(stat -c '%u:%g:%a' /{mod.PREFIX})" = 0:0:755 ]
[ "$(find /{mod.PREFIX} -mindepth 1 -maxdepth 1 -print | wc -l)" = {len(plan['files'])} ]
"""
    require(len(re.findall(r"printf '[^']+' ([0-9a-f]{64}) /([A-Za-z0-9_./+-]+) \| sha256sum -c - >/dev/null",code))==178,'Complete current guard')
    return code

def current_observation():
    stage=Path((AREA/'latest-observation').read_text().strip())
    require(stage.resolve().is_relative_to(AREA),'Known C112 observation')
    r=json.loads((stage/'observation.json').read_text());guard=observed_guard(r['boot_sequence'],r['kernel_boot_id'])
    from phase4_gambatte_install import INFRA
    require(r['passed'] is True and r['schema']==112 and r['C109_analysis_sha256']==sha(qualified()[0]/'analysis.json') and
        (stage/'ready.exit').read_text()=='0\n' and sha(stage/'ready.sh')==r['guard_sha256'] and
        (stage/'ready.sh').read_text()==guard+INFRA and (stage/'ready.stdout').read_text()==r['infrastructure'],'Authentic fresh C112 guard')
    return r

def common():
    r=current_observation();return observed_guard(r['boot_sequence'],r['kernel_boot_id'])

def asset_files():
    ctx,_,_,provider_stage,_,_=parent.historical()
    files={n:ctx['files'][n] for n in ASSETS if n!='provider-probe'}
    files['provider-probe']=provider_stage/'load-probe'
    manifest={dest:h for h,_,dest,_ in parent.prep.asset_model()[0]}
    for n,p in files.items():require(sha(p)==manifest[n],'Exact qualified public asset')
    return files

def sources():
    return [Path(__file__),*sorted(NATIVE.glob('*.sh')),
        REPO/'port/scripts/prepare-phase4-resident-assets.py',REPO/'port/scripts/check-phase4-resident-assets.py',
        REPO/'port/scripts/run-phase4-resident-assets-install.py',REPO/'port/diagnostics/phase4-resident-fixture.py',REPO/'port/utils/muos-sync-path.c',REPO/'port/scripts/observe-phase4-resident-assets.py']

def rendered_installer():
    text=parent.prep.rendered_installer()
    old='from phase4_capsule_prepare_v3 import *'
    require(text.count(old)==1,'Frozen C111 installer import')
    text=text.replace(old,'from phase4_resident_assets import *').replace('c111','c112').replace('C111','C112')
    for a,b in [('len(rows)==172','len(rows)==178'),("'schema':111","'schema':112"),
                (' = 6 ]',' = 13 ]'),("'files_added':6","'files_added':13"),
                ('/{PREFIX}/prepare.sh','/{PREFIX}/load.sh'),
                ('C107_PREPARER_CHECK_OK_NO_UI','C112_RESIDENT_CHECK_OK_NO_UI'),
                ("'C106_analysis_sha256'","'C109_analysis_sha256'")]:
        require(a in text,'Finite C112 installer anchor '+a);text=text.replace(a,b)
    require(text.count('prior,boot=qualified();guard=common()')==1,'C112 current observation anchor')
    text=text.replace('prior,boot=qualified();guard=common()','prior,previous=qualified();boot=current_observation();guard=common()')
    # C112 loader's empty capsule is a valid request, so its negative test uses
    # an existing inputs directory. No ROM is read by this install check.
    old='''    native=remote('native-stage',full+f"""if sh /{PREFIX}/load.sh prepare {demo};then exit 64;fi
[ -z "$(find {demo} -mindepth 1 -maxdepth 1 -print)" ]
echo C112_EMPTY_PREPARATION_REFUSED_NO_MUTATION
""")'''
    new='''    native=remote('native-stage',full+f"""mkdir -m 700 {demo}/inputs
if sh /{PREFIX}/load.sh prepare {demo};then exit 64;fi
[ "$(find {demo} -mindepth 1 -maxdepth 1 -print)" = {demo}/inputs ]
[ -z "$(find {demo}/inputs -mindepth 1 -print)" ]
echo C112_EMPTY_PREPARATION_REFUSED_NO_MUTATION
""")'''
    require(text.count(old)==1,'C112 nonempty capsule refusal');text=text.replace(old,new)
    ast.parse(text);return text
