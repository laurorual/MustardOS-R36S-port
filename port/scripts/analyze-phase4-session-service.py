#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Validate manual/idempotent/reopened/leased C11 generations and restoration."""
from pathlib import Path
import hashlib,json,re,sys
stage=Path(sys.argv[1]).resolve();meta=json.loads((stage/'manifest.json').read_text())
assert meta['host_passed'] and not meta['diagnostic_C06_C09_dependency'] and not meta['service_default_enabled']
assert len(meta['checks']['chain_cases'])==8 and len(meta['checks']['controller_cases'])==10
rows=[];identities=[];paints=[]
for number,reason in [(1,'manual-stop'),(2,'lease-expired'),(3,'lease-expired')]:
 d=stage/f'cycle{number}';n=d/'native'
 text=lambda name:(n/name).read_text(errors='replace')
 assert (d/'start.exit').read_text().strip()=='0' and (d/'status-after.exit').read_text().strip()=='3'
 assert text('result').strip()=='0'
 report=text('report.txt');assert 'MUOS-R35S-SESSION-P4-C11' in report and f'RESULT=0 REASON={reason}' in report
 namespaces=re.findall(r'^mnt:\[(\d+)\]$',report,re.M);assert len(namespaces)==2 and namespaces[0]!=namespaces[1]
 assert re.search(r'^/dev/mmcblk0p2 ext4 ro(?:,|$)',report,re.M)
 for filename in ['profile-effective.txt','original-restored.txt']:
  values=text(filename).splitlines();assert len(values)==21 and all(v.endswith(': OK') for v in values)
 assert all(v.endswith(': OK') for v in text('profile-source.txt').splitlines())
 for left,right in [('mixer-before.txt','mixer-after.txt'),('brightness-before.txt','brightness-after.txt'),('drm-before.txt','drm-after.txt'),('volume-before.sha256','volume-after.sha256')]:assert (n/left).read_bytes()==(n/right).read_bytes(),(number,left)
 assert text('brightness-active.txt').strip()=='80'
 assert re.search(r'^Volume: 1\.0+$',text('software-volume.txt'),re.M)
 mixer=text('mixer-active.txt');assert re.search(r"name='Playback Path'.*?: values=3",mixer,re.S) and ': values=157,157' in mixer
 assert not re.search(rb'^(?:FD_WRITER|MAP_WRITER)',(n/'root-writers.txt').read_bytes(),re.M)
 parent=re.search(r'UI_ID manager=(\d+) frontend=(\d+) parent=(\d+)',text('ui-identity.txt'));assert parent and parent[1]==parent[3]
 assert re.search(r'^rng_ready=1 wait_ms=0$',text('rng.txt'),re.M)
 health=(d/'health.txt').read_text()
 for marker in ['C07_NETWORK_OK','ROOT_RO=1','TAINT=0','NO_SESSION_PROCESSES','NO_DBUS_SOCKET','RNG_NOT_RELOADED','KERNEL_ERROR_SIGNATURES=0']:assert marker in health,marker
 assert (d/'infrastructure-after.txt').read_bytes()==(stage/'infrastructure-before.txt').read_bytes()
 assert all(v.endswith(': OK') for v in (d/'prerequisites-after.txt').read_text().splitlines())
 assert 'S30dbus-daemon' in text('stop.log') or 'Stopping dbus-daemon' in text('stop.log')
 identities.append(text('manager').strip());paints.append(float(text('first-paint.txt').split()[0]))
 user=json.loads((d/'user-confirmation.json').read_text());assert user['confirmed']==(number!=2)
 probes=json.loads((d/'ssh-probes.json').read_text());assert probes and all(p['exit']==0 and 'NETWORK_OK\n' in p['out'] and re.search(r'^ro(?:,|$)',p['out'],re.M) for p in probes)
 active=[p for p in probes if 'UI_ACTIVE\n' in p['out']]
 if number!=2:assert active
 rows.append({'generation':(d/'generation').read_text().strip(),'reason':reason,'worker_identity':identities[-1],'ui_parent':parent[1],'ssh_probes':len(probes),'ssh_probes_while_ready':len(active),'manual_visual_confirmation':user['confirmed'],'restoration_passed':True})
assert len(set(identities))==3 and paints[0]<paints[1]<paints[2]
first=stage/'cycle1';assert (first/'status-before.txt').read_bytes()==(first/'idempotent-start.txt').read_bytes()
assert (first/'stop.exit').read_text().strip()=='0' and (first/'repeated-stop.exit').read_text().strip()=='0'
report={'passed':True,'scope':'C11 standalone temporary session controller; manual stop, idempotence, restart and automatic lease cleanup','cycles':rows,'same_boot_no_reboot':True,'C06_C09_executors_not_used':True,'fresh_first_paints_and_distinct_worker_identities':True,'infrastructure_same_PID_starttime_all_cycles':True,'original_21_hashes_mixer_cache_brightness_DRM_volume_store_restored':True,'root_readonly_fat_unmounted_taint0_no_writers':True,'persistent_init_or_profile_installed':False,'full_firmware_built':False,'second_cycle_visual_unconfirmed_preserved':True,'third_cycle_visual_confirmed':True,'private_network_seed_keys_not_collected':True,'postboot_offline_fsck_performed':False,'warm_wifi_power_suspend_loudness_not_approved':True,'analyzer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');print('C11 three generations and restoration passed:',stage)
