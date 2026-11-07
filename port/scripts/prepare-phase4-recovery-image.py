#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C85 launch a finite regular-image operation in the existing container."""
from pathlib import Path
import argparse,json,os,stat,subprocess,tempfile
from phase4_backup_core import sha,write_new
from phase4_candidate import sums
from phase4_root_migration import require

REPO=Path(__file__).resolve().parents[2];WORK=REPO/'build/phase4';AREA=WORK/'recovery-image'
def latest(folder,pointer):
    p=Path((folder/pointer).read_text().strip());require(p.resolve().is_relative_to(folder),'Record location');return p
def mapped(path):
    p=Path(path);require(p.resolve().is_relative_to(WORK),'Expected work input');return '/work/'+str(p.relative_to(WORK))

def main(operation,request_path=None):
    os.umask(0o077);AREA.mkdir(exist_ok=True)
    checks=latest(AREA,'latest-checks');tested=json.loads((checks/'analysis.json').read_text())
    require(tested['passed'] is True,'Checks required')
    for n,h in tested['source_sha256'].items():require(sha(REPO/n)==h,'Tested source changed')
    parents={}
    for name in ['root-recovery','root-permissions','backup-native']:
        proof=REPO/'dist/phase4'/name
        for n,h in sums(proof/'SHA256SUMS').items():require(sha(proof/n)==h,'Parent proof changed')
        parents[name]=sha(proof/'SHA256SUMS')
    reference=latest(WORK/'root-recovery','latest-readiness');prior=json.loads((reference/'analysis.json').read_text())
    require(prior['passed'] is True and sha(reference/'binding.json')==prior['private_binding_sha256'],'C84 binding')
    binding=json.loads((reference/'binding.json').read_text());download=Path(binding['backup_download'])
    require(download.resolve().is_relative_to(WORK/'offline-backup'),'Backup location')
    receipt=json.loads((download/'backup.json').read_text());private=json.loads((download/'private-files.json').read_text())
    ack=Path(binding['backup_host_copy']);require(sha(ack)==binding['backup_host_copy_sha256'],'Host backup acknowledgment changed')
    ackdata=json.loads(ack.read_text());require(sha(download/'backup.json')==ackdata['helper_receipt_sha256'],'Backup receipt changed')
    require(private['files']==binding['backup_private_files'],'Backup private manifest changed')
    if operation=='reference':
        require(request_path is None,'Reference needs no request')
        request={'operation':operation,'backup_image':mapped(download/'root.ext4'),
            'backup_sha256':receipt['artifacts']['root.ext4']['sha256'],'backup_private_files':private['files'],
            'backup_counter':receipt['boot_sequence'],'backup_root_mode':receipt['source_root_modes']['p2']}
    else:
        require(request_path is not None,'A future controller-produced private request is required')
        request_path=Path(request_path);require(request_path.resolve().is_relative_to(AREA),'Private request location')
        s=request_path.lstat();require(stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600 and s.st_size<=1024*1024,'Private request metadata')
        request=json.loads(request_path.read_text());require(request['operation']==operation,'Operation binding')
        # Requests use host paths; the finite consumer validates schema and its
        # actual source descriptors, sealed handoff fence and capture context.
        for n in ['backup_image','observed_image','attempt_directory']:request[n]=mapped(request[n])
        require(request['backup_image']==mapped(download/'root.ext4') and request['backup_sha256']==receipt['artifacts']['root.ext4']['sha256']
            and request['backup_private_files']==private['files'] and request['backup_counter']==receipt['boot_sequence']
            and request['backup_prefix_sha256']==receipt['prefix_sha256'] and request['backup_root_mode']==receipt['source_root_modes']['p2'],'Known C82 backup required')
    stage=Path(tempfile.mkdtemp(prefix=operation+'.',dir=AREA))
    write_new(stage/'request.json',(json.dumps(request,indent=2)+'\n').encode())
    (AREA/'latest-attempt').write_text(str(stage)+'\n')
    container=(WORK/'rootfs-container.iid').read_text().strip()
    cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
        '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=64m',
        '-v',str(WORK)+':/work:rw,z','-v',str(REPO/'port')+':/port:ro,z',container,'python3',
        '/port/scripts/phase4-recovery-image.py','--request',mapped(stage/'request.json'),'--stage',mapped(stage)]
    p=subprocess.run(cmd,capture_output=True,timeout=600)
    for ext,data in [('stdout',p.stdout),('stderr',p.stderr),('exit',(str(p.returncode)+'\n').encode())]:write_new(stage/('consumer.'+ext),data)
    require(p.returncode==0,'Regular-image operation failed; inspect private stage, do not assume completion')
    result=json.loads((stage/'analysis.json').read_text());require(result['passed'] is True,'Consumer incomplete')
    report={'passed':True,'operation':operation,'component_checks':tested['case_count'],
        'checks_sha256':sha(checks/'analysis.json'),'consumer_analysis_sha256':sha(stage/'analysis.json'),
        'request_sha256':sha(stage/'request.json'),'C84_binding_sha256':sha(reference/'binding.json'),
        'parent_proofs_sha256':parents,'source_sha256':{**tested['source_sha256'],
            str(Path(__file__).relative_to(REPO)):sha(Path(__file__))},
        'physical_capture_backend_available':False,'device_writer_available':False,'reboot_requested':False}
    write_new(stage/'host-analysis.json',(json.dumps(report,indent=2)+'\n').encode())
    (AREA/('latest-'+operation)).write_text(str(stage)+'\n')
    print('C85 '+operation+' verified; regular-image operation only:',stage)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('operation',choices=['reference','collect','compose']);p.add_argument('--request',type=Path)
    a=p.parse_args();main(a.operation,a.request)
