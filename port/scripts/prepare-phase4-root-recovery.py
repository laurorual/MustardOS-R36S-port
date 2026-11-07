#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C84 bind offline recovery readiness to C82/C83; no seed/fence/media creation."""
from pathlib import Path
import json,os,stat,subprocess,tempfile
from phase4_backup_core import sha,write_new
from phase4_candidate import sums
import phase4_root_recovery as recovery

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'root-recovery'
def latest(folder,pointer):
    result=Path((folder/pointer).read_text().strip())
    recovery.require(result.resolve().is_relative_to(folder),'Private record location')
    return result

def main():
    os.umask(0o077);area.mkdir(exist_ok=True)
    check=latest(area,'latest-checks');checks=json.loads((check/'analysis.json').read_text())
    recovery.require(checks['passed'] is True and checks['case_count']==len(checks['cases']),'C84 checks required')
    for name,h in checks['source_sha256'].items():recovery.require(sha(repo/name)==h,'Tested source changed')
    parents={}
    for name in ['root-permissions','backup-native','root-migration','gambatte-card-image']:
        proof=repo/'dist/phase4'/name
        for n,h in sums(proof/'SHA256SUMS').items():recovery.require(sha(proof/n)==h,'Parent proof changed')
        parents[name]=sha(proof/'SHA256SUMS')
    copies=work/'offline-backup';ackfile=latest(copies,'latest-host-copy')/'analysis.json'
    ack=json.loads(ackfile.read_text());download=Path(ack['download'])
    recovery.require(download.resolve().is_relative_to(copies),'Backup location')
    s=download.lstat();recovery.require(stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700,'Backup directory')
    recovery.require(ack['passed'] is True and ack['independent_host_copy_verified'] is True,'Independent copy required')
    receipt=json.loads((download/'backup.json').read_text())
    recovery.require(sha(download/'backup.json')==ack['helper_receipt_sha256'] and receipt['prefix_sha256']==ack['prefix_sha256'],'Backup receipt binding')
    for n,row in receipt['artifacts'].items():
        recovery.require('/' not in n and n not in ('.','..'),'Backup filename')
        leaf=download/n;s=leaf.lstat()
        recovery.require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode) in (0o400,0o600),'Backup artifact metadata')
        recovery.require(s.st_size==row['bytes'] and sha(leaf)==row['sha256'],'Backup changed')
    private=json.loads((download/'private-files.json').read_text());counter=receipt['boot_sequence']
    recovery.manifest(private['files'],counter,True)
    for name,leaf in private['artifacts'].items():
        recovery.require(leaf in receipt['artifacts'],'Private artifact binding')
        recovery.require(sha(download/leaf)==private['files'][name]['sha256'],'Private payload hash')
    recovery.require((download/private['artifacts'][recovery.COUNTER]).read_bytes()==f'{counter}\n'.encode(),'Counter bytes')
    completion=latest(work/'root-permissions','latest-complete');repair=json.loads((completion/'analysis.json').read_text())
    hostcopy=json.loads((completion/'host-copy.json').read_text())
    for n,h in hostcopy['files'].items():recovery.require(sha(completion/n)==h,'Repair copy changed')
    context=json.loads((completion/'context.json').read_text())
    recovery.require(hostcopy['passed'] is True and repair['passed'] is True and repair['source_root_modes']=={'p2':0o755,'p3':0o755},'C83 modes')
    recovery.require(context['backup_receipt_sha256']==sha(download/'backup.json') and context['prefix_before_sha256']==receipt['prefix_sha256'],'C83/C82 source binding')
    # A regular C79 image is examined; code is never executed from the image.
    image=latest(work/'gambatte-card-image','latest-image')/'partition-readback/rootfs.ext4'
    factory=json.loads((repo/'dist/phase4/gambatte-card-image/analysis.json').read_text())
    recovery.require(sha(image)==factory['regions']['rootfs.ext4']['sha256'],'C79 extracted root changed')
    container=(work/'rootfs-container.iid').read_text().strip()
    cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
        '--userns=keep-id','-v',str(work)+':/work:ro,z',container,'debugfs','-R',
        'cat /usr/libexec/muos-entropy-functions','/work/'+str(image.relative_to(work))]
    proc=subprocess.run(cmd,capture_output=True,timeout=30)
    policy=repo/'port/device/rk-r35s-p0/entropy-diagnostic/functions.sh'
    recovery.require(proc.returncode==0 and recovery.hashed(proc.stdout)==sha(policy),'C79 entropy policy differs from exercised source')
    stage=Path(tempfile.mkdtemp(prefix='readiness.',dir=area))
    binding={'backup_host_copy':str(ackfile),'backup_host_copy_sha256':sha(ackfile),'backup_download':str(download),
        'backup_prefix_sha256':receipt['prefix_sha256'],'backup_private_files':private['files'],
        'repair_completion':str(completion),'repair_completion_sha256':sha(completion/'analysis.json'),
        'checks':str(check),'checks_sha256':sha(check/'analysis.json')}
    write_new(stage/'binding.json',(json.dumps(binding,indent=2)+'\n').encode())
    report={'passed':True,'experiment':'C84_OFFLINE_RECOVERY_CONTRACT_AND_READINESS','confirmed_backup_counter':counter,
        'backup_private_file_count':len(private['files']),'stable_identity_file_count':sum(n in recovery.STABLE for n in private['files']),
        'component_checks':checks['case_count'],'C82_backups_unchanged':True,'C83_repair_binding_verified':True,
        'C79_entropy_policy_matches_exercised_source':True,'postboot_recovery_contract_implemented':True,
        'postboot_source_collector_implemented':False,'production_regular_image_composer_implemented':False,
        'physical_recovery_backend_available':False,'recovery_image_created':False,'boot_handoff_fence_created':False,
        'live_seed_generated':False,'seed_loaded':False,'key_generated':False,'device_contacted_or_written':False,
        'candidate_provisioned':False,'reboot_requested':False,'parent_proofs_sha256':parents,
        'checks_sha256':sha(check/'analysis.json'),'private_binding_sha256':sha(stage/'binding.json'),
        'source_sha256':{**checks['source_sha256'],str(Path(__file__).relative_to(repo)):sha(Path(__file__))}}
    write_new(stage/'analysis.json',(json.dumps(report,indent=2)+'\n').encode())
    (area/'latest-readiness').write_text(str(stage)+'\n')
    print('C84 offline readiness verified; no seed, handoff fence, recovery image or media write:',stage)

if __name__=='__main__':main()
