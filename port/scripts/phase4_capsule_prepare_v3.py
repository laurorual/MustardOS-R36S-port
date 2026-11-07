# SPDX-License-Identifier: MIT
"""C111: correct the real staged callback while preserving earlier receipts."""
from pathlib import Path
import ast,json
import phase4_capsule_prepare_v2 as old
from phase4_candidate import sha
from phase4_root_migration import require

base=old.base
REPO,WORK,NATIVE,NAMES,INPUTS=old.REPO,old.WORK,old.NATIVE,old.NAMES,old.INPUTS
AREA=WORK/'capsule-prepare-v3';PREFIX='usr/libexec/muos-capsule-v3'

def qualified():
    result=old.qualified()
    root=base.proof('capsule-preparer-v2-installed')
    stage=Path((old.AREA/'latest-complete').read_text().strip())
    require(stage.resolve().is_relative_to(old.AREA),'Known C110 installation')
    r=json.loads((stage/'analysis.json').read_text());public=json.loads((root/'analysis.json').read_text())
    require(r['passed'] is True and all(public[k]==v for k,v in r.items()),'Frozen C110 proof')
    for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'C107-C110 unchanged')
    require((stage/'cleanup.stdout').read_text()=='C110_RAM_REMOVED_ROOT_RO\n','Closed C110')
    return result

def common():
    qualified();code=old.common()
    stage=Path((old.AREA/'latest-complete').read_text().strip())
    plan=json.loads((stage/'plan.json').read_text())
    require(json.loads((stage/'analysis.json').read_text())['plan_sha256']==sha(stage/'plan.json'),'C110 plan')
    for n,h in plan['files'].items():
        code+=f'''[ -f /{old.PREFIX}/{n} ];[ ! -L /{old.PREFIX}/{n} ]
[ "$(stat -c '%u:%g:%a:%h' /{old.PREFIX}/{n})" = 0:0:644:1 ]
printf '%s  %s\\n' {h} /{old.PREFIX}/{n} | sha256sum -c - >/dev/null
'''
    code+=f'''[ ! -L /{old.PREFIX} ];[ "$(stat -c '%u:%g:%a' /{old.PREFIX})" = 0:0:755 ]
[ "$(find /{old.PREFIX} -mindepth 1 -maxdepth 1 -print | wc -l)" = 6 ]
'''
    return code

def asset_model():
    table,core=old.asset_model()
    # C110 native refusal inspection found these installed libraries at 0644.
    # Preserve that mode; executable permission is unnecessary for dlopen.
    return [(h,0o644 if origin.startswith('opt/') else mode,dest,origin)
            for h,mode,dest,origin in table],core

def sources():
    return old.sources()+[Path(__file__),REPO/'port/scripts/prepare-phase4-capsule-prepare-v3.py',
        REPO/'port/scripts/check-phase4-capsule-prepare-v3.py',REPO/'port/scripts/run-phase4-capsule-prepare-v3-install.py',
        REPO/'port/diagnostics/phase4-capsule-prepare-v3-fixture.py']

def rendered_installer():
    text=old.rendered_installer()
    require(text.count('from phase4_capsule_prepare_v2 import *')==1,'Known C110 installer import')
    text=text.replace('from phase4_capsule_prepare_v2 import *','from phase4_capsule_prepare_v3 import *')
    text=text.replace('C110','C111').replace('c110','c111')
    require(text.count("len(rows)==166")==1,'Known C110 foundation inventory')
    text=text.replace('len(rows)==166','len(rows)==172')
    require(text.count("'schema':110")==3,'Known C110 schemas')
    text=text.replace("'schema':110","'schema':111")
    ast.parse(text);return text
