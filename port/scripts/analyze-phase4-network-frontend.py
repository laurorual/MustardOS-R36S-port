#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Require live C08 results, concurrent SSH, restore checks, and visual evidence."""
from pathlib import Path
import hashlib,json,re,sys

stage=Path(sys.argv[1]).resolve();native=stage/'native'
manual=Path(sys.argv[2]).resolve()
def text(name):return (native/name).read_text(errors='replace')
manifest=json.loads((stage/'manifest.json').read_text())
assert len(manifest['chain_cases'])==8 and all(x['passed'] for x in manifest['chain_cases'].values())
assert len(manifest['udev_identity_cases'])==7 and all(x['passed'] for x in manifest['udev_identity_cases'].values())
assert text('result').strip()=='0'
namespaces=re.findall(r'^mnt:\[(\d+)\]$',text('report.txt'),re.M)
assert len(namespaces)==2 and namespaces[0]!=namespaces[1]
assert (native/'network-before.txt').read_bytes()==(native/'network-after.txt').read_bytes()
identities={line.split()[0]:line.split()[1:] for line in text('network-before.txt').splitlines()}
assert set(identities)=={'dropbear','wpa','dhcp','udev'}
assert all(len(x)==2 and int(x[0])>1 and int(x[1])>0 for x in identities.values())
assert (native/'alsa-before.txt').read_bytes()==(native/'alsa-restored.txt').read_bytes()
assert (native/'drm-before.txt').read_bytes()==(native/'drm-after.txt').read_bytes()
restored=text('persistent-restore.txt').splitlines()
assert len(restored)==13 and all(line.endswith(': OK') for line in restored)
assert 'C06_AUDIO_CLEANUP_OK=1' in text('audio-cleanup.txt')
assert 'C06_RESTORED_CACHE_PATH=SPK' in text('cache-restored.txt')
assert 'C06_RESTORED_CACHE_VOLUME=35' in text('cache-restored.txt')
assert 'C06_RESTORED_CACHE_BOOT_VOLUME=2' in text('cache-restored.txt')
assert not re.search(rb'^(FD_WRITER|MAP_WRITER)',(native/'root-writers.txt').read_bytes(),re.M)
front=text('frontend.log')
parent=re.search(r'UI_ID manager=(\d+) frontend=(\d+) parent=(\d+)',front)
assert parent and parent[1]==parent[3]
for marker in ['FIRST_PAINT','SDL_AUDIODRIVER=pipewire','UI_WINDOW_STARTED','UI_WINDOW_ENDED','C06_UI_STOPPED=1',
               'C06_NATIVE_CONFIRM_BACK=1','C06_NAV_WAVE_ADJUSTED=1','C06_AUDIO_GRACE_SECONDS=3']:
    assert marker in front,marker
snapshots=[]
for name in ['ui-during.txt','ui-before-stop.txt']:
    value=text(name)
    fmt=re.search(r'^format: (S16_LE|S32_LE)$',value,re.M)
    rate=re.search(r'^rate: (44100|48000) ',value,re.M)
    assert fmt and rate and re.search(r'^channels: 2$',value,re.M)
    assert re.search(r'^\s*: values=157,157$',value,re.M)
    assert re.search(r'^\s*: values=3$',value,re.M)
    assert re.search(r'^Volume: 1\.0+$',value,re.M)
    snapshots.append({'file':name,'format':fmt[1],'rate':int(rate[1])})
probes=json.loads((stage/'ssh-probes.json').read_text())
assert len(probes)>=3
assert all(x['exit']==0 and 'NETWORK_OK\n' in x['out'] and re.search(r'^ro(?:,|$)',x['out'],re.M) for x in probes)
active=[x for x in probes if 'UI_ACTIVE\n' in x['out']]
assert len(active)>=3 and active[-1]['elapsed']-active[0]['elapsed']>=60
health=text('final-health.txt')
for marker in ['TAINT=0','ROOT_RO=1','C07_NETWORK_OK','NO_C08_PROCESSES','NO_DBUS_SOCKET','KERNEL_ERROR_SIGNATURES=0']:
    assert marker in health,marker
assert all(line.endswith(': OK') for line in text('prerequisites-after.txt').splitlines())
assert not re.search(r'S05|S10|seedrng|muos-c07-',text('services.log'))
user=json.loads((manual/'native/user-confirmation.json').read_text())
assert user['screen_controls_audio_submenus_help_ok']
assert (manual/'package/prerequisites.sha256').read_bytes()==(stage/'package/prerequisites.sha256').read_bytes()
manual_modules=sorted(set(re.findall(r'^UI_MODULE=(\S+)',(manual/'native/frontend.log').read_text(errors='replace'),re.M)))
result={'passed':True,'scope':'C08 temporary frontend/audio on C07 native firmware with concurrent SSH',
 'same_boot_no_reboot':True,'manual_screen_controls_audio_submenus_confirmation_from':str(manual),
 'manual_and_automatic_attempts_share_identical_C06_C07_prerequisites':True,'manual_observed_modules':manual_modules,
 'corrected_automatic_observed_modules':sorted(set(re.findall(r'^UI_MODULE=(\S+)',front,re.M))),
 'fresh_first_paint_and_supervisor_parent_verified':True,'ssh_probe_count':len(probes),'ssh_probes_while_ui_active':len(active),
 'observed_concurrent_ui_seconds':round(active[-1]['elapsed']-active[0]['elapsed'],2),
 'c07_network_and_main_udev_pid_starttime_preserved':identities,'eight_chain_and_seven_udev_identity_cases_passed':True,
 'alsa_thirteen_original_hashes_cache_drm_restored':True,'no_root_fd_or_shared_map_writer_reported':True,
 'private_mount_namespace_and_root_ro_return_verified':True,'owned_dbus_socket_removed':True,
 'audio_snapshots':snapshots,'codec_path_gain_software_volume':'SPK_HP / 157 / unity',
 'navigation_adapted_and_help_uses_confirm_control':True,'original_help_final_loudness_headphones_not_approved':True,
 'persistent_boot_config_kernel_dtb_libraries_unchanged':True,'hotkeys_full_boot_ui_power_long_stability_tested':False,
 'seed_credentials_or_private_keys_collected':False,'postboot_offline_fsck_performed':False,
 'analyzer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(stage/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print('C08 combined frontend/SSH and restoration analysis passed:',stage)
