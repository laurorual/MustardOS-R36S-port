# SPDX-License-Identifier: MIT
"""C76 immutable package inputs and public pre-existing system model."""
from pathlib import Path
import ast, json
from phase4_candidate import sha, sums

REPO=Path(__file__).resolve().parents[2];WORK=REPO/'build/phase4'
AREA=WORK/'gambatte-install';NATIVE=REPO/'port/device/rk-r35s-p0/gambatte-install'
ROOTS=['opt/muos/share/core','usr/share/muos-gambatte','usr/share/licenses/muos-gambatte']
def context():
    parents={}
    for name in ['gambatte-package','installed-provider-return','provider-upgrade-native','muxretro-installed']:
        proof=REPO/'dist/phase4'/name
        for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h,(name,n)
        parents[name]=sha(proof/'SHA256SUMS')
    source=WORK/'gambatte-package/build.tgnlr06f'
    r=json.loads((source/'analysis.json').read_text())
    assert (source/'analysis.json').read_bytes()==(REPO/'dist/phase4/gambatte-package/analysis.json').read_bytes()
    assert r['passed'] and r['byte_identical_to_C49_C73_core']
    for n,h in r['source_sha256'].items():assert sha(REPO/n)==h,n
    added=json.loads((source/'composition-added.json').read_text())
    names=sorted(n for n,v in added.items() if v['type']=='file')
    dirs=sorted((n for n,v in added.items() if v['type']=='directory'),key=lambda n:(len(Path(n).parts),n))
    assert len(names)==9 and len(dirs)==8
    for n in names:
        p=source/'target'/n
        assert not p.is_symlink() and sha(p)==added[n]['sha256'] and added[n]['mode']==0o644
    c72=WORK/'provider-upgrade-native/install.otw0lflu'
    plan=json.loads((c72/'plan.json').read_text());binding=json.loads((c72/'binding.json').read_text())
    qualified=json.loads((REPO/'dist/phase4/provider-upgrade-native/analysis.json').read_text())
    assert qualified['plan_sha256']==sha(c72/'plan.json')
    preserved={n.lstrip('/'):h for n,h in sums(c72/'payload/preserved.sha256').items()}
    assert len(preserved)==101
    for n,row in plan['after'].items():assert n not in preserved;preserved[n]=row['sha256']
    assert len(preserved)==132
    old_source=REPO/'port/scripts/run-phase4-provider-upgrade.py'
    assert sha(old_source)==binding['source_sha256'][str(old_source.relative_to(REPO))]
    nodes=[n for n in ast.parse(old_source.read_text()).body if isinstance(n,ast.Assign)
           and any(isinstance(t,ast.Name) and t.id=='base' for t in n.targets)]
    assert len(nodes)==1
    common=ast.literal_eval(nodes[0].value)
    for n,row in sorted(plan['after'].items()):
        common+=f'[ ! -L /{n} ];[ "$(stat -c \'%u:%g:%a:%h\' /{n})" = 0:0:{row["mode"]:o}:1 ]\n'
    for n,h in sorted(preserved.items()):
        common+=f"printf '%s  %s\\n' {h} /{n} | sha256sum -c - >/dev/null\n"
    return source,r,added,names,dirs,preserved,parents,common

INFRA='''for name in udevd wpa_supplicant udhcpc dropbear;do
for pid in $(pidof "$name");do
[ "$(awk '/^PPid:/ {print $2}' /proc/$pid/status)" = 1 ] || continue
printf '%s %s %s\\n' "$name" "$pid" "$(awk '{print $22}' /proc/$pid/stat)"
done;done
'''
