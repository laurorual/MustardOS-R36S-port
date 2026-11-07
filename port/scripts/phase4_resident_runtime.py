# SPDX-License-Identifier: MIT
"""Shared C114/C115 provenance for resident assets and the internal ROM."""
from pathlib import Path
import json,re
import phase4_internal_rom as store
from phase4_candidate import sha
from phase4_root_migration import require
assets=store.assets;parent=assets.parent
REPO,WORK=store.REPO,store.WORK
AREA=WORK/'resident-preparation';proof=parent.proof

def qualified_rom():
    install,ir,meta,plan=store.installed();root=proof('internal-rom-imported')
    stage=Path((store.AREA/'latest-complete').read_text().strip());require(stage.resolve().is_relative_to(store.AREA),'Known ROM import')
    r=json.loads((stage/'analysis.json').read_text());public=json.loads((root/'analysis.json').read_text())
    require(r['passed'] is public['passed'] is True and r['schema']==113 and
        all(public[k]==v for k,v in r.items() if k not in ['ROM_sha256','kernel_boot_id']),'Frozen C113 qualification')
    require(r['root_read_only'] is r['data_unmounted'] is r['RAM_removed'] is r['C109_snapshot_byte_identical'] is True,'Safe completed import')
    require(r['plan_sha256']==sha(stage/'plan.json') and r['independent_backup_sha256']==sha(stage/'before.tar') and
        r['C112_analysis_sha256']==sha(install/'analysis.json') and r['kernel_boot_id']==meta['kernel_boot_id'],'Same imported source/boot')
    for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'C113 source frozen')
    prior=assets.qualified()[1];require(r['ROM_sha256']==prior['ROM_sha256'] and r['ROM_bytes']==65536,'Same already qualified legal ROM')
    return stage,r,meta,plan

def common():qualified_rom();return store.common()

def capsule(value):
    require(isinstance(value,str) and re.fullmatch('/run/muos-prefs-data[.][A-Za-z0-9]{6}',value),'Finite owned capsule')
    return value

def validation_commands(value):
    d=capsule(value);_,r,meta,_=qualified_rom();prior=assets.qualified()[1]
    code=common()
    table=proof('capsule-preparer-v3-installed')/'payload/assets.tsv'
    for line in table.read_text().splitlines():
        h,_,n,_=line.split()
        code+=f'''[ -f {d}/{n} ];[ ! -L {d}/{n} ];[ "$(stat -c %u:%g:%a:%h {d}/{n})" = 0:0:700:1 ]
printf '%s  %s\\n' {h} {d}/{n} | sha256sum -c - >/dev/null
'''
    for n in parent.caller.SCRIPTS:
        h=sha(proof('manual-caller-installed')/'payload'/n)
        code+=f'''[ -f {d}/{n} ];[ ! -L {d}/{n} ];[ "$(stat -c %u:%g:%a:%h {d}/{n})" = 0:0:700:1 ]
printf '%s  %s\\n' {h} {d}/{n} | sha256sum -c - >/dev/null
cmp /usr/libexec/muos-caller/{n} {d}/{n}
'''
    for n in ['identity','role','gb-assets.sha256','launcher.sha256','store-base.sha256','installed-store.sha256']:
        code+=f"""[ -f {d}/{n} ];[ ! -L {d}/{n} ];[ "$(stat -c %u:%g:%a:%h {d}/{n})" = 0:0:600:1 ]
"""
    for marker,script in [('launcher','app-launch.sh'),('store-base','store-base.sh'),('installed-store','installed-store.sh')]:
        code+=f"printf '%s\\n' {sha(proof('manual-caller-installed')/'payload'/script)} | cmp -s - {d}/{marker}.sha256\n"
    code+=f"printf '%s  %s\\n%s  %s\\n' {prior['core_sha256']} /opt/muos/share/core/gambatte_libretro.so {r['ROM_sha256']} private.gb | cmp -s - {d}/gb-assets.sha256\n"
    code+=f'''[ -f {d}/private.gb ];[ ! -L {d}/private.gb ];[ "$(stat -c %u:%g:%a:%h:%s {d}/private.gb)" = 0:0:700:1:65536 ]
printf '%s  %s\\n' {r['ROM_sha256']} {d}/private.gb | sha256sum -c - >/dev/null
printf '%s\\n' {prior['private_identity']} | cmp -s - {d}/identity
printf 'load\\n' | cmp -s - {d}/role
printf '%s\\n%s\\n' {r['boot_sequence']} {meta['kernel_boot_id']} | cmp -s - {d}/caller-stage/boot
grep -qx C105_STAGE_READY {d}/caller-stage/ready
grep -qx C107_CAPSULE_READY {d}/preparation.once/ready
grep -qx C112_RESIDENT_INPUTS_READY_ROM_P3 {d}/preparation.once/resident
[ ! -e {d}/data ];[ ! -L {d}/data ]
[ ! -e {d}/caller-stage/run.once ];[ ! -L {d}/caller-stage/run.once ]
echo C114_RESIDENT_ASSETS_ROM_IDENTITY_METADATA_VALIDATED_NO_UI
'''
    return code
