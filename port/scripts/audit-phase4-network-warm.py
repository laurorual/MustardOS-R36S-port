#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""One diagnostic reboot with8821cu log4; export only classified public events."""
from pathlib import Path
import argparse,hashlib,ipaddress,json,re,shutil,subprocess,tempfile

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/network-warm'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('action',choices=['install','boot','collect','cleanup'])
p.add_argument('--stage',type=Path);p.add_argument('--host',required=True,type=ipaddress.IPv4Address)
a=p.parse_args();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=repo/'port/device/rk-r35s-p0/network-warm-diagnostic'
if a.action=='install':
    assert a.stage is None
    checks=Path((area/'latest-checks').read_text().strip());checked=json.loads((checks/'report.json').read_text())
    assert checked['passed'] and sha(source/'driver-events.awk')==checked['classifier_sha256']
    stage=Path(tempfile.mkdtemp(prefix='probe.',dir=area))
    for n in ['probe.conf','driver-events.awk']:shutil.copyfile(source/n,stage/n)
    shutil.copyfile(Path(__file__),stage/Path(__file__).name)
    baseline=repo/'build/phase4/boot-order/power-test.feak98w7'
    assert json.loads((baseline/'power-analysis.json').read_text())['passed']
    meta={'experiment':'C13 retained-c820 probe observability','baseline_stage':str(baseline),
          'installed_files':json.loads((baseline/'manifest.json').read_text())['installed_files'],
          'config_sha256':sha(stage/'probe.conf'),'classifier_sha256':sha(stage/'driver-events.awk'),
          'checks_stage':str(checks),'checks':checked,'source_sha256':sha(Path(__file__)),
          'driver_kernel_DTB_init_unchanged':True,'only_temporary_modprobe_config':True,
          'raw_kernel_log_exported':False,'root_cause_or_fix_proven':False}
    (stage/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
    (area/'latest-probe').write_text(str(stage)+'\n')
else:
    assert a.stage is not None;stage=a.stage.resolve();assert stage.is_relative_to(area)
    meta=json.loads((stage/'manifest.json').read_text())
assert sha(Path(__file__))==meta['source_sha256'],'Use the frozen executed source to resume this experiment'
ssh=['ssh','-p','2222','-i',str(repo/'build/phase4/private/c07-client'),'-oIdentitiesOnly=yes',
     '-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222',
     '-oUserKnownHostsFile='+str(repo/'build/phase4/private/c07-known_hosts'),'-oBatchMode=yes',
     '-oConnectTimeout=8','root@'+str(a.host)]
def remote(label,code,timeout=40):
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
/usr/libexec/muos-c07-network status
sha256sum -c /usr/libexec/muos-session/prerequisites.sha256 >/dev/null
sha256sum -c - <<'C13_PUBLIC_INSTALLED_SUMS' >/dev/null
'''+sums+'''C13_PUBLIC_INSTALLED_SUMS
'''
config='/etc/modprobe.d/muos-c13-warm-probe.conf'
verify_config=f'''[ -f {config} ] && [ ! -L {config} ]
[ "$(sha256sum {config} | cut -d' ' -f1)" = {meta['config_sha256']} ]
[ "$(stat -c '%u:%g:%a' {config})" = 0:0:644 ]
'''
if a.action=='install':
    text=(stage/'probe.conf').read_text()
    out=remote('install',guard+f'''
[ ! -L /etc/modprobe.d ] && [ -d /etc/modprobe.d ]
[ ! -e {config} ] && [ ! -L {config} ]
[ ! -e {config}.tmp ] && [ ! -L {config}.tmp ]
[ "$(cat /sys/module/8821cu/parameters/rtw_drv_log_level)" = 3 ]
printf 'BASELINE_SEQUENCE=';cat /var/lib/muos-diagnostic/boot-seq
committed=0
finish() {{
 trap - EXIT
 if [ "$committed" = 0 ]; then
  rm -f {config}.tmp
  if [ -f {config} ] && [ "$(sha256sum {config} | cut -d' ' -f1)" = {meta['config_sha256']} ];then rm {config};fi
 fi
 sync;mount -o remount,ro /
}}
trap finish EXIT
mount -o remount,rw /
cat > {config}.tmp <<'C13_FIXED_MODPROBE_CONFIG'
{text}C13_FIXED_MODPROBE_CONFIG
chmod 644 {config}.tmp;chown 0:0 {config}.tmp
mv {config}.tmp {config}
{verify_config}
modprobe -c | awk '$1=="options" && $2=="8821cu" {{for(i=3;i<=NF;i++)if($i=="rtw_drv_log_level=4")n++}} END{{exit n!=1}}'
sync;mount -o remount,ro /;c12_root_ro
committed=1;trap - EXIT
echo C13_TEMP_CONFIG_INSTALLED_ROOT_RO_NO_REBOOT
''')
    seq=int(next(x.split('=')[1] for x in out.splitlines() if x.startswith('BASELINE_SEQUENCE=')))
    (stage/'baseline-sequence').write_text(str(seq)+'\n')
elif a.action=='boot':
    seq=int((stage/'baseline-sequence').read_text())
    with (stage/'reboot-attempted').open('x') as f:f.write('One observation reboot only\n')
    remote('boot-request',guard+verify_config+f'''
[ "$(cat /var/lib/muos-diagnostic/boot-seq)" = {seq} ]
(trap '' HUP;sleep 2;exec /sbin/reboot) </dev/null >/run/c13-reboot.log 2>&1 &
echo C13_OBSERVATION_REBOOT_SCHEDULED
''')
elif a.action=='collect':
    seq=int((stage/'baseline-sequence').read_text())+1
    directory=remote('allocate-collector',guard+verify_config+'mktemp -d /run/muos-c13.XXXXXX\n').strip()
    assert re.fullmatch(r'/run/muos-c13\.[A-Za-z0-9]{6}',directory)
    r=subprocess.run(ssh+['cat > '+directory+'/driver-events.awk'],input=(stage/'driver-events.awk').read_bytes(),capture_output=True,timeout=20)
    assert r.returncode==0,r.stderr
    out=remote('public-collection',guard+verify_config+f'''
[ "$(cat /var/lib/muos-diagnostic/boot-seq)" = {seq} ]
[ "$(cat /sys/module/8821cu/parameters/rtw_drv_log_level)" = 4 ]
[ "$(sha256sum {directory}/driver-events.awk | cut -d' ' -f1)" = {meta['classifier_sha256']} ]
echo EVENTS_BEGIN
dmesg | awk -f {directory}/driver-events.awk
echo EVENTS_END
echo REPORT_BEGIN
[ "$(stat -c %s /run/muos/c07/report.txt)" -le 262144 ]
cat /run/muos/c07/report.txt
echo REPORT_END
echo RECOVERY_BEGIN
if [ -f /run/muos/c07/recovery.txt ];then
 [ "$(stat -c %s /run/muos/c07/recovery.txt)" -le 65536 ];cat /run/muos/c07/recovery.txt
fi
echo RECOVERY_END
printf 'TAINT=';cat /proc/sys/kernel/tainted
findmnt -rn -o SOURCE,FSTYPE,OPTIONS /
rm {directory}/driver-events.awk;rmdir {directory}
''')
    for label,start,end in [('driver-events','EVENTS_BEGIN','EVENTS_END'),('initial-report','REPORT_BEGIN','REPORT_END'),('recovery','RECOVERY_BEGIN','RECOVERY_END')]:
        value=out.split(start+'\n')[1].split(end+'\n')[0];(stage/(label+'.txt')).write_text(value)
    events=(stage/'driver-events.txt').read_text()
    assert events.startswith('MUOS-C13-DRIVER-EVENTS-V1\n')
    for line in events.splitlines()[1:]:assert re.fullmatch(r'EVENT=[a-z_]+ COUNT=[0-9]+ FIRST=[0-9]+\.[0-9]{3} LAST=[0-9]+\.[0-9]{3}',line)
    (stage/'collection-analysis.json').write_text(json.dumps({'passed':True,'sequence':seq,'module_log_level_confirmed':4,'all_baseline_hashes_and_root_ro':True,'raw_dmesg_exported':False},indent=2)+'\n')
    print(events,end='')
else:
    assert json.loads((stage/'collection-analysis.json').read_text())['passed']
    remote('cleanup',guard+verify_config+f'''
trap 'mount -o remount,ro /' EXIT
mount -o remount,rw /
rm {config}
sync;mount -o remount,ro /;c12_root_ro;trap - EXIT
printf '3\n' > /sys/module/8821cu/parameters/rtw_drv_log_level
[ "$(cat /sys/module/8821cu/parameters/rtw_drv_log_level)" = 3 ]
[ ! -e {config} ]
/usr/libexec/muos-c07-network status
echo C13_CONFIG_REMOVED_LOG3_ROOT_RO_NETWORK_READY
''')
    (stage/'cleanup-analysis.json').write_text(json.dumps({'passed':True,'temporary_config_absent':True,'module_log_level_restored':3,'root_readonly_FAT_unmounted_taint0':True,'network_ready':True},indent=2)+'\n')
print('C13 diagnostic action completed:',a.action,stage)
