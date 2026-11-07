# SPDX-License-Identifier: MIT
"""C110: correct the local-library mode contract without rewriting C107/C108."""
from pathlib import Path
import ast,json
import phase4_capsule_prepare as old
from phase4_candidate import sha
from phase4_root_migration import require

base=old.base
REPO,WORK,NATIVE,NAMES,INPUTS=old.REPO,old.WORK,old.NATIVE,old.NAMES,old.INPUTS
AREA=WORK/'capsule-prepare-v2';PREFIX='usr/libexec/muos-capsule-v2'

def qualified():
    result=old.qualified()
    root=base.proof('capsule-preparer-installed')
    stage=Path((old.AREA/'latest-complete').read_text().strip())
    require(stage.resolve().is_relative_to(old.AREA),'Known C108 installation')
    r=json.loads((stage/'analysis.json').read_text());public=json.loads((root/'analysis.json').read_text())
    require(r['passed'] is True and all(public[k]==v for k,v in r.items()),'Frozen C108 proof')
    for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'C107/C108 unchanged')
    require((stage/'cleanup.stdout').read_text()=='C108_RAM_REMOVED_ROOT_RO\n','Closed C108')
    return result

def common():
    qualified();code=old.common()
    stage=Path((old.AREA/'latest-complete').read_text().strip())
    plan=json.loads((stage/'plan.json').read_text())
    require(json.loads((stage/'analysis.json').read_text())['plan_sha256']==sha(stage/'plan.json'),'C108 plan')
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
    # C108 native refusal inspection found these installed libraries at 0644.
    # Preserve that mode; executable permission is unnecessary for dlopen.
    return [(h,0o644 if origin.startswith('opt/') else mode,dest,origin)
            for h,mode,dest,origin in table],core

def sources():
    return old.sources()+[Path(__file__),REPO/'port/scripts/prepare-phase4-capsule-prepare-v2.py',
        REPO/'port/scripts/check-phase4-capsule-prepare-v2.py',REPO/'port/scripts/run-phase4-capsule-prepare-v2-install.py',
        REPO/'port/diagnostics/phase4-capsule-prepare-v2-fixture.py']

def rendered_installer():
    text=old.rendered_installer()
    require(text.count('from phase4_capsule_prepare import *')==1,'Known C108 installer import')
    text=text.replace('from phase4_capsule_prepare import *','from phase4_capsule_prepare_v2 import *')
    text=text.replace('C108','C110').replace('c108','c110')
    require(text.count("len(rows)==160")==1,'Known C108 foundation inventory')
    text=text.replace('len(rows)==160','len(rows)==166')
    require(text.count("'schema':108")==3,'Known C108 schemas')
    text=text.replace("'schema':108","'schema':110")
    ast.parse(text);return text
