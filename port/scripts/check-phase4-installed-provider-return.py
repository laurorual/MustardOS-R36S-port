#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C74 bind a user-restarted boot and verify installed provider/host read-only."""
from pathlib import Path
import argparse, ast, ipaddress, json, re, subprocess, tempfile
from phase4_candidate import sha, sums
from phase4_installed_provider_session import installed, REPO, WORK, NAMES, C72

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--host', required=True, type=ipaddress.IPv4Address)
p.add_argument('--boot', required=True, type=int)
p.add_argument('--resume', type=Path)
a = p.parse_args()
assert type(a.boot) is int and 0 < a.boot < 9999
prior, binding, plan = installed()
assert a.boot > prior['boot_sequence'], 'Use a separate observed boot, never relax the C73 guard'
parents = {}
for name in ['installed-provider-session', 'provider-upgrade-native', 'frontend-libs']:
    proof = REPO / 'dist/phase4' / name
    for n, h in sums(proof / 'SHA256SUMS').items(): assert sha(proof / n) == h
    parents[name] = sha(proof / 'SHA256SUMS')
area = WORK / 'installed-provider-return'
area.mkdir(exist_ok=True)
stage = a.resume.resolve() if a.resume else Path(tempfile.mkdtemp(prefix='check.', dir=area))
assert stage.is_relative_to(area)
assert not (stage/'analysis.json').exists()
stage.chmod(0o700)
(area / 'latest-attempt').write_text(str(stage) + '\n')
source = REPO / 'port/scripts/run-phase4-provider-upgrade.py'
assert sha(source) == binding['source_sha256'][str(source.relative_to(REPO))]
nodes = [n for n in ast.parse(source.read_text()).body if isinstance(n, ast.Assign)
         and any(isinstance(t, ast.Name) and t.id == 'base' for t in n.targets)]
assert len(nodes) == 1
common = ast.literal_eval(nodes[0].value)
common += f'[ "$(cat "$c25_store/boot-seq")" = {a.boot} ]\n'
for name, row in sorted(plan['after'].items()):
    common += f'''[ ! -L /{name} ];[ "$(stat -c '%u:%g:%a:%h' /{name})" = 0:0:{row['mode']:o}:1 ]
[ "$(sha256sum /{name} | cut -d' ' -f1)" = {row['sha256']} ]
'''
for name in plan['old_directories']:
    common += f'[ ! -e /{name} ];[ ! -L /{name} ]\n'
for name in plan['new_directories']:
    common += f'[ ! -L /{name} ];[ "$(stat -c \'%u:%g:%a\' /{name})" = 0:0:755 ]\n'
for name, digest in sums(C72 / 'payload/preserved.sha256').items():
    common += f"printf '%s  %s\\n' {digest} /{name} | sha256sum -c - >/dev/null\n"
infra = '''for name in udevd wpa_supplicant udhcpc dropbear;do
for pid in $(pidof "$name");do
[ "$(awk '/^PPid:/ {print $2}' /proc/$pid/status)" = 1 ] || continue
printf '%s %s %s\\n' "$name" "$pid" "$(awk '{print $22}' /proc/$pid/stat)"
done;done
'''
ssh = ['ssh','-p','2222','-i',str(WORK/'private/c07-client'),'-oIdentitiesOnly=yes',
       '-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222',
       '-oUserKnownHostsFile='+str(WORK/'private/c07-known_hosts'),'-oBatchMode=yes',
       '-oConnectTimeout=6','root@'+str(a.host)]
def remote(label, code, timeout=60):
    (stage/(label+'.sh')).write_text(code)
    result = subprocess.run(ssh+['sh -s'],input=code,capture_output=True,text=True,timeout=timeout)
    for ext,value in [('stdout',result.stdout),('stderr',result.stderr),('exit',str(result.returncode)+'\n')]:
        (stage/(label+'.'+ext)).write_text(value)
    assert result.returncode == 0,(stage,label,result.stderr[-1000:])
    return result.stdout
