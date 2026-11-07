#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C43 private storage rehearsal bound to the qualified native CPU baseline."""
from pathlib import Path
import argparse,ipaddress,json,re,subprocess,tempfile
from phase4_candidate import sha,sums
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--host',required=True,type=ipaddress.IPv4Address)
args=parser.parse_args()
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'muxretro'
baseline=repo/'dist/phase4/muxretro-native-cpu'
for name,digest in sums(baseline/'SHA256SUMS').items():assert sha(baseline/name)==digest
br=json.loads((baseline/'analysis.json').read_text());assert br['passed']
boot=br['boot_sequence']
preflight=(baseline/'preflight.sh').read_text()
common,infrastructure=preflight.split('for name in udevd',1);infrastructure='for name in udevd'+infrastructure
source=repo/'port/device/rk-r35s-p0/muxretro-cpu/storage-capsule.sh'
lock=repo/'port/device/rk-r35s-p0/muxretro-cpu/session-lock.sh'
checks=Path((area/'latest-storage-checks').read_text().strip());cr=json.loads((checks/'analysis.json').read_text());assert cr['passed']
for name,digest in cr['source_sha256'].items():assert sha(repo/name)==digest
stage=Path(tempfile.mkdtemp(prefix='storage.',dir=area));(area/'latest-storage-attempt').write_text(str(stage)+'\n')
ssh=['ssh','-p','2222','-i',str(work/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes',
     '-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(work/'private/c07-known_hosts'),
     '-oBatchMode=yes','-oConnectTimeout=6','root@'+str(args.host)]
def remote(label,code,timeout=35,required=True):
    (stage/(label+'.sh')).write_text(code)
    r=subprocess.run(ssh+['sh -s'],input=code,capture_output=True,text=True,timeout=timeout)
    for ext,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/(label+'.'+ext)).write_text(value)
    if required:assert r.returncode==0,(stage,label,r.stdout,r.stderr)
    return r
before=remote('preflight',common+infrastructure).stdout
directory=remote('allocate',common+'mktemp -d /run/muos-prefs-data.XXXXXX\n').stdout.strip()
assert re.fullmatch(r'/run/muos-prefs-data\.[A-Za-z0-9]{6}',directory)
pins={str(p.relative_to(repo)):sha(p) for p in [Path(__file__),source,lock]}
(stage/'intent.json').write_text(json.dumps({'experiment':'C43_RAM_STORAGE','directory':directory,'boot_sequence':boot,
    'baseline_preflight_sha256':sha(baseline/'preflight.sh'),'real_preferences_mount':'ro,noload',
    'game_writers':'RAM/tmpfs','reboot':False,'source_sha256':pins},indent=2)+'\n')
remote('prepare',common+f"cat > {directory}/probe.sh <<'C43_CAPSULE'\n"+source.read_text()+f'''C43_CAPSULE
chmod 600 {directory}/probe.sh
printf '%s  %s\\n' {sha(source)} {directory}/probe.sh | sha256sum -c -
/bin/sh -n {directory}/probe.sh
''')
native=common+lock.read_text()+f'''cat /proc/1/mountinfo > {directory}/global-before.txt
/usr/libexec/muos-run-bounded 60 /usr/libexec/muos-session/mount-namespace /bin/sh {directory}/probe.sh {directory}
cmp /proc/1/mountinfo {directory}/global-before.txt
echo C43_PRIVATE_STORAGE_COMPLETE_GLOBAL_MOUNTS_UNCHANGED
'''
result=remote('native',native,timeout=75,required=False)
after=remote('postflight',common+infrastructure).stdout;assert before==after
cleanup=common+f'''[ -d {directory} ];[ ! -L {directory} ];[ "$(stat -c '%u:%g:%a' {directory})" = 0:0:700 ]
for info in /proc/[0-9]*/mountinfo; do
 [ -r "$info" ] || continue
 if awk -v prefix={directory}/ '$5 ~ "^"prefix {{found=1}} END{{exit !found}}' "$info" 2>/dev/null; then exit 64; fi
done
[ ! -d {directory}/data ] || rmdir {directory}/data
[ ! -L {directory}/ramdata ]
rm -rf {directory}/ramdata
for name in probe.sh storage.conf preferences-before.sha256 preferences-after.sha256 preferences-loaded.txt global-before.txt; do
 [ ! -f {directory}/"$name" ] || rm {directory}/"$name"
done
rmdir {directory}
c25_ready
echo C43_RAM_REMOVED_REAL_DATA_UNMOUNTED_ROOT_RO_FOUNDATION97_NETWORK_OK
'''
remote('cleanup',cleanup)
passed=result.returncode==0 and 'C43_PRIVATE_STORAGE_COMPLETE_GLOBAL_MOUNTS_UNCHANGED' in result.stdout
report={'passed':passed,'experiment':'C43_RAM_STORAGE','boot_sequence':boot,'native_exit':result.returncode,
        'real_preferences_read_only':passed,'preferences_byte_exact_after':passed,'loaded_pair':[55,70] if passed else None,
        'storage_alias_writes_RAM_only':passed,'global_mountinfo_unchanged':passed,'RAM_removed':True,
        'root_ro':True,'foundation_hashes':97,'infrastructure_preserved':True,'native_graphics_tested':False,
        'source_sha256':pins,'host_checks_stage':str(checks),'host_checks_sha256':sha(checks/'analysis.json')}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
assert passed,(stage,result.stdout,result.stderr)
(area/'latest-storage').write_text(str(stage)+'\n');print('C43 native RAM-storage capsule passed:',stage)
