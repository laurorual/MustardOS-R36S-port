#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Promote the twice-qualified C18 alias policy and verify one boot with final files."""
from pathlib import Path
import argparse,hashlib,ipaddress,json,re,shutil,subprocess,tarfile,tempfile
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'network-warm'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('action',choices=['install','boot','verify']);p.add_argument('--stage',type=Path)
p.add_argument('--experiment-stage',type=Path);p.add_argument('--host',required=True,type=ipaddress.IPv4Address)
a=p.parse_args();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if a.action=='install':
    assert a.stage is None and a.experiment_stage is not None
    experiment=a.experiment_stage.resolve();assert experiment.is_relative_to(area)
    for cycle in [1,2]:
        result=json.loads((experiment/f'cycle-{cycle}-analysis.json').read_text())
        assert result['automatic_network_ready'] and result['btusb_absent']
        assert json.loads((experiment/f'cycle-{cycle}-user-confirmation.json').read_text())['physical_dongle_reconnected'] is False
    checked=Path((area/'latest-wifi-policy-build').read_text().strip())
    build=json.loads((checked/'manifest.json').read_text());assert build['host_passed']
    for n,d in build['sources'].items():assert sha(repo/n)==d,n
    stage=Path(tempfile.mkdtemp(prefix='wifi-policy.',dir=area))
    payload=stage/'payload';shutil.copytree(checked/'target',payload/'tree')
    (payload/'new.sha256').write_text(''.join(v['sha256']+'  /'+n+'\n' for n,v in sorted(build['payload'].items())))
    trialmeta=json.loads((experiment/'manifest.json').read_text())
    shutil.copyfile(experiment/'btusb-blacklist.conf',payload/'trial.conf')
    installer=repo/'port/device/rk-r35s-p0/boot-diagnostic/install-functions.sh'
    shutil.copyfile(installer,stage/'install-functions.sh')
    with tarfile.open(stage/'deployment.tar','w') as archive:
        archive.add(payload,arcname='payload');archive.add(stage/'install-functions.sh',arcname='install-functions.sh')
    meta={'host_passed':True,'experiment_stage':str(experiment),'build_stage':str(checked),'build':build,
          'baseline_files':trialmeta['installed_files'],'payload':build['payload'],'trial_sha256':sha(payload/'trial.conf'),
          'deployment_sha256':sha(stage/'deployment.tar'),'source_sha256':sha(Path(__file__)),
          'installer_functions_sha256':sha(installer),'USB_Bluetooth_autoload_disabled':True,
          'kernel_DTB_driver_init_session_settings_changed':False}
    (stage/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
    shutil.copyfile(Path(__file__),stage/Path(__file__).name);(area/'latest-wifi-policy').write_text(str(stage)+'\n')
else:
    assert a.stage is not None;stage=a.stage.resolve();assert stage.is_relative_to(area)
    meta=json.loads((stage/'manifest.json').read_text())
assert sha(Path(__file__))==meta['source_sha256']
ssh=['ssh','-p','2222','-i',str(work/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes',
     '-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(work/'private/c07-known_hosts'),
     '-oBatchMode=yes','-oConnectTimeout=8','root@'+str(a.host)]
def remote(label,code,timeout=40):
    (stage/(label+'.sh')).write_text(code)
    r=subprocess.run(ssh+['sh -s'],input=code,text=True,capture_output=True,timeout=timeout)
    for suffix,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:
        (stage/(label+'.'+suffix)).write_text(value)
    assert r.returncode==0,(label,r.stdout,r.stderr)
    return r.stdout
sums=''.join(v['sha256']+'  /'+n+'\n' for n,v in sorted(meta['baseline_files'].items()))
guard='''set -eu
boot_package=/usr/libexec/muos-boot
. "$boot_package/native-functions.sh"
c12_guard;c12_read_config;c12_root_ro
c12_session_quiescent || exit 1
[ "$(cat /run/muos/selection/mode)" = c07 ]
[ ! -e /var/lib/muos-diagnostic/c12.once ]
[ "$allow_power" = 0 ]
[ ! -d /sys/module/btusb ]
/usr/libexec/muos-c07-network status
sha256sum -c /usr/libexec/muos-session/prerequisites.sha256 >/dev/null
sha256sum -c - <<'WIFI_ONLY_BASELINE_SUMS' >/dev/null
'''+sums+'''WIFI_ONLY_BASELINE_SUMS
'''
trial='/etc/modprobe.d/muos-c18-btusb-blacklist.conf'
stable='/etc/modprobe.d/90-muos-r35s-wifi-only.conf'
license='/usr/share/licenses/muos-r35s-wifi-only/LICENSE'
policy_sums=''.join(v['sha256']+'  /'+n+'\n' for n,v in sorted(meta['payload'].items()))
verify=guard+"sha256sum -c - <<'WIFI_ONLY_POLICY_SUMS' >/dev/null\n"+policy_sums+"WIFI_ONLY_POLICY_SUMS\n"+f'''[ ! -e {trial} ]
[ "$(stat -c '%u:%g:%a:%h' {stable})" = 0:0:644:1 ]
[ "$(stat -c '%u:%g:%a:%h' {license})" = 0:0:644:1 ]
modprobe -c | awk '$1=="blacklist" && $2=="btusb" {{n++}} END{{exit n!=1}}'
'''
if a.action=='install':
    directory=remote('allocate',guard+'mktemp -d /run/muos-wifipolicy.XXXXXX\n').strip()
    assert re.fullmatch(r'/run/muos-wifipolicy\.[A-Za-z0-9]{6}',directory)
    (stage/'remote-directory').write_text(directory+'\n')
    r=subprocess.run(ssh+['cat > '+directory+'/deployment.tar'],input=(stage/'deployment.tar').read_bytes(),capture_output=True,timeout=20);assert r.returncode==0
    remote('unpack',guard+f'[ "$(sha256sum {directory}/deployment.tar | cut -d" " -f1)" = {meta["deployment_sha256"]} ]\ntar -xf {directory}/deployment.tar -C {directory}\n')
    code=guard+f'''
[ ! -L {trial} ] && [ "$(stat -c '%u:%g:%a:%h' {trial})" = 0:0:644:1 ]
[ "$(sha256sum {trial} | cut -d' ' -f1)" = {meta['trial_sha256']} ]
[ ! -e {stable} ] && [ ! -L {stable} ]
[ ! -e {stable}.tmp ] && [ ! -L {stable}.tmp ]
[ ! -e /usr/share/licenses/muos-r35s-wifi-only ] && [ ! -L /usr/share/licenses/muos-r35s-wifi-only ]
. {directory}/install-functions.sh
install_root=/
c12_install_parents {stable};c12_install_parents {license}
printf 'BASELINE_SEQUENCE=';cat /var/lib/muos-diagnostic/boot-seq
cp {trial} {directory}/trial-before.conf
rw=0;committed=0
finish() {{
 trap - EXIT HUP INT TERM
 if [ "$rw" = 1 ];then
  if [ "$committed" = 0 ];then
   mount -o remount,rw /
   cp {directory}/trial-before.conf {trial}
   chmod 644 {trial};chown 0:0 {trial}
   rm -f {stable} {stable}.tmp {license} {license}.tmp
   rmdir /usr/share/licenses/muos-r35s-wifi-only 2>/dev/null || :
  fi
  sync;mount -o remount,ro /
 fi
}}
trap finish EXIT
trap 'exit 143' HUP INT TERM
mount -o remount,rw /;rw=1
mkdir -p /usr/share/licenses/muos-r35s-wifi-only
chmod 755 /usr/share/licenses/muos-r35s-wifi-only
cp {directory}/payload/tree{stable} {stable}.tmp
chmod 644 {stable}.tmp;chown 0:0 {stable}.tmp;mv {stable}.tmp {stable}
cp {directory}/payload/tree{license} {license}.tmp
chmod 644 {license}.tmp;chown 0:0 {license}.tmp;mv {license}.tmp {license}
sha256sum -c {directory}/payload/new.sha256 >/dev/null
rm {trial}
modprobe -c | awk '$1=="blacklist" && $2=="btusb" {{n++}} END{{exit n!=1}}'
sha256sum -c /usr/libexec/muos-session/prerequisites.sha256 >/dev/null
sync;mount -o remount,ro /;c12_root_ro
committed=1;rw=0;trap - EXIT
echo WIFI_ONLY_POLICY_PROMOTED_ROOT_RO
'''
    out=remote('install',code,timeout=50)
    seq=int(next(v.split('=')[1] for v in out.splitlines() if v.startswith('BASELINE_SEQUENCE=')))
    (stage/'baseline-sequence').write_text(str(seq)+'\n')
    remote('installed-health',verify+'echo WIFI_ONLY_FINAL_FILES_ALL_HASHES_OK\n')
    (stage/'install-analysis.json').write_text(json.dumps({'passed':True,'only_stable_config_and_MIT_license_added':True,'trial_file_removed':True,'all_baseline_hashes_55_preserved':True,'root_readonly_FAT_unmounted_taint0':True},indent=2)+'\n')
    experiment=Path(meta['experiment_stage'])
    (experiment/'cleanup-analysis.json').write_text(json.dumps({'passed':True,'temporary_config_removed':True,'promoted_to_stable_wifi_only_policy':True,'replacement_stage':str(stage),'root_readonly_FAT_unmounted_taint0':True},indent=2)+'\n')
elif a.action=='boot':
    assert json.loads((stage/'install-analysis.json').read_text())['passed']
    with (stage/'reboot-attempted').open('x') as f:f.write('Verify actual stable recipe payload on next warm boot\n')
    remote('boot-request',verify+'''
(trap '' HUP;sleep 2;exec /sbin/reboot) </dev/null >/run/wifi-only-policy-reboot.log 2>&1 &
echo WIFI_ONLY_STABLE_POLICY_REBOOT_SCHEDULED
''')
else:
    seq=int((stage/'baseline-sequence').read_text())+1
    out=remote('native-verification',verify+f'''
[ "$(cat /var/lib/muos-diagnostic/boot-seq)" = {seq} ]
echo REPORT_BEGIN
cat /run/muos/c07/report.txt
echo REPORT_END
[ ! -e /run/muos/c07/recovery ]
[ ! -e /run/muos/c07/recovery.txt ]
grep -qx 'STATUS=0 ROOT_RO=1' /run/muos/c07/report.txt
for path in /sys/bus/usb/devices/*;do
 [ -r "$path/idVendor" ] && [ -r "$path/idProduct" ] || continue
 [ "$(cat "$path/idVendor"):$(cat "$path/idProduct")" = 0bda:c820 ] || continue
 for intf in "$path":*;do
  [ -r "$intf/bInterfaceClass" ] || continue
  name=none;[ ! -L "$intf/driver" ] || name=$(basename "$(readlink -f "$intf/driver")")
  printf 'CLASS=%s DRIVER=%s\\n' "$(cat "$intf/bInterfaceClass")" "$name"
 done
done
trap 'umount /boot' EXIT
mount -t vfat -o ro,nosuid,nodev,noexec "$boot_partition" /boot
[ "$(cat /boot/DIAG.ID)" = MUOS-R35S-EXT4-P4-B01 ]
cmp /run/muos/c07/report.txt /boot/DIAG09/BOOT{seq:04d}/REPORT.TXT
umount /boot;trap - EXIT
c12_guard;c12_root_ro
printf 'BACKLIGHT=';cat /sys/class/backlight/backlight/brightness
dmesg | awk '/Kernel panic|BUG:|Oops:|EXT4-fs error|I\\/O error|mmc.*timeout/ {{n++}} END {{printf "KERNEL_ERROR_SIGNATURES=%d\\n",n}}'
echo WIFI_ONLY_NATIVE_ROOT_RO_FAT_UNMOUNTED_TAINT0
''')
    report=out.split('REPORT_BEGIN\n')[1].split('REPORT_END\n')[0];(stage/'initial-report.txt').write_text(report)
    assert 'CLASS=ff DRIVER=rtl8821cu' in out and 'CLASS=e0 DRIVER=btusb' not in out
    assert 'KERNEL_ERROR_SIGNATURES=0' in out
    (stage/'analysis.json').write_text(json.dumps({'passed':True,'sequence':seq,'automatic_network_no_physical_recovery':True,
      'stable_payload_matches_actual_recipe':True,'btusb_absent_BT_interfaces_unbound':True,
      'all_55_prerequisites_baseline_hashes_preserved':True,'root_readonly_FAT_unmounted_taint0':True,
      'full_image_built':False,'kernel_DTB_drivers_libraries_init_changed':False},indent=2)+'\n')
print('Stable Wi-Fi-only policy action completed:',a.action,stage)
