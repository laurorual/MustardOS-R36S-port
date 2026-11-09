# SPDX-License-Identifier: MIT
"""C119 explicit RAM adoption; one optimized host, original provider/worker."""
import ast,hashlib,json,re
from pathlib import Path
import phase4_batch_validation as batch
from phase4_candidate import sha
from phase4_root_migration import require
session=batch.session;prior=batch.prior;REPO,WORK=batch.REPO,batch.WORK
AREA=WORK/'batch-caller';NATIVE=REPO/'port/device/rk-r35s-p0/batch-caller'
NAMES=('functions.sh','host.sh','contract.json','LICENSE','payload.sha256','caller.sh')

def qualified():
    batch.qualified();root=session.proof('batch-validation')
    stage=Path((batch.AREA/'latest-complete').read_text().strip())
    require(stage.resolve().is_relative_to(batch.AREA),'Known C118 stage')
    r=json.loads((stage/'analysis.json').read_text());p=json.loads((root/'analysis.json').read_text())
    require(r['passed'] is p['passed'] is True and r['schema']==118 and r['metrics']==p['metrics'],'C118 native qualification')
    for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'Frozen C118 sources')
    for label in ['before','prepare','prototype','validate','profile','validate-after','after','mounts-after','cleanup','post-cleanup-health']:
        require((stage/(label+'.exit')).read_text()=='0\n','C118 safe closure')
    return stage,r

def host_source():
    original,block,_,_,rows=batch.original('host')
    # Preserve check AND launch branches and the original provider dependency.
    return session.change(original,block,batch.fragment(rows,'${root%/}',True)).replace('C77_INSTALLED_HOST_CORE_VALID','C119_HOST_BATCH_VALID')

def bundle():
    qualified();old=session.proof('manual-caller-installed')/'payload'
    data={'functions.sh':(NATIVE/'functions.sh').read_bytes(),'host.sh':host_source().encode(),
          'contract.json':(json.dumps({'schema':119,'scope':'RAM adoption/check only','run_enabled':False,
          'replaced_capsule_scripts':['installed-host.sh'],'provider_worker_and_installed_package_unchanged':True,
          'original_C105_stage_retained':True,'partial_adoption_retry':False,'ROM_or_ELF_included':False},indent=2)+'\n').encode(),
          'LICENSE':(old/'LICENSE').read_bytes()}
    data['payload.sha256']=''.join(hashlib.sha256(data[n]).hexdigest()+' '+n+'\n' for n in NAMES[:4]).encode()
    text=(NATIVE/'caller.in.sh').read_text()
    for key,value in [('@MANIFEST_SHA@',hashlib.sha256(data['payload.sha256']).hexdigest()),
                      ('@LEGACY_MANIFEST_SHA@',sha(old/'payload.sha256')),('@FUNCTIONS_SHA@',hashlib.sha256(data['functions.sh']).hexdigest()),
                      ('@LEGACY_FUNCTIONS_SHA@',sha(old/'functions.sh'))]:
        text=session.change(text,key,value)
    data['caller.sh']=text.encode();return data

def upload_commands(directory):
    d=session.previous.resident.capsule(directory);code=f'mkdir -m 700 {d}/contract-v2\n'
    for name,raw in bundle().items():
        text=raw.decode();require('C119_SOURCE_EOF' not in text,'Finite source delimiter')
        code+=f'''(set -C;cat > {d}/contract-v2/{name} <<'C119_SOURCE_EOF'
{text}C119_SOURCE_EOF
)
chmod 644 {d}/contract-v2/{name}
'''
    return code+bundle_guard(d)+'echo C119_RAM_CONTRACT_READY\n'

def bundle_guard(directory):
    d=session.previous.resident.capsule(directory);code=''
    for n,b in bundle().items():
        code+=f'''[ -f {d}/contract-v2/{n} ];[ ! -L {d}/contract-v2/{n} ];[ "$(stat -c %u:%g:%a:%h {d}/contract-v2/{n})" = 0:0:644:1 ]
printf '%s  %s\\n' {hashlib.sha256(b).hexdigest()} {d}/contract-v2/{n} | sha256sum -c - >/dev/null
'''
    return code

def validation_commands(d,guard,boot,boot_id):
    return session.change(prior.validation_commands(d,guard,boot,boot_id),'C117_CURRENT_CAPSULE_VALID_NO_UI','C119_CURRENT_CAPSULE_VALID_NO_UI')

def adopted_validation(d,guard,boot,boot_id):
    text=validation_commands(d,guard,boot,boot_id);old=session.proof('manual-caller-installed')/'payload/installed-host.sh'
    old_line=f"printf '%s  %s\\n' {sha(old)} {d}/installed-host.sh | sha256sum -c - >/dev/null"
    new_line=f"printf '%s  %s\\n' {hashlib.sha256(host_source().encode()).hexdigest()} {d}/installed-host.sh | sha256sum -c - >/dev/null"
    text=session.change(text,old_line,new_line)
    text=session.change(text,f'cmp /usr/libexec/muos-caller/installed-host.sh {d}/installed-host.sh',f'cmp {d}/contract-v2/host.sh {d}/installed-host.sh')
    text=session.change(text,f'[ ! -e {d}/caller-stage/run.once ];[ ! -L {d}/caller-stage/run.once ]',
        f'[ -d {d}/caller-stage/run.once ];[ ! -L {d}/caller-stage/run.once ]')
    return text+bundle_guard(d)

