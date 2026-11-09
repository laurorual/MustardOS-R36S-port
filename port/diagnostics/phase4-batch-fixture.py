#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C118 rootless container fixture: real lstat/SHA checks, no device access."""
from pathlib import Path
import json,os,shutil,subprocess,sys
plan=json.loads(Path(sys.argv[1]).read_text());out=Path(sys.argv[2]);base=Path('/tmp/c118')
root=base/'root';cap=Path('/run/muos-prefs-data.ABC123');cases=[]

def restore_fixture_owner(path):
    if path.is_symlink():return
    os.chown(path,0,0)
    if path.is_dir():
        path.chmod(0o700)
        for child in path.iterdir():restore_fixture_owner(child)

def reset(kind):
    if base.exists():restore_fixture_owner(base);shutil.rmtree(base)
    if cap.exists():restore_fixture_owner(cap);shutil.rmtree(cap)
    base.mkdir();root.mkdir(mode=0o755);cap.mkdir(mode=0o700)
    for n in ['lib','provider-lib']:(cap/n).mkdir(mode=0o700)
    where=root if kind=='host' else cap
    for row in plan[kind]['files']:
        p=where/row['name'];p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(row['content'].encode());p.chmod(row['mode'])
    if kind=='host':
        for p in root.rglob('*'):
            if p.is_dir():p.chmod(0o755)
    return where

def compare(kind,label,mutate=None,passed=False):
    where=reset(kind)
    if mutate:mutate(where)
    statuses=[]
    for version in ['original','batch']:
        code=f'set -eu\nroot={root}\ncapsule={cap}\n'+plan[kind][version]
        r=subprocess.run(['sh','-c',code],capture_output=True,text=True,timeout=5)
        statuses.append(r.returncode==0)
    assert statuses==[passed,passed],(kind,label,statuses)
    cases.append(kind+'-'+label)

for kind in ['host','provider']:
    leaf=lambda where:where/plan[kind]['files'][0]['name']
    compare(kind,'valid-including-empty-regular-file',passed=True)
    compare(kind,'corrupt-digest',lambda w:leaf(w).write_bytes(b'bad'))
    compare(kind,'missing-leaf',lambda w:leaf(w).unlink())
    compare(kind,'leaf-mode',lambda w:leaf(w).chmod(0o777))
    compare(kind,'leaf-special-mode',lambda w:leaf(w).chmod(0o4644))
    compare(kind,'leaf-owner',lambda w:os.chown(leaf(w),1,0))
    compare(kind,'leaf-group',lambda w:os.chown(leaf(w),0,1))
    compare(kind,'leaf-hardlink',lambda w:os.link(leaf(w),w/'extra-link'))
    compare(kind,'leaf-symlink',lambda w:(leaf(w).rename(w/'other'),leaf(w).symlink_to(w/'other')))
    compare(kind,'leaf-dangling-symlink',lambda w:(leaf(w).unlink(),leaf(w).symlink_to(base/'missing')))
    compare(kind,'leaf-directory',lambda w:(leaf(w).unlink(),leaf(w).mkdir(mode=0o644)))
    compare(kind,'leaf-FIFO-no-hash-hang',lambda w:(leaf(w).unlink(),os.mkfifo(leaf(w),0o644)))
    parent=lambda where:leaf(where).parent
    compare(kind,'parent-mode',lambda w:parent(w).chmod(0o777))
    compare(kind,'parent-owner',lambda w:os.chown(parent(w),1,0))
    compare(kind,'parent-group',lambda w:os.chown(parent(w),0,1))
    compare(kind,'parent-symlink',lambda w:(parent(w).rename(w/'other-dir'),parent(w).symlink_to(w/'other-dir')))
    if kind=='host':
        # A shared high ancestor is checked once rather than once for each leaf.
        compare(kind,'shared-ancestor-mode',lambda w:(w/'usr/share/licenses').chmod(0o700))
        compare(kind,'shared-ancestor-alias',lambda w:((w/'usr/share/licenses').rename(base/'licenses'),(w/'usr/share/licenses').symlink_to(base/'licenses')))
    # Extra legitimate files increase directory nlink; neither validator pins it.
    compare(kind,'directory-nlink-not-pinned',lambda w:(parent(w)/'unrelated-directory').mkdir(),True)

write={'passed':True,'case_count':len(cases),'cases':cases,'real_container_uid':os.getuid(),
       'all_accept_reject_results_equal':True,'original_and_batch_real_stat_SHA_used':True}
(out/'fixture-results.json').write_text(json.dumps(write,indent=2)+'\n')
print('C118 fixture:',len(cases),'accept/refuse equivalence cases passed')