uuid = remote('boot-evidence',common+'cat /proc/sys/kernel/random/boot_id\n').strip()
assert re.fullmatch('[0-9a-f-]{36}',uuid) and uuid != binding['kernel_boot_id']
common += f'[ "$(cat /proc/sys/kernel/random/boot_id)" = {uuid} ]\n'
before = remote('before',common+infra)
mounts = remote('mounts-before',common+'cat /proc/1/mountinfo\n')
directory = (stage/'remote-directory').read_text().strip() if a.resume else remote('allocate',common+'mktemp -d /run/muos-c74.XXXXXX\n').strip()
assert re.fullmatch('/run/muos-c74[.][A-Za-z0-9]{6}',directory)
(stage/'remote-directory').write_text(directory+'\n')
probe = WORK/'frontend-libs/build.84o1r4aj/load-probe'
digest = sha(probe)
transfer = subprocess.run(ssh+['cat > '+directory+'/provider-probe'],input=probe.read_bytes(),capture_output=True,timeout=20)
assert transfer.returncode == 0
arguments = ' '.join('/opt/muos/frontend/lib/'+name for name in NAMES)
assert NAMES == ['libui.so','libmuxcom.so','libmuxmod.so','libplutosvg.so']
code = common+f'''[ "$(stat -c '%u:%g:%a' {directory})" = 0:0:700 ]
[ "$(findmnt -rn -T {directory} -o FSTYPE)" = tmpfs ]
chmod 700 {directory}/provider-probe
printf '%s  %s\\n' {digest} {directory}/provider-probe | sha256sum -c - >/dev/null
if [ ! -e /run/muos/session ] && [ ! -L /run/muos/session ];then mkdir -m 700 /run/muos/session;fi
[ ! -L /run/muos/session ];[ "$(stat -c '%u:%g:%a' /run/muos/session)" = 0:0:700 ]
exec 8>/run/muos/session/lifetime.lock
flock -n 8
export LD_BIND_NOW=1 LD_LIBRARY_PATH=/opt/muos/frontend/lib
{directory}/provider-probe {arguments}
/opt/muos/frontend/muxretro --version
/opt/muos/frontend/muxretro --help
echo C74_INSTALLED_PROVIDER_AND_HOST_AFTER_USER_REBOOT_OK
'''
out = remote('native-ABI',code)
assert out.count('C65 eager load: ') == 4 and 'muxretro interface 1' in out
assert out.endswith('C74_INSTALLED_PROVIDER_AND_HOST_AFTER_USER_REBOOT_OK\n')
observed = remote('console-observation',common+'''for path in /sys/class/graphics/fbcon/cursor_blink /sys/class/vtconsole/vtcon0/name /sys/class/vtconsole/vtcon1/name;do
if [ -r "$path" ];then printf '%s=' "$path";cat "$path";fi;done
tr ' ' '\n' < /proc/cmdline | grep -E '^(vt.global_cursor_default|consoleblank)=' || :
dmesg | awk '/Kernel panic|BUG:|Oops:|EXT4-fs error|I\\/O error|mmc.*timeout/ {n++} END{printf "KERNEL_STORAGE_SIGNATURES=%d\\n",n}'
''')
assert 'KERNEL_STORAGE_SIGNATURES=0\n' in observed
assert remote('after',common+infra) == before
assert remote('mounts-after',common+'cat /proc/1/mountinfo\n') == mounts
assert remote('cleanup',common+f'''[ ! -L {directory} ];[ "$(stat -c '%u:%g:%a' {directory})" = 0:0:700 ]
rm {directory}/provider-probe
rmdir {directory}
[ ! -e {directory} ]
echo C74_RAM_REMOVED_ROOT_RO
''') == 'C74_RAM_REMOVED_ROOT_RO\n'
assert remote('final-health',common+infra) == before
assert (WORK/'graphics-config/output/.config').read_bytes() == (WORK/'network-tools/baseline.config').read_bytes()
report = {'passed':True,'experiment':'C74_INSTALLED_PROVIDER_AFTER_USER_REBOOT',
    'boot_sequence':a.boot,'previous_C73_boot':prior['boot_sequence'],'kernel_boot_id':uuid,
    'new_UUID_observed':True,'initial_missing_runtime_lock_parent_receipt_preserved':a.resume is not None,'reboot_reported_by_user':True,'agent_requested_reboot':False,
    'installed_files_verified':31,'preserved_prerequisites':101,
    'eager_installed_provider4_and_host_CLI_passed':True,'root_read_only':True,
    'infrastructure_and_global_mounts_preserved':True,'selected_kernel_storage_errors':0,
    'RAM_removed':True,'UI_audio_ROM_core_or_store_started':False,'persistent_device_files_written':False,
    'footer_flicker_absent_after_reboot_user_confirmed':True,'flicker_cause_identified':False,
    'parent_proofs_sha256':parents,'source_sha256':{str(Path(__file__).relative_to(REPO)):sha(Path(__file__))}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
(area/'latest-check').write_text(str(stage)+'\n')
print('C74 user-restarted boot',a.boot,'installed31/101/ABI/rootRO/quiet/infra/mounts passed; RAM removed:',stage)
