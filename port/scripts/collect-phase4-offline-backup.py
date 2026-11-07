#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C81 verify/fsync a downloaded independent host copy. No remote or media IO."""
from pathlib import Path
import argparse, hashlib, json, os, re, stat, tempfile
from phase4_backup_core import sha, sync_dir, write_new, verify_userdata_archive, region_sha, validate_source_root_policy
from phase4_root_migration import geometry, private_manifest, require, PREFIX_BYTES, ROOT_BYTES

REPO=Path(__file__).resolve().parents[2];AREA=REPO/'build/phase4/offline-backup'

def verify_download(source,plan_path,source_policy=None):
    require(not source.is_symlink() and source.resolve().is_relative_to(AREA),'Expected private host download directory')
    source=source.resolve();plan=json.loads(plan_path.read_text())
    require(source.is_dir() and source.stat().st_uid==os.getuid() and stat.S_IMODE(source.stat().st_mode)==0o700,'Private host directory')
    receipt=json.loads((source/'backup.json').read_text())
    require(receipt['passed'] is True and receipt['experiment']=='C81_OFFLINE_BACKUP_ONLY','Backup receipt')
    require(receipt['plan_sha256']==sha(plan_path) and receipt['boot_sequence']==plan['survey_boot_sequence'],'Backup binding')
    modes=receipt.get('source_root_modes',{'p2':0o755,'p3':0o755})
    if source_policy is not None:
        validate_source_root_policy(source_policy)
        expected=hashlib.sha256((json.dumps(source_policy,sort_keys=True)+'\n').encode()).hexdigest()
        require(receipt['source_root_policy_sha256']==expected and modes=={'p2':0o777,'p3':0o777} and receipt['metadata_repair_required_before_boot'] is True,'Explicit source-root policy binding')
    else:
        require(receipt.get('source_root_policy_sha256') is None and modes=={'p2':0o755,'p3':0o755} and receipt.get('metadata_repair_required_before_boot',False) is False,'Source drift requires explicit policy')
    for key in ['all_namespaces_checked','alias_cache_synchronized','private_state_from_fresh_backup','userdata_archive_verified','p3_unmounted']:
        require(receipt[key] is True,'Backup verification incomplete')
    for key in ['independent_host_copy_verified','device_payload_writer_available','device_format_or_restore_available','candidate_provisioned','seed_loaded','reboot_requested']:
        require(receipt[key] is False,'Unexpected helper capability/state')
    require(all(type(receipt[k]) is int and receipt[k]==0 for k in ['fat_fsck_exit','root_fsck_exit','data_fsck_exit']),'Offline fsck')
    expected={'prefix.backup','boot.fat','root.ext4','private-files.json','userdata.tar','userdata-manifest.json'}
    artifacts=receipt['artifacts']
    require(expected<=set(artifacts) and all(n in expected or re.fullmatch(r'private-[0-9]{2}\.dat',n) for n in artifacts),'Artifact paths')
    require({p.name for p in source.iterdir()}==set(artifacts)|{'backup.json'},'Download missing/extra files')
    for name in sorted(set(artifacts)|{'backup.json'}):
        path=source/name;s=path.lstat()
        require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode) in (0o400,0o600),'Unsafe host artifact')
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
        try:os.fsync(fd)
        finally:os.close(fd)
        if name in artifacts:
            row=artifacts[name];require(type(row['bytes']) is int and s.st_size==row['bytes'] and sha(path)==row['sha256'],'Host copy hash/size')
    require(artifacts['prefix.backup']['bytes']==PREFIX_BYTES and artifacts['root.ext4']['bytes']==ROOT_BYTES and artifacts['boot.fat']['bytes']==100*1024*1024,'Backup dimensions')
    if source_policy is not None:require(artifacts['root.ext4']['sha256']==source_policy['diagnostic_root_sha256'],'Source diagnostic root changed')
    require(receipt['prefix_sha256']==artifacts['prefix.backup']['sha256'],'Prefix receipt')
    fd=os.open(source/'prefix.backup',os.O_RDONLY|os.O_NOFOLLOW)
    try:
        require(region_sha(fd,16*1024*1024,100*1024*1024)==artifacts['boot.fat']['sha256'],'Host FAT extraction differs')
        require(region_sha(fd,128*1024*1024,ROOT_BYTES)==artifacts['root.ext4']['sha256'],'Host root extraction differs')
    finally:os.close(fd)
    with (source/'prefix.backup').open('rb') as f:
        prefix=f.read(16*1024*1024);mbr=prefix[:512];geometry(mbr)
    require(hashlib.sha256(mbr).hexdigest()==plan['mbr_sha256'] and hashlib.sha256(prefix).hexdigest()==plan['boot_prefix_16MiB_sha256'],'Host media identity')
    private=json.loads((source/'private-files.json').read_text());private_manifest(private['files'])
    require(private.get('source_root_mode',0o755)==modes['p2'],'Private extraction root mode')
    require(set(private['artifacts'])==set(private['files']),'Private artifact mapping')
    require(len(set(private['artifacts'].values()))==len(private['artifacts']),'Aliased private artifact')
    for name,leaf in private['artifacts'].items():
        require(leaf in artifacts and re.fullmatch(r'private-[0-9]{2}\.dat',leaf),'Private leaf mapping')
        require(sha(source/leaf)==private['files'][name]['sha256'] and (source/leaf).stat().st_size==private['files'][name]['bytes'],'Private copy differs')
    require(set(artifacts)-expected==set(private['artifacts'].values()),'Unreferenced private payload')
    userdata=json.loads((source/'userdata-manifest.json').read_text())
    require(userdata.get('source_root_mode',0o755)==modes['p3'],'Userdata extraction root mode')
    require(userdata['sha256']==artifacts['userdata.tar']['sha256'],'Userdata manifest hash')
    verify_userdata_archive(source/'userdata.tar',userdata['records'])
    require(userdata['archive_verified'] is True and userdata['file_count']==sum(v['type']=='file' for v in userdata['records'].values()),'Userdata receipt')
    stable=lambda r:{n:v for n,v in r.items() if not n.startswith('var/lib/muos-seedrng/') and n!='var/lib/muos-diagnostic/boot-seq'}
    require(stable(private['files'])==stable(plan['private_files_at_live_survey']),'Host network/key binding')
    counter='var/lib/muos-diagnostic/boot-seq'
    require((source/private['artifacts'][counter]).read_bytes()==f"{plan['survey_boot_sequence']}\n".encode(),'Host counter binding')
    sync_dir(source)
    return {'passed':True,'experiment':'C81_INDEPENDENT_HOST_COPY','plan_sha256':sha(plan_path),
        'helper_receipt_sha256':sha(source/'backup.json'),'prefix_sha256':receipt['prefix_sha256'],
        'artifact_count':len(artifacts),'independent_host_copy_verified':True,'host_files_and_directory_fsynced':True,
        'source_root_modes':modes,'metadata_repair_required_before_boot':source_policy is not None,
        'candidate_provisioned':False,'device_writer_available':False,'execution_enabled':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('download',type=Path);p.add_argument('--plan',type=Path,required=True);p.add_argument('--source-policy',type=Path);a=p.parse_args()
    os.umask(0o077);AREA.mkdir(exist_ok=True)
    require(a.plan.resolve().is_relative_to(REPO/'build/phase4/root-migration'),'Expected private migration plan')
    source_policy=None
    if a.source_policy:
        require(a.source_policy.resolve().is_relative_to(AREA),'Private source policy')
        source_policy=json.loads(a.source_policy.read_text())
    r=verify_download(a.download,a.plan,source_policy)
    stage=Path(tempfile.mkdtemp(prefix='host-copy.',dir=AREA));write_new(stage/'analysis.json',(json.dumps(r,indent=2)+'\n').encode())
    (AREA/'latest-host-copy').write_text(str(stage)+'\n')
    print('C81 independent host copy verified/fsynced; no writer enabled:',stage)
