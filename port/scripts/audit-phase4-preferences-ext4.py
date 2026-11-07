#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Run C19 ext4/remount and cancellation tests using only an owned tmpfs image."""
from pathlib import Path
import argparse,gzip,hashlib,io,ipaddress,json,re,subprocess,tarfile

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'preferences'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('stage',type=Path);p.add_argument('--host',required=True,type=ipaddress.IPv4Address)
a=p.parse_args();stage=a.stage.resolve();assert stage.is_relative_to(area)
meta=json.loads((stage/'manifest.json').read_text());assert meta['host_passed']
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
for n,d in meta['sources'].items():assert sha(repo/n)==d,n
for n,d in meta['payloads'].items():assert sha(stage/n)==d,n
assert not (stage/'native-directory').exists(),'Never overwrite native evidence'
ssh=['ssh','-p','2222','-i',str(work/'private/c07-client'),'-oIdentitiesOnly=yes',
 '-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222',
 '-oUserKnownHostsFile='+str(work/'private/c07-known_hosts'),'-oBatchMode=yes',
 '-oConnectTimeout=8','-oServerAliveInterval=10','-oServerAliveCountMax=3','root@'+str(a.host)]
def remote(label,code,timeout=30,required=True):
    (stage/(label+'.sh')).write_text(code)
    r=subprocess.run(ssh+['sh -s'],input=code,text=True,capture_output=True,timeout=timeout)
    for suffix,text in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:
        (stage/(label+'.'+suffix)).write_text(text)
    if required:assert r.returncode==0,(label,r.stdout,r.stderr)
    return r
guard='''set -eu
boot_package=/usr/libexec/muos-boot
. "$boot_package/native-functions.sh"
c12_guard;c12_read_config;c12_root_ro
c12_session_quiescent || exit 1
[ "$(cat /run/muos/selection/mode)" = c07 ]
[ ! -e /var/lib/muos-diagnostic/c12.once ];[ ! -d /sys/module/btusb ]
/usr/libexec/muos-c07-network status
sha256sum -c /usr/libexec/muos-session/prerequisites.sha256 >/dev/null
'''
loops_clear='''for loop in /sys/class/block/loop[0-7]; do
 [ ! -e "$loop/loop/backing_file" ] || exit 1
done
'''
directory=remote('native-allocate',guard+loops_clear+'''awk '/MemAvailable:/ {if ($2<131072) exit 1}' /proc/meminfo
umask 077
mktemp -d /run/muos-prefs-ext4.XXXXXX
''').stdout.strip()
assert re.fullmatch(r'/run/muos-prefs-ext4\.[A-Za-z0-9]{6}',directory)
(stage/'native-directory').write_text(directory+'\n')
cleanup=guard+loops_clear+f'''
[ ! -L {directory} ] && [ "$(stat -c '%u:%g:%a' {directory})" = 0:0:700 ]
for info in /proc/[0-9]*/mountinfo; do
 [ -r "$info" ] || continue
 if grep -F ' {directory}/mnt ' "$info" >/dev/null 2>&1; then exit 1; fi
done
if [ -f {directory}/global-before ]; then cmp /proc/1/mountinfo {directory}/global-before; fi
rm -f {directory}/phase4-preferences-ext4 {directory}/muos-preferences {directory}/data.ext4 {directory}/global-before
if [ -d {directory}/mnt ]; then rmdir {directory}/mnt; fi
rmdir {directory}
[ ! -e {directory} ]
echo RAM_IMAGE_BINARIES_DIRECTORY_REMOVED_ROOT_RO
'''
passed=False;cleanup_ok=False
try:
    payload=io.BytesIO()
    with tarfile.open(fileobj=payload,mode='w') as archive:
        for n in meta['payloads']:
            data=(stage/n).read_bytes();entry=tarfile.TarInfo(n)
            entry.size=len(data);entry.mode=0o600 if n=='data.ext4' else 0o700
            entry.uid=entry.gid=0;archive.addfile(entry,io.BytesIO(data))
    r=subprocess.run(ssh+['tar -xf - -C '+directory],input=payload.getvalue(),capture_output=True,timeout=35)
    (stage/'native-upload.stderr').write_bytes(r.stderr);assert r.returncode==0,r.stderr
    hashes=''.join(f"printf '%s  %s\\n' {d} {directory}/{n} | sha256sum -c -\n" for n,d in meta['payloads'].items())
    script=guard+loops_clear+hashes+f'''
mkdir -m 700 {directory}/mnt
cat /proc/1/mountinfo > {directory}/global-before
printf 'BOOT_SEQ=';cat /var/lib/muos-diagnostic/boot-seq
printf 'BACKLIGHT_BEFORE=';cat /sys/class/backlight/backlight/brightness
{directory}/phase4-preferences-ext4 {directory}
'''+loops_clear+f'''
cmp /proc/1/mountinfo {directory}/global-before
set +e
{directory}/phase4-preferences-ext4 {directory} --cancel-after-mount
rc=$?
set -e
[ "$rc" = 143 ]
echo PASS_SIGTERM_CLEANUP_RC143
'''+loops_clear+f'''
cmp /proc/1/mountinfo {directory}/global-before
printf 'BACKLIGHT_AFTER=';cat /sys/class/backlight/backlight/brightness
c12_guard;c12_root_ro
c12_session_quiescent || exit 1
sha256sum -c /usr/libexec/muos-session/prerequisites.sha256 >/dev/null
/usr/libexec/muos-c07-network status
echo NATIVE_EXT4_AND_CANCEL_OK_GLOBAL_MOUNTS_IDENTICAL
'''
    out=remote('native-smoke',script,timeout=110).stdout
    assert 'EXT4_LAB_OK_ROOT_RO_NO_CARD_WRITES' in out
    assert 'PASS_SIGTERM_CLEANUP_RC143' in out
    assert 'BACKLIGHT_BEFORE=80\n' in out and 'BACKLIGHT_AFTER=80\n' in out
    # Fetch only the unmounted laboratory image; never fsck any live filesystem.
    r=subprocess.run(ssh+['gzip -c '+directory+'/data.ext4'],capture_output=True,timeout=30)
    assert r.returncode==0,r.stderr
    data=gzip.decompress(r.stdout);assert len(data)==16777216
    (stage/'after.ext4').write_bytes(data)
    passed=True
