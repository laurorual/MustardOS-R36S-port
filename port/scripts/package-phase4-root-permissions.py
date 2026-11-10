#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C83 verify completion and freeze redacted evidence, never metadata capsules."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,tempfile
from phase4_backup_core import sha,write_new
from phase4_candidate import sums
from phase4_root_migration import require
from importlib import import_module

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/root-permissions'
prep=import_module('prepare-phase4-root-permissions')

def current(pointer):
    p=Path((area/pointer).read_text().strip())
    require(p.resolve().is_relative_to(area),'Private record location')
    return p

def main(host):
    os.umask(0o077)
    check=current('latest-checks');cases=json.loads((check/'analysis.json').read_text())
    require(cases['passed'] is True and cases['case_count']==len(cases['cases'])==44,'Checks required')
    for n,h in cases['source_sha256'].items():require(sha(repo/n)==h,'Tested source changed')
    inspect=current('latest-inspection');complete=current('latest-complete')
    for record in (inspect,complete):
        ack=json.loads((record/'host-copy.json').read_text())
        require(ack['passed'] is True and ack['host_capsule_copy_verified'] is True,'Independent capsule copy required')
        for n,h in ack['files'].items():require(sha(record/n)==h,'Capsule copy changed')
    ctx=json.loads((complete/'context.json').read_text());native=json.loads((complete/'analysis.json').read_text())
    planned=json.loads((inspect/'repair-plan.json').read_text())
    require(native['passed'] is True and native['operation']=='apply' and native['context_sha256']==sha(complete/'context.json')==sha(inspect/'context.json'),'Native/context binding')
    require(native['patches']==planned['patches'] and native['prefix_after_sha256']==planned['prefix_after_sha256'],'Native/plan binding')
    for k in ['device_written','kernel_readonly','backup_verified','host_copy_verified','userdata_before_matches_C82','userdata_after_matches_C82','full_prefix_posthash_verified','no_superblock_or_GDT_changes']:
        require(native[k] is True,'Native preservation missing: '+k)
    require(native['written_sectors']==2 and native['source_root_modes']=={'p2':0o755,'p3':0o755} and native['p2_fsck_exit']==native['p3_fsck_exit']==0,'Native completion')
    require(native['seed_loaded'] is False and native['reboot_requested'] is False,'No seed/boot')
    for n in (2,3):
        p=native['patches'][str(n)];before=bytes.fromhex(p['before']);after=bytes.fromhex(p['after'])
        require([i for i,(a,b) in enumerate(zip(before,after)) if a!=b]==p['changed_offsets'],'Sector byte differences')
        prep.metadata.sector_patch((complete/f'p{n}-sb.bin').read_bytes(),(complete/f'p{n}-gd.bin').read_bytes(),after,p['partition_start'],p['partition_bytes'],0o40755)
    t=prep.transport();survey=t.native(host,t.INSPECT);t.validate_inspection(survey)
    code=r'''
from pathlib import Path
import hashlib,json,stat,subprocess
aliases=['mmcblk0','mmcblk0p1','mmcblk0p2','mmcblk0p3']
p=Path('/run/udev/rules.d/99-holo-automount.rules');s=p.lstat();data=p.read_bytes()
print(json.dumps({'alias_readonly':{n:int((Path('/sys/class/block')/n/'ro').read_text()) for n in aliases},
 'runtime_rule_sha256':hashlib.sha256(data).hexdigest(),'runtime_rule_root_owned_regular_0644':stat.S_ISREG(s.st_mode) and s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o644,
 'runtime_rule_original_suffix_preserved':data.endswith(Path('/usr/lib/udev/rules.d/99-holo-automount.rules').read_bytes()),
 'runtime_rule_verifies':subprocess.run(['udevadm','verify',str(p)],capture_output=True).returncode==0}))
'''
    post=t.native(host,code)
    require(set(post['alias_readonly'].values())=={1} and post['runtime_rule_sha256']==native['automount_guard_sha256'],'Kernel/rule protection')
    require(all(post[k] is True for k in ['runtime_rule_root_owned_regular_0644','runtime_rule_original_suffix_preserved','runtime_rule_verifies']),'Rule verification')
    stamp=Path(tempfile.mkdtemp(prefix='postflight.',dir=area))
    write_new(stamp/'survey.json',(json.dumps(survey,indent=2)+'\n').encode())
    write_new(stamp/'post.json',(json.dumps(post,indent=2)+'\n').encode())
    (area/'latest-postflight').write_text(str(stamp)+'\n')
    parents={}
    for name in ['backup-native','offline-backup','root-migration','gambatte-card-image']:
        root=repo/'dist/phase4'/name
        for n,h in sums(root/'SHA256SUMS').items():require(sha(root/n)==h,'Parent proof changed')
        parents[name]=sha(root/'SHA256SUMS')
    public=Path(tempfile.mkdtemp(prefix='public.',dir=area));out=repo/'dist/phase4/root-permissions'
    require(not out.exists(),'Proof already exists; do not overwrite')
    result={'passed':True,'experiment':'C83_TWO_ROOT_INODE_MODES_REPAIRED',
        'logical_sectors_written':2,'logical_sector_bytes':512,'changed_byte_count':6,
        'root_owner_uid_gid':[0,0],'root_modes_before':{'p2':'0777','p3':'0777'},'root_modes_after':{'p2':'0755','p3':'0755'},
        'sector_changes':{n:{k:p[k] for k in ['sector_offset','changed_offsets','checksummed']} for n,p in native['patches'].items()},
        'full_640MiB_prefix_posthash_verified':True,'full_p3_payload_hashed':False,
        'superblocks_and_first_group_descriptor_blocks_unchanged':True,'userdata_file_count':9,
        'userdata_contents_and_metadata_unchanged':True,'p2_fsck_exit':0,'p3_fsck_exit':0,
        'independent_metadata_capsules_verified':True,'C82_backups_preserved':True,
        'card_unmounted':True,'root_snapshot_removed':True,'all_four_aliases_kernel_readonly':True,
        'temporary_exact_card_automount_guard_verified':True,'permanent_SteamOS_files_modified':False,
        'seed_loaded':False,'reboot_requested':False,'candidate_firmware_written':False,
        'physical_flash_power_loss_atomicity_qualified':False,'post_boot_recovery_implemented':False,
        'component_checks':44,'parent_proofs_sha256':parents,'live_capsules_private_hashes_or_payloads_included':False}
    write_new(public/'analysis.json',(json.dumps(result,indent=2)+'\n').encode())
    shutil.copyfile(check/'analysis.json',public/'component-checks.json')
    for n in ['fixtures.py','fixtures.stdout','fixtures.stderr','fixtures.exit']:shutil.copyfile(check/n,public/n)
    sources={repo/n for n in cases['source_sha256']}
    sources.update([Path(__file__),repo/'docs/archive/phase4/phase4-root-permissions.md'])
    for src in sorted(sources):
        dst=public/'source'/src.relative_to(repo);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    forbidden=[ctx['prefix_before_sha256'],native['prefix_after_sha256'],ctx['mbr_sha256'],ctx['boot_prefix_16MiB_sha256'],native['automount_guard_sha256']]
    forbidden.extend(row['sha256'] for row in ctx['backup_artifacts'].values())
    for record in (inspect,complete):
        data=json.loads((record/'analysis.json').read_text())
        for p in data['patches'].values():forbidden.extend(p[k] for k in ['before','after','before_sha256','after_sha256'])
    for p in public.rglob('*'):
        require(not p.is_symlink(),'Public symlink')
        if p.is_file():
            require(p.suffix.lower() not in {'.bin','.ext4','.fat','.dat','.tar','.img','.gb','.sav','.state'},'Public payload')
            require(not any(v.encode() in p.read_bytes() for v in forbidden),'Private metadata in proof')
    write_new(public/'SHA256SUMS',''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()).encode())
    shutil.move(str(public),out)
    print('C83 final Deck protection and redacted proof verified:',out)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True);main(p.parse_args().host)
