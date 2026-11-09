# SPDX-License-Identifier: MIT
"""C120 bounded batch-host run; frozen C119 adoption and C116 lifecycle retained."""
import ast,hashlib,json
from pathlib import Path
import phase4_batch_caller as previous
from phase4_candidate import sha
from phase4_root_migration import require
REPO,WORK,session=previous.REPO,previous.WORK,previous.session
AREA=WORK/'batch-run';NAMES=previous.NAMES

def qualified():
    previous.qualified();proof=session.proof('batch-caller')
    stage=Path((previous.AREA/'latest-complete').read_text().strip())
    require(stage.resolve().is_relative_to(previous.AREA),'Known C119 stage')
    r=json.loads((stage/'analysis.json').read_text());p=json.loads((proof/'analysis.json').read_text())
    require(r['passed'] is p['passed'] is True and r['schema']==119 and r['metrics']==p['metrics'] and r['run_enabled'] is False,'Qualified check-only adoption')
    for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'C119 frozen source')
    for label in ['adopt','refusals','profile','validate-after','after','mounts-after','cleanup','post-cleanup-health']:
        require((stage/(label+'.exit')).read_text()=='0\n','C119 safe closure')
    return stage,r

def functions():
    text=(previous.NATIVE/'functions.sh').read_text().replace('c119','c120').replace('C119','C120').replace('v2','v3')
    text=session.change(text,'the original C105 package/stage stays on disk.','the installed C105 package and original RAM metadata are retained.')
    return text+'''\nc120_run() {
    [ "$#" = 2 ] && [ "$2" = observe ] || return 64
    c105_package && c105_dependencies && caller_exec platform && c120_staged "$1" || return 64
    mkdir -m 700 "$1/caller-v3-stage/run.once" || return 64
    # Consume before exec. Failure never enables a second dispatch.
    caller_exec run "$1"
}
'''

def bundle():
    qualified();legacy=session.proof('manual-caller-installed')/'payload'
    data={'functions.sh':functions().encode(),'host.sh':previous.host_source().replace('C119_HOST_BATCH_VALID','C120_HOST_BATCH_VALID').encode(),
      'contract.json':(json.dumps({'schema':120,'scope':'RAM adoption and bounded load-only run','run_enabled':True,
      'mode':'observe','outer_seconds':240,'child_seconds':210,'game_seconds':45,
      'original_installed_worker':True,'provider_unchanged':True,'retry':False,'ROM_or_ELF_included':False},indent=2)+'\n').encode(),
      'LICENSE':(legacy/'LICENSE').read_bytes()}
    data['payload.sha256']=''.join(hashlib.sha256(data[n]).hexdigest()+' '+n+'\n' for n in NAMES[:4]).encode()
    text=(previous.NATIVE/'caller.in.sh').read_text().replace('v2','v3').replace('c119','c120').replace('C119','C120')
    text=session.change(text,'check:1|adopt:2|staged:2)','check:1|adopt:2|staged:2|run:3)')
    text=session.change(text,' *) return 64;;', ''' run) exec "$2/runner" 240 "$2/watchdog" /usr/libexec/muos-session/mount-namespace /bin/sh "$caller_root/worker.sh" "$2" observe ;;
 *) return 64;;''')
    text=session.change(text,' # C120 qualifies adoption/check only. A later explicit version will enable run.', ' run:3) c120_run "$2" "$3" ;;')
    for key,value in [('@MANIFEST_SHA@',hashlib.sha256(data['payload.sha256']).hexdigest()),('@LEGACY_MANIFEST_SHA@',sha(legacy/'payload.sha256')),
                      ('@FUNCTIONS_SHA@',hashlib.sha256(data['functions.sh']).hexdigest()),('@LEGACY_FUNCTIONS_SHA@',sha(legacy/'functions.sh'))]:
        text=session.change(text,key,value)
    data['caller.sh']=text.encode();return data

