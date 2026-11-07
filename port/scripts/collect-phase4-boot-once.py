#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Collect public C12/C11 records, compare RO FAT reports and installed hashes."""
from pathlib import Path
import argparse,hashlib,io,ipaddress,json,re,subprocess,tarfile
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/boot-order'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--stage',type=Path);parser.add_argument('--host',type=ipaddress.IPv4Address);args=parser.parse_args()
stage=(args.stage or Path((area/'latest-boot-test').read_text().strip())).resolve();assert stage.is_relative_to(area)
meta=json.loads((stage/'manifest.json').read_text())
ip=str(args.host or ipaddress.IPv4Address((stage/'native-address').read_text().strip()))
ssh=['ssh','-p','2222','-i',str(repo/'build/phase4/private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(repo/'build/phase4/private/c07-known_hosts'),'-oBatchMode=yes','-oConnectTimeout=8','root@'+ip]
def remote(label,code,timeout=30):
 r=subprocess.run(ssh+['sh -s'],input=code,capture_output=True,text=True,timeout=timeout)
 (stage/(label+'.stdout')).write_text(r.stdout);(stage/(label+'.stderr')).write_text(r.stderr);(stage/(label+'.exit')).write_text(str(r.returncode)+'\n')
 assert r.returncode==0,(label,r.stdout,r.stderr);return r.stdout
sequence=int(remote('sequence','cat /run/muos/boot-diagnostic/sequence\n').strip());assert 1<=sequence<=9999
generation=remote('generation','cat /run/muos/session/current\n').strip();assert re.fullmatch(r'run-[0-9]{4}',generation)
names=['run/muos/boot/'+name for name in ['steps.txt','network-mode','start-result','network.start.log','network.recover.log','recovery.ready.log','usb.wait-remove.log','usb.wait-add.log','network.status.log']]
names += ['run/muos/boot-diagnostic/'+name for name in ['START.txt','FINAL.txt','start-rc','sequence','save-start.log','save-final.log','quiescent.log','network-status.log']]
names += ['run/muos/boot/network-owned/'+name for name in ['dropbear','dhcp','wpa']]
names += ['run/muos/boot/udev-owned/'+name for name in ['pid','identity']]
names += [f'run/muos/session/{generation}/'+name for name in ['result','report.txt','manager','profile-source.txt','profile-effective.txt','original-restored.txt','mixer-before.txt','mixer-after.txt','mixer-active.txt','software-volume.txt','brightness-before.txt','brightness-after.txt','drm-before.txt','drm-after.txt','volume-before.sha256','volume-after.sha256','root-writers.txt','rng.txt','first-paint.txt','ui-identity.txt','stop.log','restore.log','remount.txt']]
code=f'''set -eu
[ -f /run/muos/boot-diagnostic/FINAL.txt ]
[ -f /run/muos/session/{generation}/done ]
cd /;set --
for name in {' '.join(names)}; do
 [ -f "$name" ] || continue
 [ "$(stat -c %s "$name")" -le 524288 ]
 set -- "$@" "$name"
done
tar -cf - "$@"
'''
r=subprocess.run(ssh+['sh -s'],input=code.encode(),capture_output=True,timeout=30)
(stage/'collection.tar').write_bytes(r.stdout);(stage/'collection.stderr').write_bytes(r.stderr);assert r.returncode==0,r.stderr
out=stage/'native';out.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(r.stdout)) as archive:
 for entry in archive.getmembers():
  assert entry.isfile() and entry.name in names and entry.size<=524288
  target=out/entry.name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(archive.extractfile(entry).read())
code=f'''set -eu
boot_package=/usr/libexec/muos-boot
. "$boot_package/native-functions.sh"
c12_guard
c12_read_config
c12_session_quiescent || exit 1
c12_root_ro
[ -f /run/muos/entropy/stopped ];[ ! -e /run/muos/entropy/ready ]
[ ! -e /var/lib/muos-diagnostic/c12.once ]
[ "$(cat /run/muos/selection/mode)" = c12 ]
boot_state=/run/muos/boot
c12_native_step network.status
echo NETWORK_OWNERSHIP_OK
for name in dropbear dhcp wpa; do cat /run/muos/boot/network-owned/$name; done
findmnt -rn -o SOURCE,FSTYPE,OPTIONS /
echo TAINT=$(cat /proc/sys/kernel/tainted)
trap 'umount /boot' EXIT
mount -t vfat -o ro,nosuid,nodev,noexec "$boot_partition" /boot
[ "$(cat /boot/DIAG.ID)" = MUOS-R35S-EXT4-P4-B01 ]
cmp /run/muos/boot-diagnostic/START.txt /boot/DIAG10/BOOT{sequence:04d}/START.TXT
cmp /run/muos/boot-diagnostic/FINAL.txt /boot/DIAG10/BOOT{sequence:04d}/FINAL.TXT
echo FAT_REPORTS_IDENTICAL
umount /boot;trap - EXIT
! findmnt -rn -M /boot >/dev/null
echo FAT_UNMOUNTED
sha256sum -c /usr/libexec/muos-session/prerequisites.sha256
echo PREREQUISITES_OK
printf BACKLIGHT=;cat /sys/class/backlight/backlight/brightness
dmesg | awk '/Kernel panic|BUG:|Oops:|EXT4-fs error|I\\/O error|mmc.*timeout/ {{n++}} END{{printf "KERNEL_ERROR_SIGNATURES=%d\\n",n}}'
'''
health=remote('native-health',code)
checksums='\n'.join(v['sha256']+'  /'+name for name,v in meta['installed_files'].items())+'\n'
(stage/'installed.sha256').write_text(checksums)
remote('installed-checksums',"sha256sum -c - <<'PUBLIC_C12_SUMS'\n"+checksums+'PUBLIC_C12_SUMS\n')
s=out/f'run/muos/session/{generation}';b=out/'run/muos/boot';d=out/'run/muos/boot-diagnostic'
assert (s/'result').read_text().strip()=='0'
for name in ['profile-effective.txt','original-restored.txt']:
 lines=(s/name).read_text().splitlines();assert len(lines)==21 and all(x.endswith(': OK') for x in lines),name
for before,after in [('mixer-before.txt','mixer-after.txt'),('brightness-before.txt','brightness-after.txt'),('drm-before.txt','drm-after.txt'),('volume-before.sha256','volume-after.sha256')]:assert (s/before).read_bytes()==(s/after).read_bytes(),before
assert not re.search(rb'^(FD_WRITER|MAP_WRITER)',(s/'root-writers.txt').read_bytes(),re.M)
steps=(b/'steps.txt').read_text();assert 'STEP=entropy.start LIMIT=90 RC=0' in steps
assert steps.count('STEP=entropy.start ')==1
assert 'STEP=session.start LIMIT=120 RC=0' in steps and 'STEP=session.status LIMIT=5 RC=0' in steps
mode=(b/'network-mode').read_text().strip();assert mode in ['online','recovered']
if mode=='recovered':
 for step in ['recovery.ready','usb.wait-remove','usb.wait-add','network.recover','network.status']:
  assert re.search(r'^STEP='+re.escape(step)+r' LIMIT=[0-9]+ RC=0$',steps,re.M),step
final=(d/'FINAL.txt').read_text();assert 'SESSION_QUIESCENT_RC=0 NETWORK_RC=0' in final and 'START_LOG_SAVE_RC=0' in final
for marker in ['NETWORK_OWNERSHIP_OK','FAT_REPORTS_IDENTICAL','FAT_UNMOUNTED','TAINT=0','PREREQUISITES_OK','KERNEL_ERROR_SIGNATURES=0']:assert marker in health,marker
report={'passed':True,'boot_sequence':sequence,'network_mode':mode,'saved_seed_bootstrap_once':True,'physical_recovery_current_RNG_and_owned_processes':mode=='recovered','one_shot_consumed':True,'same_pinned_SSH_key':True,'session_generation':generation,'session_lease_expired_cleanup':'REASON=lease-expired' in (s/'report.txt').read_text(),'profile21_original21_mixer_brightness_DRM_volume_restored':True,'root_readonly_FAT_unmounted_taint0':True,'FAT_public_reports_match_RAM':True,'installed_public_files_match_host':True,'C07_fallback_next_boot_tested':False,'C12_power_or_shutdown_qualified':False,'persistent_user_settings_enabled':False,'postboot_offline_fsck_performed':False,'private_seed_credentials_keys_collected':False,'collector_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(stage/'boot-analysis.json').write_text(json.dumps(report,indent=2)+'\n');print('C12 native boot/archive/owned recovery/session/cleanup checks passed:',sequence,mode)
