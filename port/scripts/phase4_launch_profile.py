# SPDX-License-Identifier: MIT
"""C117 check-only launch-cost profile; no graphical session or input injection."""
import ast,json,statistics
from decimal import Decimal
from pathlib import Path
import phase4_resident_boot_session as session
from phase4_candidate import sha
from phase4_root_migration import require

REPO,WORK=session.REPO,session.WORK
AREA=WORK/'launch-profile'
PHASES=('host_check','provider_check','content_checks_RAM_copy')

def qualified():
    session.qualified();root=session.proof('resident-boot-session')
    stage=Path((session.AREA/'latest-load').read_text().strip())
    require(stage.resolve().is_relative_to(session.AREA),'Known C116 qualification')
    r=json.loads((stage/'analysis.json').read_text());p=json.loads((root/'analysis.json').read_text())
    require(r['passed'] is p['passed'] is True and r['schema']==116 and
            p['image_input_audio_restore_and_return_physically_confirmed'] is True and
            p['boot_sequence']==r['boot_sequence'] and p['core_frames']==r['core_frames'],'Qualified C116')
    for name in ['physical-observation.json','technical-analysis.json']:
        row=json.loads((stage/name).read_text())
        require(row['passed'] is True and row['session_analysis_sha256']==sha(stage/'analysis.json'),'Bound C116 receipt')
    final=json.loads((stage/'final-audit.json').read_text());require(final['passed'] is True,'C116 closed')
    for n,h in final['recorded_receipts_sha256'].items():require(sha(stage/n)==h,'C116 closure unchanged')
    for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'C116 source frozen')
    return stage,r

def validation_commands(directory,guard,boot,boot_id):
    """Reuse C114's byte/mode checks with explicit CURRENT stage identity only."""
    session.boot_identity(boot,boot_id)
    resident=session.previous.resident
    path=Path(resident.__file__);source=path.read_text()
    tree=ast.parse(source)
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validation_commands')
    text=ast.get_source_segment(source,node)
    for old,new in [('def validation_commands(value):','def validation_commands(value,guard,boot,boot_id):'),
                    ('code=common()','code=guard'),
                    ("{r['boot_sequence']} {meta['kernel_boot_id']}",'{boot} {boot_id}'),
                    ('C114_RESIDENT_ASSETS_ROM_IDENTITY_METADATA_VALIDATED_NO_UI','C117_CURRENT_CAPSULE_VALID_NO_UI')]:
        text=session.change(text,old,new)
    env=dict(vars(resident));exec(compile(text,__file__+'-validation','exec'),env)
    return env['validation_commands'](directory,guard,boot,boot_id)

def profile_commands(directory):
    d=session.previous.resident.capsule(directory)
    return f'''set -eu
umask 077
mkdir -m 700 {d}/profile
for iteration in 1 2 3;do
 read phase_start ignored < /proc/uptime
 /bin/sh {d}/installed-host.sh {d} check
 read phase_end ignored < /proc/uptime
 printf 'C117_PHASE iteration=%s phase=host_check start=%s end=%s\\n' "$iteration" "$phase_start" "$phase_end"
 read phase_start ignored < /proc/uptime
 /bin/sh {d}/frontend-libs.sh {d} check
 read phase_end ignored < /proc/uptime
 printf 'C117_PHASE iteration=%s phase=provider_check start=%s end=%s\\n' "$iteration" "$phase_start" "$phase_end"
 read phase_start ignored < /proc/uptime
 (cd {d} && sha256sum -c gb-assets.sha256)
 content={d}/profile/content.gb
 [ ! -e "$content" ];[ ! -L "$content" ]
 cp {d}/private.gb "$content";chmod 400 "$content"
 cmp -s {d}/private.gb "$content"
 rm "$content"
 read phase_end ignored < /proc/uptime
 printf 'C117_PHASE iteration=%s phase=content_checks_RAM_copy start=%s end=%s\\n' "$iteration" "$phase_start" "$phase_end"
done
[ ! -e {d}/caller-stage/run.once ];[ ! -L {d}/caller-stage/run.once ]
echo C117_PROFILE_COMPLETE_NO_UI
'''

def metrics(text):
    import re
    rows=re.findall(r'^C117_PHASE iteration=([1-3]) phase=([A-Za-z_]+) start=([0-9]+[.][0-9]+) end=([0-9]+[.][0-9]+)$',text,re.M)
    require(len(rows)==9 and text.splitlines().count('C117_PROFILE_COMPLETE_NO_UI')==1,'Complete nine-phase profile')
    require(sum(line.startswith('C117_PHASE') for line in text.splitlines())==9,'No malformed/extra timing events')
    values={name:[] for name in PHASES};previous_end=Decimal(0)
    for (iteration,name,start,end),(want_i,want_name) in zip(rows,[(str(i),n) for i in range(1,4) for n in PHASES]):
        a,b=Decimal(start),Decimal(end)
        require((iteration,name)==(want_i,want_name) and previous_end<=a<=b and b-a<=120,'Ordered bounded phase timestamps')
        previous_end=b;values[name].append(float((b-a)*1000))
    require(text.count('C77_INSTALLED_HOST_CORE_VALID files=40 operation=check')==3 and
            text.count('C77_PROVIDER_VALID files=7 operation=check')==6,'All unmodified check invocations passed')
    require('operation=launch' not in text,'No launch in check-only profile')
    return {name:{'samples_ms':v,'median_ms':statistics.median(v),'min_ms':min(v),'max_ms':max(v)} for name,v in values.items()}
