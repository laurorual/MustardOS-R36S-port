#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C18: two bounded observation cycles with btusb alias autoload disabled."""
from pathlib import Path
import argparse,hashlib,ipaddress,json,re,shutil,subprocess,tempfile
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'network-warm'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('action',choices=['install','boot','collect','cleanup'])
p.add_argument('--stage',type=Path);p.add_argument('--cycle',type=int,choices=[1,2],default=1)
p.add_argument('--host',required=True,type=ipaddress.IPv4Address);a=p.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if a.action=='install':
    assert a.stage is None
    stage=Path(tempfile.mkdtemp(prefix='bt-isolation.',dir=area))
    source=repo/'port/device/rk-r35s-p0/network-warm-diagnostic/btusb-blacklist.conf'
    shutil.copyfile(source,stage/'btusb-blacklist.conf')
    baseline=work/'boot-order/power-test.feak98w7'
    meta={'experiment':'C18 btusb alias isolation before Wi-Fi probe','config_sha256':sha(source),
          'installed_files':json.loads((baseline/'manifest.json').read_text())['installed_files'],
          'source_sha256':sha(Path(__file__)),'kernel_DTB_driver_init_unchanged':True}
    (stage/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
    shutil.copyfile(Path(__file__),stage/Path(__file__).name);(area/'latest-bt-isolation').write_text(str(stage)+'\n')
else:
    assert a.stage is not None;stage=a.stage.resolve();assert stage.is_relative_to(area)
    meta=json.loads((stage/'manifest.json').read_text())
assert sha(Path(__file__))==meta['source_sha256']
ssh=['ssh','-p','2222','-i',str(work/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes',
     '-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(work/'private/c07-known_hosts'),
     '-oBatchMode=yes','-oConnectTimeout=8','root@'+str(a.host)]
def remote(label,code,timeout=35):
    (stage/(label+'.sh')).write_text(code)
    r=subprocess.run(ssh+['sh -s'],input=code,text=True,capture_output=True,timeout=timeout)
    for suffix,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:
        (stage/(label+'.'+suffix)).write_text(value)
    assert r.returncode==0,(label,r.stdout,r.stderr)
    return r.stdout
sums=''.join(v['sha256']+'  /'+n+'\n' for n,v in sorted(meta['installed_files'].items()))
guard='''set -eu
boot_package=/usr/libexec/muos-boot
. "$boot_package/native-functions.sh"
c12_guard;c12_read_config;c12_root_ro
c12_session_quiescent || exit 1
[ "$(cat /run/muos/selection/mode)" = c07 ]
[ ! -e /var/lib/muos-diagnostic/c12.once ]
[ "$allow_power" = 0 ]
[ ! -e /usr/libexec/muos-c16 ]
[ ! -e /var/lib/muos-diagnostic/c17.c16-used ]
/usr/libexec/muos-c07-network status
sha256sum -c /usr/libexec/muos-session/prerequisites.sha256 >/dev/null
sha256sum -c - <<'C18_PUBLIC_INSTALLED_SUMS' >/dev/null
'''+sums+'''C18_PUBLIC_INSTALLED_SUMS
'''
config='/etc/modprobe.d/muos-c18-btusb-blacklist.conf'
verify=f'''[ -f {config} ] && [ ! -L {config} ]
[ "$(stat -c '%u:%g:%a:%h' {config})" = 0:0:644:1 ]
[ "$(sha256sum {config} | cut -d' ' -f1)" = {meta['config_sha256']} ]
'''
if a.action=='install':
    text=(stage/'btusb-blacklist.conf').read_text()
    out=remote('install',guard+f'''
[ ! -L /etc/modprobe.d ]
[ ! -e {config} ] && [ ! -L {config} ]
[ ! -e {config}.tmp ] && [ ! -L {config}.tmp ]
[ -d /sys/module/btusb ]
printf 'BASELINE_SEQUENCE=';cat /var/lib/muos-diagnostic/boot-seq
trap 'mount -o remount,ro /' EXIT
mount -o remount,rw /
cat > {config}.tmp <<'C18_FIXED_CONFIG'
{text}C18_FIXED_CONFIG
chmod 644 {config}.tmp;chown 0:0 {config}.tmp
mv {config}.tmp {config}
sync;mount -o remount,ro /;c12_root_ro;trap - EXIT
{verify}
modprobe -c | awk '$1=="blacklist" && $2=="btusb" {{n++}} END{{exit n!=1}}'
echo C18_BLACKLIST_PARSED_ORIGINAL_BT_MODULE_LEFT_RUNNING
''')
    seq=int(next(v.split('=')[1] for v in out.splitlines() if v.startswith('BASELINE_SEQUENCE=')))
    (stage/'baseline-sequence').write_text(str(seq)+'\n')
elif a.action=='boot':
    seq=int((stage/'baseline-sequence').read_text())+a.cycle-1
    if a.cycle==2:
        previous=json.loads((stage/'cycle-1-analysis.json').read_text());assert previous['btusb_absent']
    with (stage/f'cycle-{a.cycle}-requested').open('x') as f:f.write('Distinct cycle; Bluetooth absent on both sides only in cycle2\n')
    code=guard+verify+f'[ "$(cat /var/lib/muos-diagnostic/boot-seq)" = {seq} ]\n'
    if a.cycle==2:code+='[ ! -d /sys/module/btusb ]\n'
    code+='(trap \'\' HUP;sleep 2;exec /sbin/reboot) </dev/null >/run/c18-reboot.log 2>&1 &\necho C18_REBOOT_SCHEDULED\n'
    remote(f'cycle-{a.cycle}-boot',code)
elif a.action=='collect':
    seq=int((stage/'baseline-sequence').read_text())+a.cycle
    out=remote(f'cycle-{a.cycle}-collection',guard+verify+f'''
[ "$(cat /var/lib/muos-diagnostic/boot-seq)" = {seq} ]
if [ -d /sys/module/btusb ];then echo BTUSB_PRESENT=1;else echo BTUSB_PRESENT=0;fi
for p in /sys/bus/usb/devices/*;do
 [ -r "$p/idVendor" ] && [ -r "$p/idProduct" ] || continue
 [ "$(cat "$p/idVendor"):$(cat "$p/idProduct")" = 0bda:c820 ] || continue
 for intf in "$p":*;do
  [ -r "$intf/bInterfaceClass" ] || continue
  name=none;[ ! -L "$intf/driver" ] || name=$(basename "$(readlink -f "$intf/driver")")
  printf 'INTERFACE=%s CLASS=%s DRIVER=%s\\n' "$(cat "$intf/bInterfaceNumber")" "$(cat "$intf/bInterfaceClass")" "$name"
 done
done
echo REPORT_BEGIN
cat /run/muos/c07/report.txt
echo REPORT_END
echo RECOVERY_BEGIN
if [ -f /run/muos/c07/recovery.txt ];then cat /run/muos/c07/recovery.txt;fi
echo RECOVERY_END
trap 'umount /boot' EXIT
mount -t vfat -o ro,nosuid,nodev,noexec "$boot_partition" /boot
[ "$(cat /boot/DIAG.ID)" = MUOS-R35S-EXT4-P4-B01 ]
cmp /run/muos/c07/report.txt /boot/DIAG09/BOOT{seq:04d}/REPORT.TXT
umount /boot;trap - EXIT
c12_guard;c12_root_ro
''')
    report=out.split('REPORT_BEGIN\n')[1].split('REPORT_END\n')[0]
    recovery=out.split('RECOVERY_BEGIN\n')[1].split('RECOVERY_END\n')[0]
    (stage/f'cycle-{a.cycle}-initial-report.txt').write_text(report)
    (stage/f'cycle-{a.cycle}-recovery.txt').write_text(recovery)
    absent='BTUSB_PRESENT=0' in out and not re.search(r'^btusb ',report,re.M)
    m={'collected':True,'sequence':seq,'btusb_absent':absent,
       'BT_absent_before_and_after_reboot':a.cycle==2 and absent,
       'automatic_network_ready':'STATUS=0 ROOT_RO=1' in report and not recovery.strip(),
       'all_55_prerequisites_and_baseline_hashes_passed':True,'root_readonly_FAT_unmounted_taint0':True}
    (stage/f'cycle-{a.cycle}-analysis.json').write_text(json.dumps(m,indent=2)+'\n')
    print(json.dumps(m,indent=2))
else:
    assert (stage/'cycle-1-analysis.json').exists()
    remote('cleanup',guard+verify+f'''
trap 'mount -o remount,ro /' EXIT
mount -o remount,rw /
rm {config}
sync;mount -o remount,ro /;c12_root_ro;trap - EXIT
[ ! -e {config} ]
/usr/libexec/muos-c07-network status
echo C18_POLICY_RESTORED_ROOT_RO_NETWORK_READY_NO_FORCED_BT_PROBE
''')
    (stage/'cleanup-analysis.json').write_text(json.dumps({'passed':True,'temporary_config_removed':True,'root_readonly_FAT_unmounted_taint0':True,'network_ready':True,'btusb_runtime_not_forced_to_load':True},indent=2)+'\n')
print('C18 action completed:',a.action,stage)
