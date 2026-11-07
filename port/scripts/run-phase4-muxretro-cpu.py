#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C42 bounded native CPU/loader preflight in RAM; no video/audio session."""
from pathlib import Path
import argparse
import ipaddress
import json
import re
import subprocess
import tempfile
from phase4_candidate import sha

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--host',required=True,type=ipaddress.IPv4Address)
parser.add_argument('--boot',required=True,type=int)
args=parser.parse_args();assert 1<=args.boot<=9999
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'muxretro'
lock_source=repo/'port/device/rk-r35s-p0/muxretro-cpu/session-lock.sh'
audit=Path((area/'latest-audit').read_text().strip());ar=json.loads((audit/'analysis.json').read_text())
assert ar['passed'] and ar['final_ELF_loader_and_early_CLI_passed']
build=Path(ar['build_stage']);br=json.loads((build/'analysis.json').read_text())
assert sha(build/'analysis.json')==ar['build_analysis_sha256']
for report in [ar,br]:
    for name,digest in report['source_sha256'].items():assert sha(repo/name)==digest,name
smoke=Path((work/'libretro-smoke/latest').read_text().strip());sr=json.loads((smoke/'analysis.json').read_text());assert sr['passed']
files={'muxretro':build/'source/bin/muxretro','smoke-check':smoke/'check','r35s_smoke_libretro.so':smoke/'r35s_smoke_libretro.so'}
digests={'muxretro':ar['binary_sha256'],'smoke-check':sr['binary_sha256']['check'],'r35s_smoke_libretro.so':sr['binary_sha256']['r35s_smoke_libretro.so']}
for name,path in files.items():assert sha(path)==digests[name],name
stage=Path(tempfile.mkdtemp(prefix='cpu.',dir=area));(area/'latest-cpu-attempt').write_text(str(stage)+'\n')
ssh=['ssh','-p','2222','-i',str(work/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes',
     '-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(work/'private/c07-known_hosts'),
     '-oBatchMode=yes','-oConnectTimeout=6','root@'+str(args.host)]
def remote(label,code,timeout=35,required=True):
    (stage/(label+'.sh')).write_text(code)
    r=subprocess.run(ssh+['sh -s'],input=code,capture_output=True,text=True,timeout=timeout)
    for ext,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/(label+'.'+ext)).write_text(value)
    if required:assert r.returncode==0,(stage,label,r.stdout,r.stderr)
    return r
common=f'''set -eu
export PATH=/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
umask 077
c25_store=/var/lib/muos-diagnostic; c25_state=/run/muos/c25
. /usr/libexec/muos-c25/policy.sh
. /usr/libexec/muos-c25/card-guard.sh
. /usr/libexec/muos-c25/native.sh
c25_ready
[ "$(cat /var/lib/muos-diagnostic/boot-seq)" = {args.boot} ]
[ ! -e "$c25_store/c25.once" ]; [ ! -L "$c25_store/c25.once" ]
[ "$(cat /proc/asound/card0/pcm0p/sub0/status)" = closed ]
if pidof muxretro smoke-check >/dev/null; then exit 64; fi
'''
infrastructure='''for name in udevd wpa_supplicant udhcpc dropbear; do
for p in $(pidof "$name"); do
[ "$(awk '/^PPid:/ {print $2}' /proc/$p/status)" = 1 ] || continue
printf '%s %s %s\\n' "$name" "$p" "$(awk '{print $22}' /proc/$p/stat)"
done; done
'''
remote('preflight',common+infrastructure)
directory=remote('allocate',common+'mktemp -d /run/muos-muxretro.XXXXXX\n').stdout.strip()
assert re.fullmatch(r'/run/muos-muxretro\.[A-Za-z0-9]{6}',directory)
(stage/'intent.json').write_text(json.dumps({'experiment':'C42_MUXRETRO_NATIVE_CPU','boot_sequence':args.boot,
    'directory':directory,'binary_sha256':digests,'build_analysis_sha256':sha(build/'analysis.json'),
    'early_CLI_only':True,'graphical_session':False,'reboot':False,'rootfs_write':False,
    'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),lock_source]}},indent=2)+'\n')
for name,path in files.items():
    r=subprocess.run(ssh+['cat > '+directory+'/'+name],input=path.read_bytes(),capture_output=True,timeout=30)
    assert r.returncode==0,(name,r.stderr)
code=common+f'''[ -d {directory} ];[ ! -L {directory} ];[ "$(stat -c '%u:%g:%a' {directory})" = 0:0:700 ]
cd {directory}
'''
for name,digest in digests.items():code+=f"printf '%s  %s\\n' {digest} {name} | sha256sum -c -\nchmod 700 {name}\n"
code+=f'''ulimit -c 0
export HOME={directory} LD_BIND_NOW=1 LD_LIBRARY_PATH=/opt/muos/frontend/lib
'''+lock_source.read_text()+'''
bounded=/usr/libexec/muos-run-bounded
"$bounded" 10 ./muxretro --version
"$bounded" 10 ./muxretro --help
rc=0; "$bounded" 10 ./muxretro diagnostic.so --no-content --netplay-host || rc=$?
[ "$rc" = 1 ]
"$bounded" 10 ./smoke-check ./r35s_smoke_libretro.so
echo C42_NATIVE_CPU_EARLY_CLI_AND_CORE_API_OK
'''
result=remote('native',code,timeout=75,required=False)
after=remote('postflight',common+infrastructure)
assert after.stdout==(stage/'preflight.stdout').read_text(),'Infrastructure identity changed'
remote('cleanup',common+f'''cd {directory}
rm muxretro smoke-check r35s_smoke_libretro.so
cd /
rmdir {directory}
c25_ready
echo C42_RAM_REMOVED_ROOT_RO_FOUNDATION97_NETWORK_OK
''')
passed=result.returncode==0 and 'C42_NATIVE_CPU_EARLY_CLI_AND_CORE_API_OK' in result.stdout
output={'passed':passed,'experiment':'C42_MUXRETRO_NATIVE_CPU','boot_sequence':args.boot,
        'native_process_exit':result.returncode,'native_CPU_loader_qualified':passed,
        'graphics_audio_and_input_hardware_qualified':False,'physical_observation_pending':True,
        'root_ro':True,'foundation_hashes':97,'infrastructure_preserved':True,'PCM_closed':True,
        'RAM_removed':True,'reboot_requested':False,'original32_preserved':True,
        'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),lock_source]}}
(stage/'analysis.json').write_text(json.dumps(output,indent=2)+'\n')
assert passed,(stage,result.stdout,result.stderr)
(area/'latest-cpu').write_text(str(stage)+'\n')
print('C42 native CPU/loader/API preflight passed; graphics untested:',stage)