def refusal_commands(d):
    session.previous.resident.capsule(d)
    return f'''if sh {d}/contract-v2/caller.sh adopt {d};then exit 64;fi
if sh {d}/contract-v2/caller.sh run {d} observe;then exit 64;fi
[ -d {d}/caller-stage/run.once ];[ ! -e {d}/caller-v2-stage/run.once ]
sh {d}/contract-v2/caller.sh staged {d}
echo C119_REPEAT_AND_RUN_REFUSED_NO_UI
'''

def profile_commands(d):
    session.previous.resident.capsule(d)
    return f'''sh {d}/contract-v2/caller.sh staged {d}
read phase_start ignored < /proc/uptime
sh {d}/installed-host.sh {d} check
read phase_end ignored < /proc/uptime
printf 'C119_HOST_CHECK start=%s end=%s\\n' "$phase_start" "$phase_end"
echo C119_ADOPTED_CONTRACT_VERIFIED_NO_UI
'''

def metrics(text):
    matches=re.findall(r'^C119_HOST_CHECK start=([0-9]+[.][0-9]+) end=([0-9]+[.][0-9]+)$',text,re.M)
    require(len(matches)==1 and text.splitlines().count('C119_HOST_BATCH_VALID files=40 operation=check')==1 and
            text.splitlines().count('C77_PROVIDER_VALID files=7 operation=check')==1 and
            text.splitlines().count('C119_ADOPTED_CONTRACT_VERIFIED_NO_UI')==1 and 'operation=launch' not in text,'Native adopted check')
    from decimal import Decimal
    a,b=map(Decimal,matches[0]);require(a<=b and b-a<=120,'Bounded check interval')
    return {'adopted_host_check_ms':float((b-a)*1000),'samples':1,'actual_launch_or_graphical_timing':False}

def rendered_runner():
    source=REPO/'port/scripts/run-phase4-launch-profile.py'
    require(source.read_bytes()==(session.proof('launch-profile')/'source'/source.relative_to(REPO)).read_bytes(),'Frozen C117 runner')
    text=session.change(source.read_text(),'import phase4_launch_profile as model','import phase4_batch_caller as model')
    text=text.replace('C117','C119').replace("'schema':117","'schema':119").replace('C116_analysis_sha256','C118_analysis_sha256')
    anchor="    stage=Path(tempfile.mkdtemp(prefix='profile.',dir=model.AREA))"
    text=session.change(text,anchor,"    for n,b in model.bundle().items():\n        model.require(model.hashlib.sha256(b).hexdigest()==cr['bundle_sha256'][n],'Exact tested bundle')\n"+anchor)
    anchor='    validation=model.validation_commands(d,guard,a.boot,a.boot_id)'
    text=session.change(text,anchor,"    model.require(remote('bundle',guard+model.upload_commands(d))=='C119_RAM_CONTRACT_READY\\n','RAM bundle')\n    model.require(remote('contract-check',guard+f'sh {d}/contract-v2/caller.sh check\\n')=='C119_CONTRACT_CHECK_OK_NO_UI\\n','Native contract check')\n"+anchor)
    anchor="    measured=model.metrics(remote('profile',guard+model.profile_commands(d)))"
    text=session.change(text,anchor,"    model.require(remote('adopt',guard+f'sh {d}/contract-v2/caller.sh adopt {d}\\n')=='C119_ADOPTED_CAPSULE_READY_NO_UI\\n','Native adoption')\n    model.require(remote('refusals',guard+model.refusal_commands(d))=='C119_STAGED_CHECK_OK_NO_UI\\nC119_REPEAT_AND_RUN_REFUSED_NO_UI\\n','No retry or run')\n"+anchor)
    text=session.change(text,"remote('validate-after',validation)","remote('validate-after',model.adopted_validation(d,guard,a.boot,a.boot_id))")
    text=session.change(text,"'unmodified_check_scripts_used':True,'inputs_uploaded':0,",
       "'original_installed_scripts_unchanged':True,'only_capsule_host_replaced':True,'legacy_stage_retained':True,'legacy_RAM_run_once_reserved':True,\n        'adoption_contract_version':119,'run_enabled':False,'runtime_inputs_uploaded':0,'RAM_contract_files_uploaded':6,'bundle_sha256':cr['bundle_sha256'],")
    text=session.change(text,'proc uptime; kernel tick resolution; includes measurement overhead; warm repeated checks',
                        'proc uptime; timestamps to 0.01 s; one adopted check; no frequency control')
    ast.parse(text);return text
