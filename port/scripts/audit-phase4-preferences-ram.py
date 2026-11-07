#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C19 native ABI/filesystem smoke test strictly in /run, with immediate cleanup."""
from pathlib import Path
import argparse,hashlib,ipaddress,json,re,subprocess
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'preferences'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',type=Path);p.add_argument('--host',required=True,type=ipaddress.IPv4Address);a=p.parse_args()
stage=a.stage.resolve();assert stage.is_relative_to(area)
m=json.loads((stage/'manifest.json').read_text());assert m['host_passed']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for n,d in m['sources'].items():assert sha(repo/n)==d,n
assert sha(stage/'muos-preferences')==m['production_binary_sha256']
ssh=['ssh','-p','2222','-i',str(work/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes',
     '-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(work/'private/c07-known_hosts'),
     '-oBatchMode=yes','-oConnectTimeout=8','root@'+str(a.host)]
def remote(label,code):
    (stage/(label+'.sh')).write_text(code)
    r=subprocess.run(ssh+['sh -s'],input=code,text=True,capture_output=True,timeout=25)
    for suffix,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:
        (stage/(label+'.'+suffix)).write_text(v)
    assert r.returncode==0,(label,r.stdout,r.stderr)
    return r.stdout
guard='''set -eu
boot_package=/usr/libexec/muos-boot
. "$boot_package/native-functions.sh"
c12_guard;c12_read_config;c12_root_ro
c12_session_quiescent || exit 1
[ "$(cat /run/muos/selection/mode)" = c07 ]
[ ! -e /var/lib/muos-diagnostic/c12.once ]
[ ! -d /sys/module/btusb ]
/usr/libexec/muos-c07-network status
sha256sum -c /usr/libexec/muos-session/prerequisites.sha256 >/dev/null
'''
assert not (stage/'native-directory').exists(),'Do not overwrite native test evidence'
directory=remote('native-allocate',guard+'mktemp -d /run/muos-prefs.XXXXXX\n').strip()
assert re.fullmatch(r'/run/muos-prefs\.[A-Za-z0-9]{6}',directory)
(stage/'native-directory').write_text(directory+'\n')
r=subprocess.run(ssh+['cat > '+directory+'/muos-preferences'],input=(stage/'muos-preferences').read_bytes(),capture_output=True,timeout=15);assert r.returncode==0
code=guard+f'''
[ "$(sha256sum {directory}/muos-preferences | cut -d' ' -f1)" = {m['production_binary_sha256']} ]
chmod 700 {directory}/muos-preferences
cleanup() {{
 rm -f {directory}/store/preferences {directory}/store/.preferences.new {directory}/store/.lock {directory}/store/.muos-preferences-v1
 rmdir {directory}/store
 rm -f {directory}/muos-preferences
 rmdir {directory}
}}
trap cleanup EXIT
umask 077
mkdir -m 700 {directory}/store
printf 'MUOS-R35S-PREFS-V1\\n' > {directory}/store/.muos-preferences-v1
printf 'BACKLIGHT_BEFORE=';cat /sys/class/backlight/backlight/brightness
{directory}/muos-preferences --dir {directory}/store init
{directory}/muos-preferences --dir {directory}/store save 60 75
{directory}/muos-preferences --dir {directory}/store init
set +e
{directory}/muos-preferences --dir {directory}/store save 101 75
rc=$?
set -e
[ "$rc" = 64 ]
echo INVALID_VOLUME_REFUSED_RC64
{directory}/muos-preferences --dir {directory}/store load
printf 'BACKLIGHT_AFTER=';cat /sys/class/backlight/backlight/brightness
cleanup;trap - EXIT
[ ! -e {directory} ]
c12_guard;c12_root_ro
/usr/libexec/muos-c07-network status
echo NATIVE_RAM_STORE_OK_REMOVED_ROOT_RO_FAT_UNMOUNTED_TAINT0
'''
out=remote('native-smoke',code)
assert out.count('VOLUME=60\n')==3 and out.count('BRIGHTNESS=75\n')==3
assert 'BACKLIGHT_BEFORE=80\n' in out and 'BACKLIGHT_AFTER=80\n' in out
(stage/'native-analysis.json').write_text(json.dumps({'passed':True,'native_AArch64_ABI_and_tmpfs_store':True,
 'existing_value_preserved_by_init':True,'invalid_input_refused':True,'binary_and_RAM_store_removed':True,
 'root_readonly_FAT_unmounted_taint0_wifi_preserved':True,'hardware_volume_brightness_not_changed':True,
 'partitions_or_persistent_device_files_modified':False,'ext4_data_mount_or_reboot_persistence_tested':False,
 'audit_source_sha256':sha(Path(__file__))},indent=2)+'\n')
print('C19 native RAM-only store passed and removed; no display/audio/root/partition changes.')
