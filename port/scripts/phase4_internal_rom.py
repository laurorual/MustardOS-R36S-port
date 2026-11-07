# SPDX-License-Identifier: MIT
"""C113 private ROM import: current C112 guard, independent logical backup."""
from pathlib import Path
import json,re
import phase4_resident_assets as assets
from phase4_candidate import sha
from phase4_root_migration import require
REPO,WORK=assets.REPO,assets.WORK
AREA=WORK/'internal-rom';NATIVE=REPO/'port/device/rk-r35s-p0/internal-rom'
ROM=REPO/'port/roms/gb/Super Mario Land (World) (Rev 1).gb'

def installed():
    assets.qualified();root=assets.parent.proof('resident-assets-installed')
    stage=Path((assets.AREA/'latest-complete').read_text().strip());require(stage.resolve().is_relative_to(assets.AREA),'Known C112 install')
    r=json.loads((stage/'analysis.json').read_text());public=json.loads((root/'analysis.json').read_text())
    require(r['passed'] is True and r['schema']==112 and all(public[k]==v for k,v in r.items()),'C112 native proof')
    for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'Frozen C112 source')
    plan=json.loads((stage/'plan.json').read_text());meta=json.loads((stage/'manifest.json').read_text())
    require(r['plan_sha256']==sha(stage/'plan.json') and r['files_added']==13 and r['root_read_only'] is r['RAM_removed'] is True,'Closed C112 installation')
    require((stage/'cleanup.stdout').read_text()=='C112_RAM_REMOVED_ROOT_RO\n','Authentic native cleanup')
    return stage,r,meta,plan

def common():
    _,r,meta,plan=installed();observation=assets.current_observation()
    require(observation['boot_sequence']==r['boot_sequence'] and observation['kernel_boot_id']==meta['kernel_boot_id'],'Exact C112 observed boot')
    code=assets.common()
    for n,h in plan['files'].items():
        code+=f'''[ -f /{assets.PREFIX}/{n} ];[ ! -L /{assets.PREFIX}/{n} ]
[ "$(stat -c '%u:%g:%a:%h' /{assets.PREFIX}/{n})" = 0:0:644:1 ]
printf '%s  %s\\n' {h} /{assets.PREFIX}/{n} | sha256sum -c - >/dev/null
'''
    code+=f'''[ ! -L /{assets.PREFIX} ];[ "$(stat -c '%u:%g:%a' /{assets.PREFIX})" = 0:0:755 ]
[ "$(find /{assets.PREFIX} -mindepth 1 -maxdepth 1 -print | wc -l)" = 13 ]
'''
    require(len(re.findall(r"printf '[^']+' ([0-9a-f]{64}) /([A-Za-z0-9_./+-]+) \| sha256sum -c - >/dev/null",code))==191,'Complete C113 guard')
    return code

def sources():
    return [Path(__file__),*sorted(NATIVE.glob('*.sh')),REPO/'port/scripts/run-phase4-internal-rom.py',
            REPO/'port/scripts/check-phase4-internal-rom.py',REPO/'port/diagnostics/phase4-internal-rom-fixture.py']
