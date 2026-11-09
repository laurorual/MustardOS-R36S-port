# SPDX-License-Identifier: MIT
"""C116 resident session on an explicitly observed boot; C112-C115 stay frozen."""
import ast,json,uuid
from pathlib import Path
import phase4_resident_session as previous
from phase4_candidate import sha
from phase4_root_migration import require

REPO,WORK,NATIVE,NAMES=previous.REPO,previous.WORK,previous.NATIVE,previous.NAMES
AREA=WORK/'resident-boot-session'
proof,caller,prep=previous.proof,previous.caller,previous.prep
historical,watch_script,render_online=previous.historical,previous.watch_script,previous.render_online

def qualified():
    result=previous.qualified()
    checks=Path((previous.AREA/'latest-checks').read_text().strip())
    require(checks.resolve().is_relative_to(previous.AREA),'Known C115 checks')
    r=json.loads((checks/'analysis.json').read_text())
    require(r['passed'] is True and r['schema']==115 and r['case_count']==16 and
            r['local_ROM_reads_prohibited'] is True,'Qualified C115 routing')
    for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'C115 source unchanged')
    return result

def boot_identity(boot,boot_id):
    _,r,meta,_=qualified()
    require(type(boot) is int and r['boot_sequence']<=boot<=999999,'Valid resident boot counter')
    require(isinstance(boot_id,str) and str(uuid.UUID(boot_id))==boot_id,'Canonical current boot UUID')
    require((boot==r['boot_sequence'])==(boot_id==meta['kernel_boot_id']),'Resident boot transition agrees')

def current_common(common,old_boot,new_boot,boot_id=None):
    boot_identity(new_boot,boot_id)
    _,_,_,plan=previous.store.installed()
    code=previous.assets.observed_guard(new_boot,boot_id)
    for n,h in plan['files'].items():
        code+=f'''[ -f /{previous.assets.PREFIX}/{n} ];[ ! -L /{previous.assets.PREFIX}/{n} ]
[ "$(stat -c '%u:%g:%a:%h' /{previous.assets.PREFIX}/{n})" = 0:0:644:1 ]
printf '%s  %s\\n' {h} /{previous.assets.PREFIX}/{n} | sha256sum -c - >/dev/null
'''
    code+=f'''[ ! -L /{previous.assets.PREFIX} ];[ "$(stat -c '%u:%g:%a' /{previous.assets.PREFIX})" = 0:0:755 ]
[ "$(find /{previous.assets.PREFIX} -mindepth 1 -maxdepth 1 -print | wc -l)" = 13 ]
'''
    require(code.count(' | sha256sum -c - >/dev/null')==191 and code.splitlines().count('c25_ready')==1,
            'Complete current resident guard and original global readiness')
    return code

def bind(prior,provider,observation,boot,boot_id):
    boot_identity(boot,boot_id);stage,_,_,_=qualified()
    require(observation['boot_sequence']==boot and observation['kernel_boot_id']==boot_id,'Same observed current boot')
    require(observation['C113_analysis_sha256']==sha(stage/'analysis.json') and
            observation['C113_proof_sha256']==sha(proof('internal-rom-imported')/'SHA256SUMS'),'Historical ROM receipt retained')
    return previous.parent.base.legacy.bind(prior,provider,observation,boot,boot_id)

def change(text,old,new):
    require(text.count(old)==1,'Finite C116 adapter: '+old[:90]);return text.replace(old,new)

def rendered_runner():
    text=previous.rendered_runner()
    require(text.count('from phase4_resident_session import ')==2,'Two frozen C115 imports')
    text=text.replace('from phase4_resident_session import ','from phase4_resident_boot_session import ')
    for old,new in [
        ("p.add_argument('--boot', required=True, type=int)","p.add_argument('--boot', required=True, type=int)\np.add_argument('--boot-id', required=True)"),
        ("current_common(context['common'], prior['boot_sequence'], args.boot)","current_common(context['common'], prior['boot_sequence'], args.boot, args.boot_id)"),
        ("REPO / 'port/scripts/phase4_resident_session.py']","REPO / 'port/scripts/phase4_resident_session.py', REPO / 'port/scripts/phase4_resident_boot_session.py']"),
        ("'schema':115, 'C115_resident_runtime_validation':True","'schema':116, 'C116_resident_boot_runtime_validation':True"),
        ('C115 resident source observed boot','C116 resident source observed boot'),
        ('C115 resident source session collected:','C116 resident source session collected:')]:
        text=change(text,old,new)
    ast.parse(text);return text
