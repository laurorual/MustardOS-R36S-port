#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C85 finite in-container entrypoint. Regular 512MiB inputs only, never media."""
from pathlib import Path
import argparse,json,os,stat,sys
from phase4_backup_core import write_new
from phase4_root_migration import require
import phase4_root_recovery as recovery
import phase4_recovery_image as core

def input_path(value):
    path=Path(value)
    require(path.is_absolute() and str(path).startswith('/work/') and '..' not in path.parts,'Input must be under private work tree')
    return path

def main(request,stage):
    os.umask(0o077);request=input_path(str(request));stage=input_path(str(stage));core.private_stage(stage)
    fd=os.open(request,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        s=os.fstat(fd);require(stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1
            and stat.S_IMODE(s.st_mode)==0o600 and 0<s.st_size<=1024*1024,'Private request file')
        data=os.read(fd,s.st_size+1);require(len(data)==s.st_size,'Request length');r=json.loads(data)
    finally:os.close(fd)
    common={'operation','backup_image','backup_sha256','backup_private_files','backup_counter','backup_root_mode'}
    extra={'backup_prefix_sha256','observed_image','observed_sha256','attempt_directory','attempt_id','attempt_sha256','capture_context'}
    require(type(r) is dict and r.get('operation') in ('reference','collect','compose'),'Finite operation required')
    require(set(r)==(common if r['operation']=='reference' else common|extra),'Request schema')
    image=input_path(r['backup_image']);size=512*1024*1024
    if r['operation']=='reference':
        with core.source_image(image,r['backup_sha256'],size) as source:base=core.scan(source,stage,r['backup_root_mode'])
        require(base['private_files']==r['backup_private_files'] and base['boot_sequence']==r['backup_counter'],'Reference manifest/counter binding')
        write_new(stage/'tree.json',(json.dumps(base['tree'],indent=2)+'\n').encode())
        result={'passed':True,'experiment':'C85_REFERENCE_BACKUP_REGULAR_IMAGE_SCAN','root_fsck_exit':0,
            'root_image_bytes':size,'private_file_count':len(base['private_files']),'tree_entry_count':len(base['tree']),
            'source_image_unchanged':True,'recovery_image_created':False,'postboot_observation_created':False,
            'seed_generated_or_loaded':False,'device_contacted_or_written':False,'reboot_requested':False}
        write_new(stage/'analysis.json',(json.dumps(result,indent=2)+'\n').encode())
    else:
        attempt=recovery.load_attempt(input_path(r['attempt_directory']),r['attempt_id'],r['attempt_sha256'])
        recovery.checked_attempt(attempt,r['backup_private_files'],r['backup_counter'],r['backup_prefix_sha256'])
        observed=input_path(r['observed_image'])
        if r['operation']=='collect':
            captured,observation=core.collect_postboot(observed,r['observed_sha256'],size,stage,attempt,r['capture_context'])
            # Derive and validate the policy before publishing any completion.
            plan=recovery.recovery_plan(r['backup_private_files'],r['backup_counter'],r['backup_prefix_sha256'],attempt,observation)
            write_new(stage/'observation.json',(json.dumps(observation,indent=2)+'\n').encode())
            write_new(stage/'tree.json',(json.dumps(captured['tree'],indent=2)+'\n').encode())
            write_new(stage/'plan.json',(json.dumps(plan,indent=2)+'\n').encode())
            write_new(stage/'analysis.json',(json.dumps({'passed':True,'experiment':'C85_REGULAR_POSTBOOT_COLLECTOR',
                'source_image_unchanged':True,'device_writer_available':False,'physical_capture_backend_available':False,
                'recovery_image_created':False,'seed_generated_or_loaded':False},indent=2)+'\n').encode())
        else:
            core.compose(image,r['backup_sha256'],observed,r['observed_sha256'],size,stage,
                r['backup_private_files'],r['backup_counter'],r['backup_prefix_sha256'],attempt,r['capture_context'],r['backup_root_mode'])
    print('C85 '+r['operation'].upper()+' COMPLETE',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',type=Path,required=True);p.add_argument('--stage',type=Path,required=True);a=p.parse_args()
    try:main(a.request,a.stage)
    except BaseException as error:
        try:
            input_path(str(a.stage));core.private_stage(a.stage)
            write_new(a.stage/'failure.json',(json.dumps({'passed':False,'error_type':type(error).__name__,
                'reason':str(error),'completion_must_not_be_assumed':True},indent=2)+'\n').encode())
        except BaseException:pass
        print('C85 FAILED ('+type(error).__name__+'); keep private partial stage. No automatic retry or device operation.',file=sys.stderr);sys.exit(1)
