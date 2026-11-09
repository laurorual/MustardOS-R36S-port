# SPDX-License-Identifier: MIT
"""C118 batched metadata/digests; check-only prototype, frozen originals retained."""
import ast,hashlib,json,re,statistics
from decimal import Decimal
from pathlib import Path,PurePosixPath
import phase4_launch_profile as prior
from phase4_candidate import sha
from phase4_root_migration import require
REPO,WORK,session=prior.REPO,prior.WORK,prior.session
AREA=WORK/'batch-validation'
PHASES=('original_host','batch_host','original_provider','batch_provider')

def qualified():
    prior.qualified();root=session.proof('launch-profile')
    stage=Path((prior.AREA/'latest-complete').read_text().strip())
    require(stage.resolve().is_relative_to(prior.AREA),'Known C117 profile')
    r=json.loads((stage/'analysis.json').read_text());p=json.loads((root/'analysis.json').read_text())
    require(r['passed'] is p['passed'] is True and r['schema']==117 and r['metrics']==p['metrics'],'C117 native profile')
    for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'C117 sources frozen')
    for label in ['before','prepare','validate','profile','validate-after','after','mounts-after','cleanup','post-cleanup-health']:
        require((stage/(label+'.exit')).read_text()=='0\n','C117 closed')
    return stage,r

def original(kind):
    require(kind in ('host','provider'),'Finite validator role')
    name='installed-host.sh' if kind=='host' else 'frontend-libs.sh'
    p=REPO/'port/device/rk-r35s-p0/installed-core-session'/name
    require(p.read_bytes()==(session.proof('resident-boot-session')/'source'/p.relative_to(REPO)).read_bytes(),'Frozen C116 validator')
    text=p.read_text();tag='C73_PINNED_PAYLOAD' if kind=='host' else 'C66_PROVIDER'
    pattern=r'(?m)^while read -r digest '+('mode relative;do' if kind=='host' else 'name; do')+r'\n[\s\S]*?^'+tag+r'\n'
    matches=list(re.finditer(pattern,text));require(len(matches)==1,'Finite original validation loop')
    block=matches[0].group();header,table=block.split("done <<'"+tag+"'\n")
    rows=[]
    for line in table.removesuffix(tag+'\n').splitlines():
        parts=line.split();require(len(parts)==(3 if kind=='host' else 2),'Manifest fields')
        h=parts[0];mode=int(parts[1],8) if kind=='host' else 0o700;name=parts[-1]
        rows.append((h,mode,name))
    require(len(rows)==(40 if kind=='host' else 7),'Complete pinned model')
    return text,block,header,tag,rows

def fragment(rows,prefix,ancestors):
    require(prefix in ('${root%/}','$capsule'),'Finite path prefix')
    require(rows and len(rows)<=40 and len({n for _,_,n in rows})==len(rows),'Unique bounded leaves')
    leaves={}
    for h,mode,n in rows:
        require(re.fullmatch('[0-9a-f]{64}',h) and mode in (0o644,0o755,0o700) and
                re.fullmatch('[A-Za-z0-9_+.-]+(?:/[A-Za-z0-9_+.-]+)*',n) and
                all(x not in ('.','..') for x in n.split('/')),'Finite digest/mode/path')
        leaves[n]=mode
    dirs=sorted({str(p) for _,_,n in rows for p in PurePosixPath(n).parents if str(p)!='.'}) if ancestors else []
    require(not set(dirs)&set(leaves),'No leaf/directory overlap')
    entries=[(n,0o755,True) for n in dirs]+[(n,mode,False) for n,mode in leaves.items()]
    args=' '.join('"'+prefix+'/'+n+'"' for n,_,_ in entries)
    expected='\n'.join('0:0:'+format(mode,'o')+':'+('*' if directory else '1')+':'+format((0o40000 if directory else 0o100000)|mode,'x')+':'+prefix+'/'+n for n,mode,directory in entries)
    hashes='\n'.join(h+'  '+prefix+'/'+n for h,_,n in rows)
    return f'''# C118: one lstat batch; exact type/uid/gid/mode/nlink/path, then all digests.
batch_actual=$(LC_ALL=C stat -c '%u:%g:%a:%h:%f:%n' -- {args}) || exit 64
batch_actual=$(printf '%s\\n' "$batch_actual" | awk 'BEGIN{{FS=OFS=":"}} NF!=6{{exit 64}} $5=="41ed"{{$4="*"}} {{print}}') || exit 64
batch_expected=$(cat <<C118_METADATA
{expected}
C118_METADATA
)
[ "$batch_actual" = "$batch_expected" ] || exit 64
sha256sum -c - >/dev/null <<C118_DIGESTS
{hashes}
C118_DIGESTS
'''

def rendered(kind):
    text,block,_,_,rows=original(kind)
    text=session.change(text,block,fragment(rows,'${root%/}' if kind=='host' else '$capsule',kind=='host'))
    # C118 only qualifies check. Launch remains forbidden until a later integration.
    text=session.change(text,'check:2|launch:2)','check:2)')
    if kind=='host':
        text=session.change(text,'/bin/sh "$capsule/frontend-libs.sh" "$capsule" "$operation"',
                            '/bin/sh "$capsule/batch-provider.sh" "$capsule" "$operation"')
    text=text.replace('C77_INSTALLED_HOST_CORE_VALID','C118_BATCH_HOST_VALID').replace('C77_PROVIDER_VALID','C118_BATCH_PROVIDER_VALID')
    return text

def validation_commands(directory,guard,boot,boot_id):
    return session.change(prior.validation_commands(directory,guard,boot,boot_id),
                          'C117_CURRENT_CAPSULE_VALID_NO_UI','C118_CURRENT_CAPSULE_VALID_NO_UI')

