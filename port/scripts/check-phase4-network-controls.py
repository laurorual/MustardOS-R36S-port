#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Exercise C09 helper readbacks, monitor stop and restoration without hardware."""
from pathlib import Path
import json,subprocess,tempfile
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
stage=Path(tempfile.mkdtemp(prefix='controls-hooks.',dir=work/'network-tools'))
s=(repo/'port/device/rk-r35s-p0/network-controls-diagnostic/extension.sh').read_text()
s=s.replace('/sys/class/backlight/backlight','/tmp/hardware').replace('/opt/muos/share/volume','/tmp/volume').replace('/opt/muos/config','/tmp/config').replace('/opt/muos/share/hotkey','/tmp/hotkey').replace('/opt/muos/frontend/muvarctl','/tmp/bin/muvarctl').replace('/opt/muos/script/device/audio.sh','/tmp/bin/audio').replace('/opt/muos/script/device/bright.sh','/tmp/bin/bright').replace('/usr/libexec/muos-run-bounded','/tmp/bin/bounded')
(stage/'fixture-extension.sh').write_text(s)
script=r'''
set -eu
export PATH=/tmp/bin:/usr/sbin:/usr/bin:/sbin:/bin
mkdir -p /tmp/bin /tmp/hardware /tmp/volume /tmp/hotkey /tmp/config/settings/general /tmp/config/settings/advanced
cat > /tmp/bin/muvarctl <<'EOF'
#!/bin/sh
case "$3" in
 settings/general/volume) cat /tmp/config/settings/general/volume ;;
 settings/general/brightness) cat /tmp/config/settings/general/brightness ;;
 *) exit 1 ;;
esac
EOF
cat > /tmp/bin/audio <<'EOF'
#!/bin/sh
v=$(cat /tmp/config/settings/general/volume)
n=5; [ "${MOCK_DOUBLE:-0}" = 0 ] || n=10
case "$1" in D) v=$((v-n)) ;; U) v=$((v+n)) ;; *) exit 1 ;; esac
printf '%s\n' "$v" > /tmp/config/settings/general/volume
EOF
cat > /tmp/bin/bright <<'EOF'
#!/bin/sh
v=$(cat /tmp/hardware/brightness)
n=5; [ "${MOCK_BRIGHT_DOUBLE:-0}" = 0 ] || n=10
case "$1" in D) v=$((v-n)) ;; U) v=$((v+n)) ;; *) exit 1 ;; esac
printf '%s\n' "$v" > /tmp/hardware/brightness
EOF
cat > /tmp/bin/wpctl <<'EOF'
#!/bin/sh
v=$(cat /tmp/config/settings/general/volume)
awk -v v="$v" 'BEGIN{printf "Volume: %.2f\n",v/100}'
EOF
printf '#!/bin/sh\nshift\nexec "$@"\n' > /tmp/bin/bounded
printf '#!/bin/sh\necho mount >> /tmp/mounts\n' > /tmp/bin/mount
printf '#!/bin/sh\necho umount >> /tmp/mounts\n' > /tmp/bin/umount
chmod 755 /tmp/bin/*
. /fixture/fixture-extension.sh
new_case() {
 state=/tmp/state-$1;mkdir "$state"
 c09_brightness_saved=0; c09_volume_bound=0; c09_monitor=
 c09_brightness=/tmp/hardware/brightness; c09_max=160;c09_original=80
 printf '80\n' > /tmp/hardware/brightness
 printf '160\n' > /tmp/hardware/max_brightness
 printf '80\n' > /tmp/config/settings/general/brightness
 printf '100\n' > /tmp/config/settings/general/volume
 for n in incbright incvolume overdrive; do printf '5\n' > /tmp/config/settings/advanced/$n; done
 printf '{}\n' > /tmp/hotkey/r35s-bringup.json
 printf '35\n' > /tmp/volume/fixture
 rm -f /tmp/orig-called
 : > /tmp/mounts
}
c09_orig_frontend() { touch /tmp/orig-called; }
c09_orig_before_core() { touch /tmp/orig-called; return 1; }
new_case success
c06_frontend
c09_stop_monitor
[ -z "$c09_monitor" ] && [ -e /tmp/orig-called ]
grep -q HELPER_VOLUME_DOWN=95 "$state/helpers.txt"
grep -q HELPER_BRIGHT_DOWN=75 "$state/helpers.txt"
[ "$(cat /tmp/hardware/brightness)" = 80 ]
new_case double-volume
if MOCK_DOUBLE=1 c06_frontend; then exit 1; fi
[ ! -e /tmp/orig-called ] && [ -z "$c09_monitor" ]
new_case double-brightness
if MOCK_BRIGHT_DOUBLE=1 c06_frontend; then exit 1; fi
[ ! -e /tmp/orig-called ] && [ -z "$c09_monitor" ]
new_case restore
printf '80\n' > "$state/brightness-before.txt"
c09_brightness_saved=1; c09_volume_bound=1
c09_volume_manifest > "$state/volume-store-before.sha256"
sha256sum /tmp/config/settings/general/brightness > "$state/controls-before.sha256"
printf '75\n' > /tmp/hardware/brightness
c09_restore
[ "$(cat /tmp/hardware/brightness)" = 80 ]
[ "$(cat /tmp/mounts)" = umount ]
new_case bad-maximum
printf '80\n' > "$state/brightness-before.txt";c09_brightness_saved=1
printf '159\n' > /tmp/hardware/max_brightness
printf '75\n' > /tmp/hardware/brightness
if c09_restore; then exit 1; fi
[ "$(cat /tmp/hardware/brightness)" = 75 ]
new_case config-changed
printf '80\n' > "$state/brightness-before.txt";c09_brightness_saved=1
sha256sum /tmp/config/settings/general/brightness > "$state/controls-before.sha256"
printf '70\n' > /tmp/config/settings/general/brightness
if c09_restore; then exit 1; fi
for value in 0 20 170; do
 new_case guard-$value
 printf '%s\n' "$value" > /tmp/hardware/brightness
 if c06_before_core; then exit 1; fi
 [ ! -e /tmp/orig-called ] && [ ! -s /tmp/mounts ]
done
printf 'PASS helper readbacks/double-step refusal/monitor stop/restore/hardware limits/config hashes\n'
'''
args=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{stage}:/fixture:ro,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-c',script]
r=subprocess.run(args,capture_output=True,text=True,timeout=35);(stage/'stdout.txt').write_text(r.stdout);(stage/'stderr.txt').write_text(r.stderr)
record={'passed':r.returncode==0,'exit':r.returncode,'hardware_tested':False,'cases':['helper95/100 and75/80 readbacks plus monitor stop','double volume step refuses UI','double brightness step refuses UI','brightness/hash/volume directory restore','unexpected hardware max refuses write','changed persistent config detected','brightness0 refused before writes','brightness20 refused before writes','brightness170 refused before writes']}
(stage/'report.json').write_text(json.dumps(record,indent=2)+'\n');assert r.returncode==0,(stage,r.stderr)
(work/'network-tools/latest-controls-hooks').write_text(str(stage)+'\n');print('C09 controls fixtures passed:',stage)
