#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Qualify and package the finite Deck helper; no SSH or block-device actions."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import argparse,hashlib,importlib.util,json,shutil,subprocess,tarfile,tempfile

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'preferences'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--resume-from',type=Path);args=parser.parse_args()
survey=Path((area/'latest-layout').read_text().strip());assert survey.is_relative_to(area)
io_checks=Path((area/'latest-offline-io').read_text().strip());server_checks=Path((area/'latest-offline-server').read_text().strip())
assert io_checks.is_relative_to(area) and server_checks.is_relative_to(area)
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
io=json.loads((io_checks/'checks.json').read_text());check=json.loads((server_checks/'checks.json').read_text())
assert io['passed'] and check['passed']
for name,digest in io['sources'].items():assert sha(repo/'port/scripts'/name)==digest,name
source=repo/'port/scripts/phase4-userdata-offline-server.py'
assert sha(source)==check['server_source_sha256']
assert sha(repo/'port/scripts/check-phase4-userdata-offline-server.py')==check['check_source_sha256']
root_checks=Path((area/'latest-root-mode-checks').read_text().strip());assert root_checks.is_relative_to(area)
root_qualification=json.loads((root_checks/'checks.json').read_text());assert root_qualification['passed']
assert root_qualification['server_source_sha256']==sha(source)
assert root_qualification['io_source_sha256']==sha(repo/'port/scripts/phase4_userdata_io.py')
assert root_qualification['check_source_sha256']==sha(repo/'port/scripts/check-phase4-root-mode-repair.py')
spec=importlib.util.spec_from_file_location('helper',source);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
stage=Path(tempfile.mkdtemp(prefix='offline-package.',dir=area));stage.chmod(0o755)
payload=stage/'payload';payload.mkdir(mode=0o700)
for name in ['phase4-userdata-offline-server.py','phase4_userdata_io.py','phase4_userdata_layout.py',
             'inspect-phase4-userdata-offline.py','phase4-userdata-offline-client.py']:
    shutil.copyfile(repo/'port/scripts'/name,payload/name);(payload/name).chmod(0o600)
for name in ['userdata-plan.json','inventory.json','mbr.before','mbr.proposed']:
    shutil.copyfile(survey/name,payload/name);(payload/name).chmod(0o600)
native=stage/'native-preferences';native.mkdir()
for name in ['data-functions.sh','diagnostic.sh']:
    shutil.copyfile(repo/'port/device/rk-r35s-p0/preferences'/name,native/name)
# Exercise the formatter's exact feature set, UUID, label and inode policy on a
# regular disposable image. -F is solely for this regular-file fixture.
plan=json.loads((survey/'userdata-plan.json').read_text());wanted=plan['new_partition']
(stage/'data-marker').write_text('MUOS-R35S-DATA-V1\n');(stage/'prefs-marker').write_text('MUOS-R35S-PREFS-V1\n')
(stage/'debugfs.commands').write_text('write data-marker /.muos-r35s-data-v1\nset_inode_field /.muos-r35s-data-v1 mode 0100600\nmkdir /MUOS\nmkdir /MUOS/preferences\nset_inode_field /MUOS/preferences mode 040700\nwrite prefs-marker /MUOS/preferences/.muos-preferences-v1\nset_inode_field /MUOS/preferences/.muos-preferences-v1 mode 0100600\n')
relative='/work/'+str(stage.relative_to(work));container=(work/'rootfs-container.iid').read_text().strip()
code=f'''set -eu
cd {relative}
truncate -s 16777216 formatter-fixture.ext4
mke2fs -q -F -t ext4 -b 4096 -I 256 -i 65536 -m 0 -L {wanted['planned_label']} -U {wanted['planned_uuid']} \\
 -O none,{','.join(sorted(helper.FEATURES))} -E lazy_itable_init=0,lazy_journal_init=0 formatter-fixture.ext4
debugfs -w -f debugfs.commands formatter-fixture.ext4 > marker-write.log 2>&1
e2fsck -fn formatter-fixture.ext4 > formatter-fsck.txt 2>&1
dumpe2fs -h formatter-fixture.ext4 > formatter-superblock.txt 2>&1
blkid -p -o export formatter-fixture.ext4 > formatter-blkid.txt
debugfs -R 'cat /.muos-r35s-data-v1' formatter-fixture.ext4 > data-marker-readback 2> data-marker.stderr
debugfs -R 'cat /MUOS/preferences/.muos-preferences-v1' formatter-fixture.ext4 > prefs-marker-readback 2> prefs-marker.stderr
debugfs -R 'stat /MUOS/preferences' formatter-fixture.ext4 > preferences-inode.txt 2>&1
for name in data-functions.sh diagnostic.sh;do
 qemu-aarch64 -cpu cortex-a35 -L /work/linux-diagnostic/network-recovery.zz7sq2ve/extracted /work/linux-diagnostic/network-recovery.zz7sq2ve/extracted/bin/busybox sh -n native-preferences/$name
done
set +e
qemu-aarch64 -cpu cortex-a35 -L /work/linux-diagnostic/network-recovery.zz7sq2ve/extracted /work/linux-diagnostic/network-recovery.zz7sq2ve/extracted/bin/busybox sh native-preferences/diagnostic.sh initialize > native-entrypoint.stdout 2> native-entrypoint.stderr
rc=$?
set -e
test "$rc" = 64
'''
r=subprocess.run(['podman','run','--rm','--network=none','--read-only','--cap-drop=all',
 '--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev',
 '-v',f'{work}:/work:rw,z',container,'sh','-c',code],capture_output=True,text=True,timeout=45)
