#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Whitelist-only C10 session collection and idle health; no private network data."""
from pathlib import Path
import io,json,re,shlex,subprocess,sys,tarfile
repo=Path(__file__).resolve().parents[2];stage=Path(sys.argv[1]).resolve();assert stage.is_relative_to(repo/'build/phase4/runtime-profile')
remote=(stage/'remote-directory').read_text().strip();assert re.fullmatch(r'/run/muos-c10\.[A-Za-z0-9]{6}',remote)
ssh=['ssh','-p','2222','-i',str(repo/'build/phase4/private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes','-oUserKnownHostsFile='+str(repo/'build/phase4/private/c07-known_hosts'),'-oBatchMode=yes','root@192.168.15.17']
names=['report.txt','result','network-before.txt','network-after.txt','services.log','frontend.log','cleanup.log','persistent-restore.txt','cache-restored.txt','audio-cleanup.txt','drm-before.txt','drm-after.txt','alsa-before.txt','alsa-restored.txt','remount.txt','root-writers.txt','ui-during.txt','ui-before-stop.txt','sdl-audio-env.txt','helpers.txt','controls-events.txt','controls-before.sha256','controls-restored.txt','controls-cache.txt','brightness-before.txt','brightness-after.txt','volume-store-before.sha256','volume-store-after.sha256','profile-effective.txt','profile-static.txt','profile-runtime.txt','profile-defaults-restored.txt']
code='''set -eu
[ "$(uname -r)" = 4.4.189-muos-r35s-p4 ]
[ "$(cat /etc/muos-network-diagnostic)" = MUOS-R35S-NETWORK-P4-C07 ]
'''+f'test -f {remote}/state/done\ncd {remote}/state\n'+'set --\nfor name in '+' '.join(shlex.quote(n) for n in names)+'''; do
 [ -f "$name" ] || continue
 [ "$(stat -c %s "$name")" -le 524288 ]
 set -- "$@" "$name"
done
tar -cf - "$@"
'''
r=subprocess.run(ssh+['sh -s'],input=code.encode(),capture_output=True,timeout=25);(stage/'collection.tar').write_bytes(r.stdout);(stage/'collection.stderr').write_bytes(r.stderr);assert r.returncode==0,r.stderr
native=stage/'native';native.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(r.stdout)) as t:
 for member in t.getmembers():
  assert member.isfile() and member.name in names and member.size<=524288
  (native/member.name).write_bytes(t.extractfile(member).read())
health=r'''set -eu
/usr/libexec/muos-c07-network status
echo C07_NETWORK_OK
findmnt -rn -o OPTIONS / | tr ',' '\n' | grep -qx ro
echo ROOT_RO=1
! mountpoint -q /boot
printf 'TAINT='; cat /proc/sys/kernel/tainted
for n in muxfrontend muhotkey muinput pipewire wireplumber dbus-daemon mulog; do ! pidof "$n" >/dev/null; done
echo NO_C09_PROCESSES
[ ! -S /run/dbus/system_bus_socket ]; echo NO_DBUS_SOCKET
[ -f /run/muos/entropy/stopped ] && [ ! -f /run/muos/entropy/ready ]; echo C07_RNG_STOPPED_UNCHANGED
dmesg | awk '/Kernel panic|BUG:|Oops:|EXT4-fs error|I\/O error|mmc.*timeout/ {n++} END{printf "KERNEL_ERROR_SIGNATURES=%d\n",n}'
'''
r=subprocess.run(ssh+['sh -s'],input=health,capture_output=True,text=True);(native/'final-health.txt').write_text(r.stdout);(stage/'health.stderr').write_text(r.stderr);assert r.returncode==0,(r.stdout,r.stderr)
r=subprocess.run(ssh+['sha256sum -c '+remote+'/prerequisites.sha256'],capture_output=True,text=True);(native/'prerequisites-after.txt').write_text(r.stdout);(stage/'prerequisites-after.stderr').write_text(r.stderr);assert r.returncode==0
print('C10 public session collected; native result='+ (native/'result').read_text().strip()+', idle health and original public hashes passed:',stage)
