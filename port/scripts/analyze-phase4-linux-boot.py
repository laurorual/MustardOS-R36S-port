#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Bind native diagnostic logs, host assets and returned stock health."""
from pathlib import Path
import hashlib
import json
import re

repo=Path(__file__).resolve().parents[2]
stage=Path((repo/'build/phase4/uboot-sd/latest-build').read_text().strip())
observed=json.loads((stage/'log-collection.json').read_text())
user=json.loads((stage/'native-first-linux.json').read_text())
report=observed['files']['REPORT.TXT']['text']
log=observed['files']['DMESG.TXT']['text']
stock=(stage/'stock-return-dmesg.txt').read_text()
final=json.loads((stage/'stock-return-final.json').read_text())
assert final['taint']=='0' and final['services']['out']=='active\nactive\nactive'
assert final['port_units']['exit']==0 and not final['port_units']['out']
assert final['image']['out'].split()[0]=='31bdb671d640863448b59f79801277fe486fa6c78c326bd4ebb51a54559b0577'
assert all(line.rsplit(None,1)[1]=='0' for line in final['btrfs']['out'].splitlines())
assert '/roms2 vfat rw,' in final['mounts']['out'] and '/opt/system/Tools vfat rw,' in final['mounts']['out']
assert observed['files']['RESULT.TXT']['text'].strip()=='INIT_REACHED_AND_LOGS_SAVED'
assert report.startswith('MUOS-R35S-LINUX-P4-A01\nLinux localhost 4.4.189-muos-r35s-p4 ')
assert 'Linux version 4.4.189-muos-r35s-p4 (muos@r35s-port)' in log
assert 'MODEL\nR36S-V12 2023-08-18 Panel 0\n' in report
assert 'TAINT\n0\n' in report
assert 'rootfs / rootfs rw,' in report and 'LOG_DEVICE\n/dev/mmcblk0p1\n' in report
assert 'MODULES\nLOG_DEVICE' in report
assert 'rdinit=/init' in report
assert observed['kernel']=='4.4.189' and observed['taint']=='0'
assert observed['stock_image']['stdout'].split()[0]=='31bdb671d640863448b59f79801277fe486fa6c78c326bd4ebb51a54559b0577'
assert observed['btrfs']['exit_code']==0
stats=observed['btrfs']['stdout'].splitlines()
assert len(stats)==5 and all(line.rsplit(None,1)[1]=='0' for line in stats)
assert observed['services']['stdout']=='active\nactive\nactive'
assert observed['mount_namespace_private'] and observed['secondary_mounted_readonly']
assert observed['secondary_unmounted_after_collection']
pattern=r'\bOops:|\bBUG:|Kernel panic|Call trace:|Internal error|I/O error|Buffer I/O|mmc.*(?:error|timeout|timed out)'
severe=lambda text:[line for line in text.splitlines() if re.search(pattern,line,re.I)]
assert not severe(log) and not severe(stock)
assert 'Console: switching to colour frame buffer device 80x30' in log
assert 'Update mode to 640x480p60' in log
assert 'Probed as mali0' in log
shared=[]
for marker in ['drm-logo@00000000','Setting trigger mode 8 for irq 170 failed',
               'failed on clk_get clk_cabac','Failed to add route Mic Jack -> direct -> MIC_IN',
               'Failed to add route HPOL -> direct -> Headphone Jack',
               'Failed to add route HPOR -> direct -> Headphone Jack','failed to parse loader memory']:
    assert marker in log and marker in stock
    shared.append(marker)
config=(repo/'build/phase4/kernel-output/.config').read_text()
assert 'CONFIG_KEYBOARD_GPIO=m\n' in config
assert 'N: Name="GO-Super Gamepad"' in report
assert 'odroidgo3-keys' not in report
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
result={'scope':'one native Linux/initramfs boot and manual stock-card return on R35S/Panel 0',
        'passed':True,'kernel_release':'4.4.189-muos-r35s-p4',
        'kernel_booted':True,'minimal_initramfs_booted':True,'pid1_reached':True,
        'console_framebuffer_640x480_80x30':True,'candidate_taint':0,
        'candidate_report_uptime_seconds':float(report.split('UPTIME\n')[1].split()[0]),
        'candidate_memtotal_kib':int(re.search(r'MemTotal:\s+(\d+) kB',report)[1]),
        'candidate_modules_loaded':False,'minimal_logs_saved_to_test_card':True,
        'native_log_fault_pattern':pattern,'native_log_severe_matches':severe(log),
        'stock_return_log_severe_matches':severe(stock),
        'selected_diagnostics_also_present_in_stock':shared,
        'shared_diagnostics_proven_harmless':False,
        'deferred_drm_probe_eventually_bound':True,'kernel_mali_probe_seen':True,
        'egl_gles_on_own_kernel_tested':False,'audio_playback_on_own_kernel_tested':False,
        'gpio_keys_module_not_in_minimal_initramfs':True,
        'input_events_on_own_kernel_tested':False,'product_rootfs_ext4_booted':False,
        'frontend_on_own_kernel_booted':False,'network_on_own_kernel_tested':False,
        'linux_software_shutdown_tested':False,'long_term_stability_tested':False,
        'other_panels_tested':False,'stock_return_health_passed':True,
        'stock_card_image_hash_unchanged':True,'collection_namespace_readonly':True,
        'stock_existing_mounts_preserved':True,
        'assets':{key:user[key] for key in ['image_sha256','kernel_sha256','uboot_sha256']},
        'evidence_sha256':{name:sha(stage/name) for name in ['log-collection.json','stock-return-dmesg.txt','native-first-linux.json','write-result.json','stock-return-final.json','return-confirmation.json']},
        'analyzer_source_sha256':sha(Path(__file__))}
(stage/'native-linux-analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
