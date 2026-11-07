# SPDX-License-Identifier: MIT
"""C109 runtime through the installed preparer and the installed caller."""
from pathlib import Path
import ast,json
import phase4_capsule_prepare_v3 as prep
from phase4_candidate import sha
from phase4_root_migration import require

base=prep.base;caller=base.caller
REPO,WORK,NATIVE,NAMES=base.REPO,base.WORK,base.NATIVE,base.NAMES
AREA=WORK/'prepared-capsule-session';proof=base.proof

def qualified():
    prep.qualified();root=proof('capsule-preparer-v3-installed')
    stage=Path((prep.AREA/'latest-complete').read_text().strip())
    require(stage.resolve().is_relative_to(prep.AREA),'Known C111 install')
    r=json.loads((stage/'analysis.json').read_text());public=json.loads((root/'analysis.json').read_text())
    require(r['passed'] is True and r['schema']==111 and all(public[k]==v for k,v in r.items()),'Frozen C111 native proof')
    require(r['files_added']==6 and r['root_read_only'] is r['RAM_removed'] is
        r['native_empty_preparation_refused_without_mutation'] is True,'Closed C111 installation')
    for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'Frozen C107/C111 source changed')
    plan=json.loads((stage/'plan.json').read_text());meta=json.loads((stage/'manifest.json').read_text())
    require(r['plan_sha256']==sha(stage/'plan.json'),'C111 plan binding')
    require((stage/'cleanup.stdout').read_text()=='C111_RAM_REMOVED_ROOT_RO\n','Authentic cleanup')
    return stage,r,meta,plan

def historical():qualified();return base.historical()

def current_common(common,old_boot,new_boot):
    _,r,meta,plan=qualified();require(type(new_boot) is int and new_boot==r['boot_sequence'],'Same observed C111 boot')
    code=prep.common();require(meta['kernel_boot_id'] in code,'Same C106/C111 boot identity')
    for n,h in plan['files'].items():
        code+=f'''[ -f /{prep.PREFIX}/{n} ];[ ! -L /{prep.PREFIX}/{n} ]
[ "$(stat -c '%u:%g:%a:%h' /{prep.PREFIX}/{n})" = 0:0:644:1 ]
printf '%s  %s\\n' {h} /{prep.PREFIX}/{n} | sha256sum -c - >/dev/null
'''
    code+=f'''[ ! -L /{prep.PREFIX} ];[ "$(stat -c '%u:%g:%a' /{prep.PREFIX})" = 0:0:755 ]
[ "$(find /{prep.PREFIX} -mindepth 1 -maxdepth 1 -print | wc -l)" = 6 ]
'''
    return code

def bind(prior,provider,observation,boot,boot_id):
    stage,r,meta,_=qualified()
    require(type(boot) is int and boot==r['boot_sequence'] and boot_id==meta['kernel_boot_id'],'Exact C111 boot')
    require(observation['C111_analysis_sha256']==sha(stage/'analysis.json') and
        observation['C111_proof_sha256']==sha(proof('capsule-preparer-v3-installed')/'SHA256SUMS'),'C111 observation binding')
    return base.legacy.bind(prior,provider,observation,boot,boot_id)

def watch_script(directory):
    code=base.watch_script(directory)
    anchor='[ -d '+directory+' ] || exit 0\n'
    require(code.count(anchor)==1,'Known watcher lifecycle anchor')
    code=code.replace('worker_seen=','worker_seen=;timing_selected=;timing_present=',1)
    events=f'''if [ -z "$timing_selected" ] && grep -qx 'C46_NATIVE_SELECTION_CONSUMED options_quarantined=1' {directory}/state/core.log 2>/dev/null;then
 timing_selected=1;printf 'C109_EVENT selection_consumed uptime=%s\\n' "$(cut -d' ' -f1 /proc/uptime)"
fi
if [ -z "$timing_present" ] && grep -q '^C44_FIRST_PRESENT seconds=45 ' {directory}/state/game.log 2>/dev/null;then
 timing_present=1;printf 'C109_EVENT first_game_present uptime=%s\\n' "$(cut -d' ' -f1 /proc/uptime)"
fi
'''
    return code.replace(anchor,anchor+events)

def render_online(online):
    text=base.render_online(online)
    def change(old,new):
        nonlocal text
        require(text.count(old)==1,'Finite C109 online anchor '+old[:60]);text=text.replace(old,new)
    change("f'mkdir -m 700 {directory}/lib {directory}/provider-lib\\n'","f'mkdir -m 700 {directory}/inputs\\n'")
    change(' if n in caller_scripts:continue',' if n not in prepared_inputs:continue')
    change("ssh+['cat > '+directory+'/'+n]","ssh+['cat > '+directory+'/inputs/'+prepared_inputs[n]]")
    start=text.index('code=common+f"sh /usr/libexec/muos-caller/caller.sh stage')
    end=text.index("remote('prepare',code,timeout=120)",start)
    text=text[:start]+'''code=common+f"chmod 700 {directory}/inputs/*\\nsh /usr/libexec/muos-capsule-v3/prepare.sh prepare {directory}\\n"
'''+text[end:]
    anchor="remote('prepare',code,timeout=120)"
    change(anchor,anchor+'''\nassert (stage/'prepare.stdout').read_text()=='C107_CAPSULE_PREPARED_RAM_ONLY\\n' ''')
    anchor="echo C106_INSTALLED_CALLER_RUN_ONCE_CONFIRMED\\n')"
    change(anchor,"grep -qx C107_CAPSULE_READY {directory}/preparation.once/ready\\n"+anchor)
    ast.parse(text);return text

def rendered_runner():
    text=base.rendered_runner()
    require(text.count('from phase4_installed_caller_session import ')==2,'C106 import anchors')
    text=text.replace('from phase4_installed_caller_session import ','from phase4_prepared_capsule_session import ')
    changes={
        "REPO / 'port/scripts/phase4_installed_caller_session.py'":"REPO / 'port/scripts/phase4_prepared_capsule_session.py'",
        'caller_scripts=caller.SCRIPTS)':'caller_scripts=caller.SCRIPTS, prepared_inputs=prep.INPUTS)',
        "'schema':106, 'C106_installed_caller_runtime_validation':True":"'schema':109, 'C109_local_preparation_runtime_validation':True, 'capsule_metadata_generated_on_device':True, 'public_assets_copied_locally':7, 'public_assets_uploaded_by_host':4",
        'qualified, caller, proof':'qualified, caller, proof, prep',
        'C106 installed caller observed boot':'C109 local preparation observed boot',
        'C106 installed caller session collected:':'C109 local preparation session collected:',
    }
    for old,new in changes.items():require(text.count(old)==1,'Finite C109 runner anchor '+old[:60]);text=text.replace(old,new)
    require(text.count('C105_analysis_sha256')==2 and text.count('C105_proof_sha256')==2,'Two C111 binding pairs')
    text=text.replace('C105_analysis_sha256','C111_analysis_sha256').replace('C105_proof_sha256','C111_proof_sha256')
    require(text.count("proof('manual-caller-installed')")==2,'Two C111 parent proof anchors')
    text=text.replace("proof('manual-caller-installed')","proof('capsule-preparer-v3-installed')")
    ast.parse(text);return text
