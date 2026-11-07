#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Opt-in C20 real-data diagnostic; hardware execution requires completed storage."""
from pathlib import Path
import argparse,hashlib,ipaddress,json,re,subprocess,tempfile

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'preferences'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('operation',choices=['initialize','verify-after-reboot'])
p.add_argument('--host',required=True,type=ipaddress.IPv4Address);a=p.parse_args()
stage=Path(tempfile.mkdtemp(prefix='data-native.',dir=area))
checked=Path((area/'latest-checks').read_text().strip());meta=json.loads((checked/'manifest.json').read_text())
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert meta['host_passed'] and sha(checked/'muos-preferences')==meta['production_binary_sha256']
for name,digest in meta['sources'].items():assert sha(repo/name)==digest,name
assets=repo/'port/device/rk-r35s-p0/preferences'
payload={name:(assets/name).read_bytes() for name in ['data-functions.sh','diagnostic.sh']}
payload['card-guard.sh']=(repo/'port/device/rk-r35s-p0/linux-diagnostic/card-guard.sh').read_bytes()
payload['muos-preferences']=(checked/'muos-preferences').read_bytes()
ssh=['ssh','-p','2222','-i',str(work/'private/c07-client'),'-oIdentitiesOnly=yes',
 '-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222',
 '-oUserKnownHostsFile='+str(work/'private/c07-known_hosts'),'-oBatchMode=yes',
 '-oConnectTimeout=8','root@'+str(a.host)]
def remote(label,code,timeout=30,required=True):
    (stage/(label+'.sh')).write_text(code)
    r=subprocess.run(ssh+['sh -s'],input=code,text=True,capture_output=True,timeout=timeout)
    for suffix,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:
        (stage/(label+'.'+suffix)).write_text(value)
    if required:assert r.returncode==0,(label,r.stdout,r.stderr)
    return r
guard='''set -eu
boot_package=/usr/libexec/muos-boot
. "$boot_package/native-functions.sh"
c12_guard;c12_read_config;c12_root_ro
c12_session_quiescent || exit 1
[ "$(cat /run/muos/selection/mode)" = c07 ]
[ ! -e /var/lib/muos-diagnostic/c12.once ];[ ! -d /sys/module/btusb ]
[ "$(stat -c '%u:%g:%a' /)" = 0:0:755 ]
sha256sum -c /usr/libexec/muos-session/prerequisites.sha256 >/dev/null
/usr/libexec/muos-c07-network status
'''
directory=remote('allocate',guard+'umask 077\nmktemp -d /run/muos-prefs-data.XXXXXX\n').stdout.strip()
assert re.fullmatch(r'/run/muos-prefs-data\.[A-Za-z0-9]{6}',directory)
(stage/'native-directory').write_text(directory+'\n');cleanup_ok=False
try:
    for name,data in payload.items():
        r=subprocess.run(ssh+['cat > '+directory+'/'+name],input=data,capture_output=True,timeout=20)
        assert r.returncode==0,r.stderr
    hashes={name:hashlib.sha256(data).hexdigest() for name,data in payload.items()}
    verify=''.join(f"printf '%s  %s\\n' {digest} {directory}/{name} | sha256sum -c -\n" for name,digest in hashes.items())
    code=guard+verify+f'''
chmod 700 {directory}/muos-preferences
mkdir -m 700 {directory}/data
cat /proc/1/mountinfo > {directory}/global-before
printf 'BOOT_SEQ=';cat /var/lib/muos-diagnostic/boot-seq
printf 'BACKLIGHT_BEFORE=';cat /sys/class/backlight/backlight/brightness
/usr/libexec/muos-session/mount-namespace /usr/libexec/muos-session/bin/muos-run-bounded 45 /bin/sh {directory}/diagnostic.sh {a.operation}
cmp /proc/1/mountinfo {directory}/global-before
printf 'BACKLIGHT_AFTER=';cat /sys/class/backlight/backlight/brightness
'''+guard
    out=remote('native',code,timeout=65).stdout
    assert 'VOLUME=60\nBRIGHTNESS=75\n' in out and 'DATA_NATIVE_60_75_OK_ROOT_RO_NO_GLOBAL_MOUNT' in out
    assert 'BACKLIGHT_BEFORE=80\n' in out and 'BACKLIGHT_AFTER=80\n' in out
finally:
    code=guard+f'''
for info in /proc/[0-9]*/mountinfo;do
 [ -r "$info" ] || continue
 if grep -F ' {directory}/data ' "$info" >/dev/null 2>&1;then exit 1;fi
done
if [ -f {directory}/global-before ];then cmp /proc/1/mountinfo {directory}/global-before;fi
rm -f {directory}/data-functions.sh {directory}/diagnostic.sh {directory}/card-guard.sh {directory}/muos-preferences {directory}/global-before {directory}/default {directory}/saved {directory}/loaded
if [ -d {directory}/data ];then rmdir {directory}/data;fi
rmdir {directory}
echo OWNED_RAM_REMOVED_REAL_DATA_UNMOUNTED
'''
    cleanup_ok=remote('cleanup',code,required=False).returncode==0
assert cleanup_ok,'Cleanup refused; inspect evidence before removing any path'
result={'passed':True,'operation':a.operation,'real_p3_store_60_75':True,
        'root_ro_and_global_mounts_preserved':True,'readonly_and_absent_mount_refused':True,
        'RAM_removed_real_data_unmounted':True,'hardware_settings_not_applied':True,
        'runtime_firmware_integration_enabled':False,'audit_source_sha256':sha(Path(__file__)),
        'sources':{name:hashlib.sha256(data).hexdigest() for name,data in payload.items()}}
(stage/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
(area/('latest-data-'+a.operation)).write_text(str(stage)+'\n')
print('C20 real preferences store passed:',a.operation,stage)