finally:
    r=remote('native-cleanup',cleanup,required=False)
    cleanup_ok=r.returncode==0
    if not cleanup_ok:print('Cleanup refused: inspect native-cleanup evidence; do not remove an attached image.')
assert passed and cleanup_ok
relative='/work/'+str(stage.relative_to(work))
code=f'''set -eu
cd {relative}
e2fsck -fn after.ext4 > fsck-after.txt 2>&1
debugfs -R 'cat /store/preferences' after.ext4 > record-after.txt 2> debugfs-after.stderr
'''
r=subprocess.run(['podman','run','--rm','--network=none','--read-only','--cap-drop=all',
 '--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev',
 '-v',f'{work}:/work:rw,z',meta['container'],'sh','-c',code],capture_output=True,text=True,timeout=30)
(stage/'offline-check.stderr').write_text(r.stderr);assert r.returncode==0,(r.stdout,r.stderr)
assert (stage/'record-after.txt').read_text()=='MUOS-PREFS-1\nVOLUME=60\nBRIGHTNESS=75\n'
analysis={'passed':True,'native_AArch64_ext4_rw_unmount_remount':True,'defaults_preserve_60_75':True,
 'absent_wrong_backing_and_readonly_refused':True,'SIGTERM_cleanup_rc143':True,
 'global_mounts_identical_root_ro_FAT_unmounted_taint0_wifi_preserved':True,
 'owned_loop_detached_and_RAM_directory_removed':True,'hardware_settings_unchanged':True,
 'after_image_offline_fsck_passed':True,'after_image_sha256':sha(stage/'after.ext4'),
 'card_partitions_or_persistent_device_files_modified':False,'reboot_persistence_tested':False,
 'persistent_mode_enabled':False,'audit_source_sha256':sha(Path(__file__))}
(stage/'native-analysis.json').write_text(json.dumps(analysis,indent=2)+'\n')
print('C19 native ext4/remount + SIGTERM cleanup passed; all RAM resources removed; offline image fsck passed.')
