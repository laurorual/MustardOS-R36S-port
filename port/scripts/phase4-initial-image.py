#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C88 finite container entrypoint. Only regular 512MiB image provisioning."""
from pathlib import Path
import argparse,json,os,stat,sys
from phase4_root_migration import require,ROOT_BYTES
from phase4_backup_core import write_new
import phase4_initial_image as core
import phase4_recovery_image as image

def work_path(value):
    p=Path(value);require(p.is_absolute() and str(p).startswith('/work/') and '..' not in p.parts,'Private work path')
    return p

def main(request,stage):
    os.umask(0o077);request=work_path(request);stage=work_path(stage);image.private_stage(stage)
    fd=os.open(request,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        before=os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and before.st_nlink==1
            and stat.S_IMODE(before.st_mode)==0o600 and 0<before.st_size<=1024*1024,'Private request metadata')
        raw=os.read(fd,before.st_size+1)
        require(len(raw)==before.st_size and image.signature(os.fstat(fd))==image.signature(before),'Request changed')
        r=json.loads(raw)
    finally:os.close(fd)
    require(type(r) is dict and set(r)=={'factory_image','factory_sha256','reference_image','reference_sha256','private_files','counter'},'Finite provision request')
    core.compose(work_path(r['factory_image']),r['factory_sha256'],work_path(r['reference_image']),
        r['reference_sha256'],ROOT_BYTES,stage,r['private_files'],r['counter'])
    print('C88 INITIAL IMAGE COMPLETE',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',required=True);p.add_argument('--stage',required=True);a=p.parse_args()
    try:main(a.request,a.stage)
    except BaseException as error:
        try:
            stage=work_path(a.stage);image.private_stage(stage)
            write_new(stage/'failure.json',(json.dumps({'passed':False,'error_type':type(error).__name__,'reason':str(error)},indent=2)+'\n').encode())
        except BaseException:pass
        print('C88 FAILED ('+type(error).__name__+'); keep private partial stage; no device action.',file=sys.stderr);sys.exit(1)