def upload_commands(d):
    session.previous.resident.capsule(d);text=f'mkdir -m 700 {d}/contract-v3\n'
    for n,b in bundle().items():
        value=b.decode();require('C120_SOURCE_EOF' not in value,'Finite code delimiter')
        text+=f"(set -C;cat > {d}/contract-v3/{n} <<'C120_SOURCE_EOF'\n{value}C120_SOURCE_EOF\n)\nchmod 644 {d}/contract-v3/{n}\n"
    return text+bundle_guard(d)+'echo C120_RAM_CONTRACT_READY\n'

def bundle_guard(d):
    session.previous.resident.capsule(d);text=''
    for n,b in bundle().items():
        text+=f'''[ -f {d}/contract-v3/{n} ];[ ! -L {d}/contract-v3/{n} ];[ "$(stat -c %u:%g:%a:%h {d}/contract-v3/{n})" = 0:0:644:1 ]
printf '%s  %s\\n' {hashlib.sha256(b).hexdigest()} {d}/contract-v3/{n} | sha256sum -c - >/dev/null
'''
    return text

historical,current_common,bind,watch_script= session.historical,session.current_common,session.bind,session.watch_script
NATIVE,caller,prep,proof=session.NATIVE,session.caller,session.prep,session.proof

def render_online(online):
    text=session.render_online(online)
    anchor="remote('installed-host-check',common+f'/bin/sh {directory}/installed-host.sh {directory} check\\n')"
    text=session.change(text,anchor,"""remote('batch-bundle',common+batch.upload_commands(directory),timeout=120)
remote('batch-adopt',common+f'sh {directory}/contract-v3/caller.sh adopt {directory}\\n',timeout=120)
remote('batch-stage',common+f'sh {directory}/contract-v3/caller.sh staged {directory}\\n',timeout=120)
"""+anchor)
    text=session.change(text,"entry=f'/bin/sh /usr/libexec/muos-caller/caller.sh run {directory} {native_mode}'",
                            "entry=f'/bin/sh {directory}/contract-v3/caller.sh run {directory} {native_mode}'")
    text=session.change(text,"remote('caller-execution',common+f'", "remote('caller-execution',common+batch.bundle_guard(directory)+f'")
    anchor='cmp /usr/libexec/muos-caller/worker.sh {directory}/worker.sh\\n'
    text=session.change(text,anchor,anchor+'''[ -d {directory}/caller-v3-stage/run.once ];[ ! -L {directory}/caller-v3-stage/run.once ]\\n[ "$(stat -c %u:%g:%a {directory}/caller-v3-stage/run.once)" = 0:0:700 ]\\ncmp {directory}/contract-v3/host.sh {directory}/installed-host.sh\\nfor n in ready boot package;do cmp {directory}/caller-stage/$n {directory}/caller-v3-before/$n;done\\n''')
    text=session.change(text,'echo C106_INSTALLED_CALLER_RUN_ONCE_CONFIRMED\\n', 'echo C120_BATCH_CALLER_RUN_ONCE_CONFIRMED\\n')
    ast.parse(text);return text

