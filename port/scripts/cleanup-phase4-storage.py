#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Remove completed synthetic test trees; keep reports, sources and artifacts."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,re,shutil,stat

REPO=Path(__file__).resolve().parents[2];BUILD=REPO/'build';WORK=BUILD/'phase4'

def candidates():
    targets=[]
    for area in sorted(WORK.iterdir()):
        if not area.is_dir() or area.is_symlink() or area.name in {'private','root-migration','offline-backup'}:continue
        for stage in sorted(area.iterdir()):
            if not stage.is_dir() or stage.is_symlink() or 'checks' not in stage.name:continue
            report=stage/'analysis.json'
            if not report.is_file():continue
            try:r=json.loads(report.read_text())
            except (ValueError,OSError):continue
            if r.get('passed') is not True:continue
            for child in sorted(stage.iterdir()):
                if child.is_dir() and not child.is_symlink() and (child.name in {'fixture','fixtures','fixture-root'} or re.fullmatch(r'case-[0-9]{3}',child.name)):
                    targets.append(child)
    return targets

def allocated(path):
    total=path.lstat().st_blocks*512
    for base,dirs,files in os.walk(path,followlinks=False):
        for n in dirs+files:total+=(Path(base)/n).lstat().st_blocks*512
    return total

def compiler_candidates():
    targets=[]
    for output in [WORK/'rootfs-output',WORK/'graphics-config/output']:
        for p in sorted((output/'build').iterdir()):
            if not p.is_dir() or p.is_symlink():continue
            # Used directly by prepare-foundation, network auditing or recipes.
            if p.name.startswith(('rockchip-mali-','libnl-','muos-','host-skeleton','buildroot-config')):continue
            targets.append(p)
    return targets

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true')
    p.add_argument('--compilation-cache',action='store_true',help='Discard rebuildable package intermediates, preserving installed SDKs')
    a=p.parse_args();targets=compiler_candidates() if a.compilation_cache else candidates();before=shutil.disk_usage(REPO).free
    records=[{'path':str(t.relative_to(REPO)),'allocated_bytes':allocated(t)} for t in targets]
    print(json.dumps({'discardable_trees':len(records),'allocated_bytes':sum(r['allocated_bytes'] for r in records),'apply':a.apply},indent=2),flush=True)
    if not a.apply:return
    mounts=[line.split()[4] for line in Path('/proc/self/mountinfo').read_text().splitlines()]
    for target in targets:
        assert target.resolve().is_relative_to(WORK) and not target.is_symlink()
        assert not any(m==str(target) or m.startswith(str(target)+'/') for m in mounts),'Mounted fixture'
    audit=BUILD/'cleanup';audit.mkdir(exist_ok=True)
    report=audit/(('compiler-cache-' if a.compilation_cache else 'fixtures-')+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json')
    result={'scope':'rebuildable compilation intermediates' if a.compilation_cache else 'completed synthetic fixture directories only','removed':records,'free_bytes_before':before,'free_bytes_after':None}
    protected=[WORK/'graphics-config/output/.config',WORK/'rootfs-output/.config',WORK/'network-tools/baseline.config']
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    licenses={p/'COPYING.LIB':(p/'COPYING.LIB').read_bytes() for p in targets if p.name.startswith('glibc-') and (p/'COPYING.LIB').is_file()}
    report.write_text(json.dumps(result,indent=2)+'\n')
    for target in targets:shutil.rmtree(target)
    for path,data in licenses.items():path.parent.mkdir(exist_ok=True);path.write_bytes(data)
    assert all(hashlib.sha256(Path(n).read_bytes()).hexdigest()==h for n,h in hashes.items())
    result['protected_configuration_sha256']=hashes
    os.sync();result['free_bytes_after']=shutil.disk_usage(REPO).free
    result['reclaimed_bytes']=result['free_bytes_after']-before
    report.write_text(json.dumps(result,indent=2)+'\n')
    print('Reclaimed bytes:',result['reclaimed_bytes'],'audit:',report)

if __name__=='__main__':main()
