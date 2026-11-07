#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C100 finite container entrypoint: pinned factory512MiB, regular output only."""
from pathlib import Path
import argparse,json,os,stat
import phase4_c79_layout as layout
from phase4_root_migration import require,ROOT_BYTES


def work_path(value):
    p=Path(value)
    require(p.is_absolute() and str(p).startswith('/work/') and '..' not in p.parts,'Private work path required')
    return p


def main(request,stage):
    os.umask(0o077);request=work_path(request);stage=work_path(stage);layout.image.private_stage(stage)
    fd=os.open(request,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        s=os.fstat(fd)
        require(stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and
            stat.S_IMODE(s.st_mode)==0o600 and 0<s.st_size<=4096,'Finite private request')
        raw=os.read(fd,s.st_size+1)
        require(len(raw)==s.st_size and layout.image.signature(os.fstat(fd))==layout.image.signature(s),'Request changed')
        value=json.loads(raw)
    finally:os.close(fd)
    require(set(value)=={'factory_image','factory_sha256'} and value['factory_sha256']==layout.C79_SHA,'Pinned C79 factory only')
    layout.compose(work_path(value['factory_image']),layout.C79_SHA,ROOT_BYTES,stage)
    print('C100 LAYOUT COMPLETE',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',required=True);p.add_argument('--stage',required=True)
    a=p.parse_args();main(a.request,a.stage)
