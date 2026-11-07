#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C102 transaction fault injection on disposable regular directory trees."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys

stage=Path(sys.argv[1]);template=(stage/'template.dat').read_bytes()
transaction=Path('/port/device/rk-r35s-p0/c79-layout-install/transaction.sh')
cases=[]

def run(name,setup='',failure=None,retained=False,hook=''):
    base=Path('/tmp/c102')/name;base.mkdir(parents=True)
    root=base/'root';payload=base/'payload';root.mkdir(mode=0o755);payload.mkdir()
    for d in ['etc','mnt']: (root/d).mkdir(mode=0o755)
    (root/'etc/foundation').write_bytes(b'untouched foundation\n');(root/'etc/foundation').chmod(0o644)
    (payload/'asound.conf').write_bytes(template);(payload/'asound.conf').chmod(0o644)
    (payload/'foundation.sha256').write_text(hashlib.sha256((root/'etc/foundation').read_bytes()).hexdigest()+'  etc/foundation\n')
    script='''set -eu
umask 077
layout_root=$1;layout_payload=$2
layout_rw=0;layout_temporary=0;layout_published=0;layout_directory=0
failed=0
. /port/device/rk-r35s-p0/c79-layout-install/transaction.sh
layout_exec() {
    printf '%s\\n' "$1" >> "$layout_payload/events"
    case "$1" in rw) layout_rw=1;;esac
'''+hook+'''
    case "$1" in '''+(failure or 'never')+''')
        if [ "$failed" = 0 ];then failed=1;return 1;fi;;esac
    return 0
}
'''+setup+'''
'''
    if name=='success':
        script+='c102_apply;[ "$layout_rw" = 0 ];c102_verify\n'
    else:
        script+='''if c102_apply;then echo unexpected_success;exit 1;fi
if [ "$layout_rw" = 1 ];then
'''
        script+=('if c102_rollback;then echo unsafe_rollback;exit 1;fi\n' if retained else 'c102_rollback\n')
        script+='fi\n'
    result=subprocess.run(['sh','-c',script,'fixture',str(root),str(payload)],capture_output=True,text=True)
    (stage/(name+'.log')).write_text(result.stdout+result.stderr)
    assert result.returncode==0,(name,result.stdout,result.stderr)
    events=(payload/'events').read_text().splitlines() if (payload/'events').exists() else []
    if name=='success':
        assert (root/'etc/asound.conf').read_bytes()==template and (root/'etc/asound.conf').stat().st_mode&0o777==0o644
        assert not list((root/'mnt/mmc').iterdir()) and events[-3:]==['verify','sync','ro']
    elif retained:
        assert (root/'etc/asound.conf').exists() or (root/'etc/asound.conf.c102-new').exists()
        if name=='directory-neighbor':assert (root/'mnt/mmc/foreign').read_bytes()==b'foreign'
        if name=='partial-temporary':assert (root/'etc/asound.conf.c102-new').read_bytes()==b'partial'
        if name=='foundation-changed':assert (root/'etc/foundation').read_bytes()==b'changed'
    elif failure:
        assert not (root/'etc/asound.conf').exists() and not (root/'mnt/mmc').exists()
        assert not (root/'etc/asound.conf.c102-new').exists()
        assert 'rw' not in events or events[-1]=='ro'
    else:assert 'rw' not in events,(name,events)
    cases.append(name);shutil.rmtree(base)

run('success')
for name,setup in {
    'existing-file':'printf foreign > "$layout_root/etc/asound.conf"',
    'existing-directory':'mkdir "$layout_root/mnt/mmc"',
    'existing-temporary':'printf foreign > "$layout_root/etc/asound.conf.c102-new"',
    'dangling-destination':'ln -s missing "$layout_root/etc/asound.conf"',
    'dangling-temporary':'ln -s missing "$layout_root/etc/asound.conf.c102-new"',
    'directory-alias':'ln -s missing "$layout_root/mnt/mmc"',
    'etc-alias':'mv "$layout_root/etc" "$layout_root/realetc";ln -s realetc "$layout_root/etc"',
    'mnt-alias':'mv "$layout_root/mnt" "$layout_root/realmnt";ln -s realmnt "$layout_root/mnt"',
    'parent-mode':'chmod 777 "$layout_root/mnt"',
    'root-mode':'chmod 777 "$layout_root"',
    'foreign-mnt-file':'printf foreign > "$layout_root/mnt/foreign"',
    'foreign-mnt-directory':'mkdir "$layout_root/mnt/foreign"',
    'template-wrong-bytes':'printf bad > "$layout_payload/asound.conf"',
    'template-mode':'chmod 600 "$layout_payload/asound.conf"',
    'template-hardlink':'ln "$layout_payload/asound.conf" "$layout_payload/alias"',
    'template-alias':'mv "$layout_payload/asound.conf" "$layout_payload/real";ln -s real "$layout_payload/asound.conf"',
    'foundation-wrong':'printf changed > "$layout_root/etc/foundation"',
}.items():run(name,setup)
for point in ['guard','rw','staged','linked','published','directory','verify','sync','ro']:
    run('failure-'+point,failure=point)
for name,hook in {
    'partial-temporary':'[ "$1" != staged ] || { printf partial > "$layout_root/etc/asound.conf.c102-new";return 1; }',
    'changed-mode':'[ "$1" != staged ] || { chmod 600 "$layout_root/etc/asound.conf.c102-new";return 1; }',
    'foreign-hardlink':'[ "$1" != published ] || { ln "$layout_root/etc/asound.conf" "$layout_root/etc/foreign";return 1; }',
    'directory-neighbor':'[ "$1" != directory ] || { printf foreign > "$layout_root/mnt/mmc/foreign";return 1; }',
    'foundation-changed':'[ "$1" != directory ] || { printf changed > "$layout_root/etc/foundation";return 1; }',
    'foreign-destination':'[ "$1" != staged ] || { printf foreign > "$layout_root/etc/asound.conf";return 1; }',
    'changed-directory-mode':'[ "$1" != directory ] || { chmod 777 "$layout_root/mnt/mmc";return 1; }',
    'directory-new-symlink':'[ "$1" != directory ] || { rmdir "$layout_root/mnt/mmc";ln -s missing "$layout_root/mnt/mmc";return 1; }',
}.items():run(name,hook=hook,retained=True)
(stage/'fixture-results.json').write_text(json.dumps({'passed':True,'cases':cases,'case_count':len(cases)},indent=2)+'\n')
print('C102 transaction fixtures passed:',len(cases))
