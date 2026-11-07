#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Require native C09 control transitions, user confirmation and full cleanup."""
from pathlib import Path
import hashlib,json,re,sys
stage=Path(sys.argv[1]).resolve();native=stage/'native'
def text(n):return (native/n).read_text(errors='replace')
m=json.loads((stage/'manifest.json').read_text());assert m['host_passed'] and m['control_cases']['passed']
assert len(m['chain_cases'])==8 and all(c['passed'] for c in m['chain_cases'].values())
assert len(m['udev_identity_cases'])==7 and all(c['passed'] for c in m['udev_identity_cases'].values())
assert text('result').strip()=='0'
is_profile=m['experiment']=='MUOS-R35S-RUNTIME-PROFILE-P4-C10'
assert m['experiment'] in text('report.txt')
ns=re.findall(r'^mnt:\[(\d+)\]$',text('report.txt'),re.M);assert len(ns)==2 and ns[0]!=ns[1]
assert (native/'network-before.txt').read_bytes()==(native/'network-after.txt').read_bytes()
identities={r.split()[0]:r.split()[1:] for r in text('network-before.txt').splitlines()};assert set(identities)=={'dropbear','wpa','dhcp','udev'}
assert (native/'alsa-before.txt').read_bytes()==(native/'alsa-restored.txt').read_bytes()
assert (native/'drm-before.txt').read_bytes()==(native/'drm-after.txt').read_bytes()
for filename,count in [('persistent-restore.txt',13),('controls-restored.txt',5)]:
 lines=text(filename).splitlines();assert len(lines)==count and all(r.endswith(': OK') for r in lines),filename
assert (native/'volume-store-before.sha256').read_bytes()==(native/'volume-store-after.sha256').read_bytes()
assert (native/'brightness-before.txt').read_bytes()==(native/'brightness-after.txt').read_bytes()
before=int(text('brightness-before.txt'));assert 40<=before<=160
helpers=text('helpers.txt')
for marker in ['HELPER_VOLUME_DOWN=95','HELPER_VOLUME_UP=100',f'HELPER_BRIGHT_DOWN={before-5}',f'HELPER_BRIGHT_UP={before}']:assert marker in helpers,marker
states=[tuple(map(int,match)) for match in re.findall(r'^CONTROL_STATE t=[0-9.]+ volume=([0-9]+) brightness=([0-9]+)$',text('controls-events.txt'),re.M)]
expected=[(100,before)] if is_profile else [(100,before),(95,before),(100,before),(100,before-5),(100,before)]
assert states==expected,{'actual':states,'expected':expected}
assert 'C06_AUDIO_CLEANUP_OK=1' in text('audio-cleanup.txt')
assert not re.search(rb'^(?:FD_WRITER|MAP_WRITER)',(native/'root-writers.txt').read_bytes(),re.M)
front=text('frontend.log');parent=re.search(r'UI_ID manager=(\d+) frontend=(\d+) parent=(\d+)',front);assert parent and parent[1]==parent[3]
for marker in ['FIRST_PAINT','SDL_AUDIODRIVER=pipewire','UI_WINDOW_STARTED','UI_WINDOW_ENDED','C06_UI_STOPPED=1','C06_NATIVE_CONFIRM_BACK=1','C06_NAV_WAVE_ADJUSTED=1','C06_AUDIO_GRACE_SECONDS=3']:assert marker in front,marker
live=(stage/'hotkey-during.txt').read_text();hotkey=re.search(r'HOTKEY_PID=(\d+) PARENT=(\d+) MANAGER=(\d+)',live);assert hotkey and hotkey[2]==hotkey[3]==parent[1]
for n in ['ui-during.txt','ui-before-stop.txt']:
 snap=text(n);assert re.search(r'^format: (S16_LE|S32_LE)$',snap,re.M) and re.search(r'^rate: (44100|48000) ',snap,re.M) and re.search(r'^channels: 2$',snap,re.M)
 assert re.search(r'^\s*: values=157,157$',snap,re.M) and re.search(r'^\s*: values=3$',snap,re.M)
 assert re.search(r'^Volume: 1\.0+$',snap,re.M)
probes=json.loads((stage/'ssh-probes.json').read_text());assert all(r['exit']==0 and 'NETWORK_OK\n' in r['out'] and re.search(r'^ro(?:,|$)',r['out'],re.M) for r in probes)
active=[r for r in probes if 'UI_ACTIVE\n' in r['out']];assert len(active)>=3 and active[-1]['elapsed']-active[0]['elapsed']>=min(60,m.get('ui_window_seconds',120)/2)
health=text('final-health.txt')
for marker in ['TAINT=0','ROOT_RO=1','C07_NETWORK_OK','NO_C09_PROCESSES','NO_DBUS_SOCKET','KERNEL_ERROR_SIGNATURES=0']:assert marker in health,marker
assert all(r.endswith(': OK') for r in text('prerequisites-after.txt').splitlines())
user=json.loads((native/'user-confirmation.json').read_text())
if is_profile:
 assert user['menu_audio_ok']
 assert m['profile_payload_from_actual_install_macro_and_posthook']
 active_profile=text('profile-effective.txt').splitlines()
 assert len(active_profile)==m['profile_file_count'] and all(r.endswith(': OK') for r in active_profile)
 static_profile=text('profile-static.txt').splitlines()
 assert len(static_profile)==m['profile_file_count']-2 and all(r.endswith(': OK') for r in static_profile)
 assert 'RUNTIME_VOLUME=100\nRUNTIME_BRIGHTNESS=80\n' in text('profile-runtime.txt')
 restored=text('profile-defaults-restored.txt').splitlines();assert len(restored)==2 and all(r.endswith(': OK') for r in restored)
 assert 'C10_GENERATED_PROFILE_ACTIVE=1' in front
else:
 assert user['four_isolated_taps_completed'] and user['audio_and_controls_reported_working_first_session']
record={'passed':True,'scope':'C09 temporary native hotkeys/helpers/UI/audio with concurrent SSH on Panel0; measured control values','user_confirmation':user,'control_states':states,'helper_steps_verified':True,'brightness_visual_double_step_perception_remains_recorded':user['brightness_looked_like_two_steps'],'brightness_percent_by_source':[before*100//160,(before-5)*100//160,before*100//160],'hotkey_supervisor_parent_verified':True,'ssh_probe_count':len(probes),'ssh_probes_while_ui_active':len(active),'ui_concurrent_seconds':round(active[-1]['elapsed']-active[0]['elapsed'],2),'network_and_udev_identity_preserved':identities,'original_alsa_brightness_volume_directory_18_hashes_cache_drm_restored':True,'root_ro_fat_unmounted_taint0_no_writers':True,'persistent_init_kernel_driver_libraries_changed':False,'root_postboot_offline_fsck_performed':False,'automatic_wifi_warm_reboot_approved':False,'power_suspend_headphones_long_stability_tested':False,'analyzer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
if is_profile:
 record.update(scope='C10 generated Buildroot profile, native menu/audio/SSH and restoration',generated_profile_files_verified=m['profile_file_count'],buildroot_ui_autostart_enabled=False)
(stage/'analysis.json').write_text(json.dumps(record,indent=2)+'\n');print('C10 generated profile and cleanup passed:' if is_profile else 'C09 controls/helper/native button trace and cleanup passed:',stage)