def prototype_commands(directory):
    d=session.previous.resident.capsule(directory);code=''
    for kind in ['host','provider']:
        text=rendered(kind);h=hashlib.sha256(text.encode()).hexdigest();name=d+'/batch-'+kind+'.sh'
        require('C118_SOURCE_EOF' not in text,'Finite source delimiter')
        code+=f'''[ ! -e {name} ];[ ! -L {name} ]
(set -C;cat > {name} <<'C118_SOURCE_EOF'
{text}C118_SOURCE_EOF
)
chmod 700 {name}
[ "$(stat -c %u:%g:%a:%h {name})" = 0:0:700:1 ]
printf '%s  %s\\n' {h} {name} | sha256sum -c - >/dev/null
'''
    code+='echo C118_PROTOTYPES_RAM_ONLY_READY\n';return code

def rendered_runner():
    source=REPO/'port/scripts/run-phase4-launch-profile.py'
    require(source.read_bytes()==(session.proof('launch-profile')/'source'/source.relative_to(REPO)).read_bytes(),'Frozen C117 runner')
    text=session.change(source.read_text(),'import phase4_launch_profile as model','import phase4_batch_validation as model')
    text=text.replace('C117','C118').replace("'schema':117","'schema':118")
    text=text.replace('C116_analysis_sha256','C117_analysis_sha256')
    anchor="    stage=Path(tempfile.mkdtemp(prefix='profile.',dir=model.AREA))"
    text=session.change(text,anchor,"    for kind,h in cr['generated_sha256'].items():\n        model.require(model.hashlib.sha256(model.rendered(kind).encode()).hexdigest()==h,'Exact tested prototype bytes')\n"+anchor)
    old="    validation=model.validation_commands(d,guard,a.boot,a.boot_id)"
    text=session.change(text,old,"    model.require(remote('prototype',guard+model.prototype_commands(d))=='C118_PROTOTYPES_RAM_ONLY_READY\\n','Checked RAM prototypes')\n"+old)
    text=session.change(text,"'unmodified_check_scripts_used':True,'inputs_uploaded':0,",
        "'installed_original_scripts_unchanged':True,'prototype_scripts_RAM_only':True,'prototype_launch_refused':True,\n        'runtime_inputs_uploaded':0,'prototype_shell_programs_uploaded':2,'prototype_sha256':cr['generated_sha256'],")
    text=session.change(text,'proc uptime; kernel tick resolution; includes measurement overhead; warm repeated checks',
                        'proc uptime; timestamps to 0.01 s; measurement overhead included; warm alternating checks')
    ast.parse(text);return text

def profile_commands(directory):
    d=session.previous.resident.capsule(directory)
    commands={'original_host':'installed-host.sh','batch_host':'batch-host.sh','original_provider':'frontend-libs.sh','batch_provider':'batch-provider.sh'}
    text='set -eu\n'
    for i in range(1,4):
        # Alternate pair order to reduce a fixed cache/order advantage.
        order=PHASES if i%2 else ('batch_host','original_host','batch_provider','original_provider')
        for phase in order:
            text+=f'''read phase_start ignored < /proc/uptime
/bin/sh {d}/{commands[phase]} {d} check
read phase_end ignored < /proc/uptime
printf 'C118_PHASE iteration={i} phase={phase} start=%s end=%s\\n' "$phase_start" "$phase_end"
'''
    for kind in ['host','provider']:
        h=hashlib.sha256(rendered(kind).encode()).hexdigest();name=d+'/batch-'+kind+'.sh'
        text+=f'''[ -f {name} ];[ ! -L {name} ];[ "$(stat -c %u:%g:%a:%h {name})" = 0:0:700:1 ]
printf '%s  %s\\n' {h} {name} | sha256sum -c - >/dev/null
'''
    text+=f'''[ ! -e {d}/caller-stage/run.once ];[ ! -L {d}/caller-stage/run.once ]
echo C118_BATCH_PROFILE_COMPLETE_NO_UI
'''
    return text

def metrics(text):
    rows=re.findall(r'^C118_PHASE iteration=([1-3]) phase=([a-z_]+) start=([0-9]+[.][0-9]+) end=([0-9]+[.][0-9]+)$',text,re.M)
    require(len(rows)==12 and sum(x.startswith('C118_PHASE') for x in text.splitlines())==12 and
            text.splitlines().count('C118_BATCH_PROFILE_COMPLETE_NO_UI')==1,'Complete C118 profile')
    order=[(str(i),p) for i in range(1,4) for p in (PHASES if i%2 else ('batch_host','original_host','batch_provider','original_provider'))]
    values={p:[] for p in PHASES};previous=Decimal(0)
    for (i,p,a,b),expected in zip(rows,order):
        start,end=Decimal(a),Decimal(b)
        require((i,p)==expected and previous<=start<=end and end-start<=120,'Ordered bounded C118 samples')
        previous=end;values[p].append(float((end-start)*1000))
    for marker,count in [('C77_INSTALLED_HOST_CORE_VALID files=40 operation=check',3),
                         ('C77_PROVIDER_VALID files=7 operation=check',6),
                         ('C118_BATCH_HOST_VALID files=40 operation=check',3),
                         ('C118_BATCH_PROVIDER_VALID files=7 operation=check',6)]:
        require(text.splitlines().count(marker)==count,'Passed check witnesses '+marker)
    require('operation=launch' not in text,'No launch qualified')
    return {p:{'samples_ms':v,'median_ms':statistics.median(v),'min_ms':min(v),'max_ms':max(v)} for p,v in values.items()}