def rendered_runner():
    text=session.rendered_runner()
    require(text.count('from phase4_resident_boot_session import ')==2,'Frozen runner import count')
    text=text.replace('from phase4_resident_boot_session import ','from phase4_batch_run import ')
    text=session.change(text,"qualification_stage, _, _, _ = qualified()", "qualified()\nqualification_stage, _, _, _ = session.qualified()")
    text=session.change(text,'qualified, caller, proof, prep','qualified, caller, proof, prep, session')
    text=session.change(text,"sources = [Path(__file__),", "sources = [REPO/'port/scripts/phase4_batch_run.py', REPO/'port/scripts/check-phase4-batch-run.py', Path(__file__),")
    text=session.change(text,'files, expected = context[\'files\'], context[\'expected\']',
      "import phase4_batch_run as batch\nfor n,b in batch.bundle().items():\n    assert hashlib.sha256(b).hexdigest()==check_report['bundle_sha256'][n]\nfiles, expected = context['files'], context['expected']")
    text=session.change(text,'import argparse, ipaddress, json, re, subprocess, tempfile','import argparse, ipaddress, json, re, subprocess, tempfile, hashlib')
    text=session.change(text,'prepared_inputs={})','prepared_inputs={}, batch=batch)')
    text=session.change(text,"'C106_INSTALLED_CALLER_RUN_ONCE_CONFIRMED\\n'","'C120_BATCH_CALLER_RUN_ONCE_CONFIRMED\\n'")
    text=session.change(text,"game.count('C77_INSTALLED_HOST_CORE_VALID files=40 operation=launch')", "game.count('C120_HOST_BATCH_VALID files=40 operation=launch')")
    text=session.change(text,"'schema':116, 'C116_resident_boot_runtime_validation':True", "'schema':120, 'C120_batch_run_runtime_validation':True, 'RAM_contract_files_uploaded':6, 'bundle_sha256':check_report['bundle_sha256']")
    text=session.change(text,"'installed_entrypoint_used':True", "'installed_entrypoint_used':False, 'versioned_RAM_entrypoint_used':True")
    text=session.change(text,"'caller_scripts_transferred_by_host':False", "'legacy_caller_scripts_transferred_by_host':False, 'adopted_host_code_uploaded':True")
    text=text.replace('C116 resident source observed boot','C120 batch caller observed boot').replace('C116 resident source session collected:','C120 batch caller session collected:')
    ast.parse(text);return text

# Native automated qualification deliberately never dispatches the graphical run.
def validation_commands(d,guard,boot,boot_id):
    return previous.validation_commands(d,guard,boot,boot_id).replace('C119','C120')

def adopted_validation(d,guard,boot,boot_id):
    text=previous.adopted_validation(d,guard,boot,boot_id)
    old=previous.bundle_guard(d);require(text.endswith(old),'Original bundle guard suffix')
    text=text[:-len(old)]
    a=hashlib.sha256(previous.host_source().encode()).hexdigest();b=hashlib.sha256(bundle()['host.sh']).hexdigest()
    text=session.change(text,a,b)
    # Replace C119's bundle guard in full, not its embedded script digests.
    return text.replace('contract-v2','contract-v3').replace('C119','C120')+bundle_guard(d)

def refusal_commands(d):
    session.previous.resident.capsule(d)
    return f'''if sh {d}/contract-v3/caller.sh adopt {d};then exit 64;fi
if sh {d}/contract-v3/caller.sh run {d} save;then exit 64;fi
if sh {d}/contract-v3/caller.sh run {d};then exit 64;fi
[ -d {d}/caller-stage/run.once ];[ ! -e {d}/caller-v3-stage/run.once ]
sh {d}/contract-v3/caller.sh staged {d}
echo C120_REPEAT_AND_INVALID_RUN_REFUSED_NO_UI
'''

def profile_commands(d):return previous.profile_commands(d).replace('contract-v2','contract-v3').replace('C119','C120')
def metrics(text):return previous.metrics(text.replace('C120','C119'))

def native_runner():
    text=previous.rendered_runner()
    text=session.change(text,'import phase4_batch_caller as model','import phase4_batch_run as model')
    text=text.replace('C119','C120').replace("'schema':119","'schema':120").replace('C118_analysis_sha256','C119_analysis_sha256')
    text=text.replace('/contract-v2/','/contract-v3/')
    text=session.change(text,'C120_REPEAT_AND_RUN_REFUSED_NO_UI','C120_REPEAT_AND_INVALID_RUN_REFUSED_NO_UI')
    text=session.change(text,"'adoption_contract_version':119,'run_enabled':False", "'adoption_contract_version':120,'run_enabled':True,'native_graphical_dispatch_qualified':False")
    ast.parse(text);return text