(stage/'formatter.stdout').write_text(r.stdout);(stage/'formatter.stderr').write_text(r.stderr)
assert r.returncode==0,(stage,r.stdout,r.stderr)
features=(stage/'formatter-superblock.txt').read_text().split('Filesystem features:')[1].splitlines()[0].split()
assert set(features)==helper.FEATURES
values=dict(line.split('=',1) for line in (stage/'formatter-blkid.txt').read_text().splitlines() if '=' in line)
assert values['TYPE']=='ext4' and values['UUID']==wanted['planned_uuid'] and values['LABEL']==wanted['planned_label']
assert (stage/'data-marker-readback').read_bytes()==(stage/'data-marker').read_bytes()
assert (stage/'prefs-marker-readback').read_bytes()==(stage/'prefs-marker').read_bytes()
assert 'Mode:  0700' in (stage/'preferences-inode.txt').read_text()
names=[n.name for n in payload.iterdir() if n.name!='phase4-userdata-offline-client.py']
manifest={'qualified_offline_adapter':True,'temporary_root_socket_only':True,
          'test128_only_original32_protected':True,'bounded_MBR_commit_and_explicit_recovery_cases':io['case_count'],
          'protocol_and_sysfs_refusal_cases':check['case_count'],'regular_formatter_image_fsck_and_markers_passed':True,
          'root_permission_correction_qualified_on_private_regular_copy':True,
          'root_permission_correction_real_card_executed':False,
          'real_data_guard_shell_syntax_and_wrong_entrypoint_checked':True,
          'real_data_guard_native_execution':False,
          'large_real_partition_or_native_Deck_operations_tested':False,
          'files':{n:sha(payload/n) for n in names}}
(payload/'package.json').write_text(json.dumps(manifest,indent=2)+'\n');(payload/'package.json').chmod(0o600)
with tarfile.open(stage/'deployment.tar','w') as archive:
    for path in sorted(payload.iterdir()):archive.add(path,arcname=path.name,recursive=False)
record={'passed':True,'host_tests_only_no_devices':True,'deployment_sha256':sha(stage/'deployment.tar'),
        'manifest':manifest,'io_checks':str(io_checks),'server_checks':str(server_checks),
        'root_mode_checks':str(root_checks),
        'native_diagnostic_sources':{name:sha(native/name) for name in ['data-functions.sh','diagnostic.sh']},
        'native_audit_sha256':sha(repo/'port/scripts/audit-phase4-preferences-data.py'),
        'prepare_source_sha256':sha(Path(__file__))}
if args.resume_from is not None:
    previous=args.resume_from.resolve();assert previous.is_relative_to(area)
    recovery=json.loads((previous/'independent-backup.json').read_text());private=Path(recovery['host_private_copy'])
    assert private.is_relative_to(work/'private') and not private.is_symlink()
    assert private.stat().st_size==671088640 and sha(private)==recovery['sha256']
    recovery['previous_deployment_sha256']=recovery['deployment_sha256']
    recovery['deployment_sha256']=record['deployment_sha256']
    recovery['resumed_from_package']=str(previous)
    (stage/'independent-backup.json').write_text(json.dumps(recovery,indent=2)+'\n')
    record['resumes_verified_backup_from']=str(previous)
(stage/'checks.json').write_text(json.dumps(record,indent=2)+'\n')
(area/'latest-offline-package').write_text(str(stage)+'\n')
print('C20 helper ready:',io['case_count'],'bounded-I/O +',check['case_count'],
      'guard cases and regular ext4 formatter/fsck/markers passed:',stage)
