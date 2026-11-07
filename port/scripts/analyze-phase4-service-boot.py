#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Analyze the C01 PID1/selected-service native result and stock return."""
from pathlib import Path
import hashlib,json,re

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
stage=Path((work/'linux-diagnostic/latest-services').read_text().strip())
d=json.loads((stage/'log-collection.json').read_text())
assert d['experiment']=='MUOS-R35S-INIT-P4-C01'
assert d['base_media_marker']=='MUOS-R35S-EXT4-P4-B01'
r=d['files']['REPORT.TXT']['text'];log=d['files']['DMESG.TXT']['text']
assert d['files']['RESULT.TXT']['text'].strip()=='C01_DIAGNOSTIC_STATUS=0'
assert r.startswith('MUOS-R35S-INIT-P4-C01\n') and '4.4.189-muos-r35s-p4' in r
assert 'PID1\n/bin/busybox\n' in r
pid1=r.split('PID1\n',1)[1].split('ACTIVE STATUS\n',1)[0]
assert re.search(r'\binit\b',pid1),pid1
assert 'ACTIVE STATUS\n0\n' in r and 'FINAL STATUS\n0\n' in r and 'TAINT\n0\n' in r
active=r.split('ACTIVE INPUT\n',1)[1].split('ACTIVE MODULES\n',1)[0]
assert 'Name="muOS-Keys"' in active and 'Name="odroidgo3-keys"' in active
assert 'gpio_keys ' in r.split('ACTIVE MODULES\n',1)[1].split('ACTIVE PROCESSES\n',1)[0]
mapping=r.split('MAPPING\n',1)[1].splitlines()[0]
assert re.fullmatch(r'[0-9a-f]{32},muOS-Keys,.*platform:Linux,',mapping),mapping
active_processes=r.split('ACTIVE PROCESSES\n',1)[1].split('MAPPING\n',1)[0]
# The default ps view may omit the D-Bus daemon's different UID. Its live
# operation is checked by the RPC reply below, not by this filtered table.
for name in ['muinput','udevd']:assert name in active_processes,name
assert not re.search(r'\b(muxfrontend|muhotkey|pipewire|wireplumber)\b',active_processes)
final_processes=r.split('FINAL PROCESSES\n',1)[1].split('FINAL INPUT\n',1)[0]
assert not re.search(r'\b(muinput|dbus-daemon|udevd|udev-worker|muxfrontend|muhotkey|pipewire|wireplumber)\b',final_processes)
final_input=r.split('FINAL INPUT\n',1)[1].split('TAINT\n',1)[0]
assert 'Name="muOS-Keys"' not in final_input
assert 'org.freedesktop.DBus' in r.split('DBUS\n',1)[1].split('FINAL PROCESSES\n',1)[0]
mounts=r.split('FINAL MOUNTS\n',1)[1]
root=[line for line in mounts.splitlines() if len(line.split())>=4 and line.split()[1]=='/']
assert len(root)==1 and root[0].split()[2]=='ext4' and 'ro' in root[0].split()[3].split(',')
assert not any(line.split()[1]=='/mnt/mmc' or line.split()[1].startswith('/run/muos/storage/') for line in mounts.splitlines())
assert d['candidate_ext4_fsck']['exit_code']==0
assert d['taint']=='0' and d['services']['stdout']=='active\nactive\nactive'
assert d['stock_image']['stdout'].split()[0]=='31bdb671d640863448b59f79801277fe486fa6c78c326bd4ebb51a54559b0577'
stats=d['btrfs']['stdout'].splitlines()
assert len(stats)==5 and all(x.rsplit(None,1)[1]=='0' for x in stats)
assert d['mount_namespace_private'] and d['secondary_mounted_readonly'] and d['secondary_unmounted_after_collection']
pattern=r'\bOops:|\bBUG:|Kernel panic|Call trace:|Internal error|I/O error|Buffer I/O|mmc.*(?:error|timeout|timed out)|EXT4-fs error'
faults=[line for line in log.splitlines() if re.search(pattern,line,re.I)]
assert not faults,faults
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
result={'scope':'one native BusyBox PID1 boot and selected service start/readiness/stop without Wi-Fi dongle',
 'passed':True,'kernel_release':'4.4.189-muos-r35s-p4','busybox_pid1_verified':True,
 'diagnostic_inittab_sysinit_tested':True,'complete_product_rcs_tested':False,
 'board_coldplug_gpio_keys_passed':True,'dbus_rpc_passed':True,'muinput_normalized_device_created_and_removed':True,
 's90_s95_s96_status_passed':True,'mapping':mapping,'selected_services_stopped':True,
 'root_returned_readonly':True,'fat_logs_saved':True,'candidate_taint':0,
 'candidate_report_uptime_seconds':float(r.split('UPTIME\n',1)[1].split()[0]),
 'offline_ext4_fsck_passed':True,'stock_health_passed':True,'log_fault_pattern':pattern,'log_fault_matches':faults,
 'frontend_on_own_kernel_tested':False,'audio_playback_gles_tested':False,'control_events_tested':False,
 'wifi_coldplug_tested':False,'software_shutdown_tested':False,'other_panels_tested':False,
 'long_term_stability_tested':False,'collection_sha256':sha(stage/'log-collection.json'),
 'analyzer_source_sha256':sha(Path(__file__))}
(stage/'native-service-analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
