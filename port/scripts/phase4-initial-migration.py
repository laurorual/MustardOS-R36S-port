#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C92 finite regular-image CLI. No media, mount, fence, init or network IO."""
from pathlib import Path
import argparse,json,os,stat,sys
from phase4_backup_core import write_new
from phase4_root_migration import require,ROOT_BYTES
import phase4_initial_migration as migration
import phase4_recovery_image as image

def work_path(value):
    p=Path(value)
    require(p.is_absolute() and str(p).startswith('/work/') and '..' not in p.parts,'Private regular-image work path')
    return p

def main(request,stage):
    os.umask(0o077);request=work_path(request);stage=work_path(stage);image.private_stage(stage)
    fd=os.open(request,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        s=os.fstat(fd);require(stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1
            and stat.S_IMODE(s.st_mode)==0o600 and 0<s.st_size<=1024*1024,'Private request metadata')
        raw=os.read(fd,s.st_size+1)
        require(len(raw)==s.st_size and image.signature(os.fstat(fd))==image.signature(s),'Request changed')
        r=json.loads(raw)
    finally:os.close(fd)
    keys={'factory_image','factory_sha256','observed_image','observed_sha256','backup_private_files',
        'backup_counter','backup_prefix_sha256','attempt_directory','attempt_id','attempt_sha256','capture_context'}
    require(type(r) is dict and set(r)==keys,'Finite initial migration composition schema')
    attempt=migration.recovery.load_attempt(work_path(r['attempt_directory']),r['attempt_id'],r['attempt_sha256'])
    migration.compose(work_path(r['factory_image']),r['factory_sha256'],work_path(r['observed_image']),
        r['observed_sha256'],ROOT_BYTES,stage,r['backup_private_files'],r['backup_counter'],
        r['backup_prefix_sha256'],attempt,r['capture_context'])
    print('C92 INITIAL MIGRATION IMAGE COMPLETE',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',required=True);p.add_argument('--stage',required=True);a=p.parse_args()
    try:main(a.request,a.stage)
    except BaseException as error:
        try:
            stage=work_path(a.stage);image.private_stage(stage)
            write_new(stage/'failure.json',migration.recovery.encoded({'passed':False,'error_type':type(error).__name__,
                'reason':str(error),'no_automatic_retry_or_device_operation':True}))
        except BaseException:pass
        print('C92 FAILED ('+type(error).__name__+'); preserve private partial image, no automatic retry.',file=sys.stderr);sys.exit(1)
