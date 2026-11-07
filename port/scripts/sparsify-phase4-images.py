#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Reclaim allocated zero ranges in regular build images; verify every byte hash."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,stat,subprocess,shutil

REPO=Path(__file__).resolve().parents[2];BUILD=REPO/'build'
EXCLUDED={'private','root-migration','offline-backup','.git','cleanup'}
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args()
    os.umask(0o077);targets=[]
    for root,dirs,files in os.walk(BUILD,followlinks=False):
        dirs[:]=[n for n in dirs if n not in EXCLUDED and not (Path(root)/n).is_symlink()]
        for name in files:
            path=Path(root)/name;info=path.lstat()
            if path.suffix not in {'.img','.ext4','.fat','.cpio'} or not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:continue
            if info.st_size>=64*1024*1024 and info.st_blocks*512>=32*1024*1024:targets.append(path)
    print('Large regular build images:',len(targets),'apply:',a.apply,flush=True)
    if not a.apply:return
    area=BUILD/'cleanup';area.mkdir(exist_ok=True)
    report=area/('sparse-images-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json')
    result={'free_bytes_before':shutil.disk_usage(REPO).free,'files':[]}
    report.write_text(json.dumps(result,indent=2)+'\n')
    for i,path in enumerate(sorted(targets)):
        before=path.stat();digest=sha(path)
        r=subprocess.run(['fallocate','--dig-holes','--',str(path)],capture_output=True,timeout=180)
        assert r.returncode==0,(str(path),r.returncode)
        after=path.stat();assert after.st_size==before.st_size and after.st_ino==before.st_ino and after.st_mode==before.st_mode
        assert sha(path)==digest,'Image bytes changed: '+str(path)
        os.utime(path,ns=(before.st_atime_ns,before.st_mtime_ns))
        result['files'].append({'path':str(path.relative_to(REPO)),'sha256':digest,'bytes':before.st_size,
                              'allocated_before':before.st_blocks*512,'allocated_after':after.st_blocks*512})
        report.write_text(json.dumps(result,indent=2)+'\n')
        if i%10==0:print('Verified images',i+1,'/',len(targets),flush=True)
    os.sync();result['free_bytes_after']=shutil.disk_usage(REPO).free
    result['reclaimed_bytes']=result['free_bytes_after']-result['free_bytes_before']
    report.write_text(json.dumps(result,indent=2)+'\n')
    print('Reclaimed bytes:',result['reclaimed_bytes'],'audit:',report,flush=True)

if __name__=='__main__':main()
