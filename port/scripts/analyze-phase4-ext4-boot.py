#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Verify the narrow native ext4/storage/gpio_keys result and stock return."""
from pathlib import Path
import hashlib,json,re

repo=Path(__file__).resolve().parents[2]
stage=Path((repo/'build/phase4/uboot-sd/latest-build').read_text().strip())
d=json.loads((stage/'log-collection.json').read_text())
assert d['experiment']=='MUOS-R35S-EXT4-P4-B01'
r=d['files']['REPORT.TXT']['text'];log=d['files']['DMESG.TXT']['text']
assert d['files']['RESULT.TXT']['text'].strip()=='EXT4_DIAGNOSTIC_STATUS=0'
assert r.startswith('MUOS-R35S-EXT4-P4-B01\nLinux localhost 4.4.189-muos-r35s-p4 ')
assert 'STATUS\n0\n' in r and 'TAINT\n0\n' in r
assert 'GPIO_KEYS_OK' in r and 'STORAGE_OK' in r
assert 'Name="odroidgo3-keys"' in r
assert 'gpio_keys ' in r.split('MODULES\n',1)[1].split('UI CONFIG\n',1)[0]
mounts=r.split('FINAL MOUNTS\n',1)[1].split('TAINT\n',1)[0]
root_lines=[line for line in mounts.splitlines() if len(line.split())>=4 and line.split()[1]=='/']
assert len(root_lines)==1 and root_lines[0].split()[2]=='ext4'
assert 'ro' in root_lines[0].split()[3].split(',')
assert not any('/mnt/mmc'==line.split()[1] or line.split()[1].startswith('/run/muos/storage/') for line in mounts.splitlines())
assert 'enabled=0\nhotkeys=0\n' in r
processes=r.split('PROCESSES\n',1)[1]
assert not re.search(r'\b(muxfrontend|muhotkey|muinput|pipewire|wireplumber)\b',processes)
assert 'root=PARTUUID=4d554432-02' in log
assert 'init=/sbin/muos-ext4-diag' in log
assert d['candidate_ext4_fsck']['exit_code']==0
assert d['taint']=='0' and d['services']['stdout']=='active\nactive\nactive'
assert d['stock_image']['stdout'].split()[0]=='31bdb671d640863448b59f79801277fe486fa6c78c326bd4ebb51a54559b0577'
assert d['btrfs']['exit_code']==0
stats=d['btrfs']['stdout'].splitlines()
assert len(stats)==5 and all(x.rsplit(None,1)[1]=='0' for x in stats)
assert d['mount_namespace_private'] and d['secondary_mounted_readonly'] and d['secondary_unmounted_after_collection']
pattern=r'\bOops:|\bBUG:|Kernel panic|Call trace:|Internal error|I/O error|Buffer I/O|mmc.*(?:error|timeout|timed out)|EXT4-fs error'
faults=[line for line in log.splitlines() if re.search(pattern,line,re.I)]
assert not faults,faults
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
result={'scope':'one native ext4 boot, explicit gpio_keys and S90 storage transaction; no complete rcS/UI',
 'passed':True,'kernel_release':'4.4.189-muos-r35s-p4','pid1_from_ext4':True,
 'initial_root_readonly_checked_in_init':True,'root_partuuid':'4d554432-02',
 'gpio_keys_loaded':True,'volume_input_device_enumerated':True,'storage_start_status_stop_passed':True,
 'storage_binds_removed':True,'final_root_readonly':True,'logs_saved':True,
 'candidate_taint':0,'log_fault_pattern':pattern,'log_fault_matches':faults,
 'offline_candidate_ext4_fsck_passed':True,'stock_health_passed':True,
 'product_rcs_tested':False,'full_coldplug_tested':False,'frontend_on_own_kernel_tested':False,
 'input_events_tested':False,'audio_gles_network_tested':False,'software_shutdown_tested':False,
 'other_panels_tested':False,'long_term_stability_tested':False,
 'collection_sha256':sha(stage/'log-collection.json'),'source_sha256':sha(Path(__file__))}
(stage/'native-ext4-analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
