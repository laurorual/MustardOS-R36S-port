#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Render C66 guards as exact deltas of the immutable C63 scripts."""
from phase4_frontend_libs_session import historical, NATIVE, REPO, NAMES
from phase4_candidate import sha

context, _, _, _, provider, _ = historical()
NATIVE.mkdir(exist_ok=True)
parent = REPO / 'port/device/rk-r35s-p0/installed-host-session'
app = (parent / 'app-launch.sh').read_text()
anchor = 'exec /bin/sh "$capsule/installed-host.sh" "$capsule" launch'
assert app.count(anchor) == 1
(NATIVE / 'app-launch.sh').write_text(app.replace(anchor,
    'export LD_BIND_NOW=1 LD_LIBRARY_PATH="$capsule/provider-lib:/opt/muos/frontend/lib"\n' + anchor))
guard = (parent / 'installed-host.sh').read_text()
anchor = '[ "$operation" = check ] || [ "$(findmnt -rn -M /mnt/mmc -o FSTYPE)" = tmpfs ]'
assert guard.count(anchor) == 1
(NATIVE / 'installed-host.sh').write_text(guard.replace(anchor,
    '/bin/sh "$capsule/frontend-libs.sh" "$capsule" "$operation"\n' + anchor))
screen = (parent / 'stopped-screen.sh').read_text()
(NATIVE / 'stopped-screen.sh').write_text(screen.replace('C63', 'C66'))
rows = [(provider['libraries'][n]['sha256'], 'provider-lib/' + n) for n in NAMES]
rows += [(provider['libraries'][n]['sha256'], 'lib/' + n) for n in NAMES if n != 'libmuxmod.so']
text = '''#!/bin/sh
# SPDX-License-Identifier: MIT
# C66 fixed RAM provider; diagnostic C46 libmuxmod remains a menu override.
set -eu
export PATH=/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
capsule=${1:-};operation=${2:-}
case "$capsule" in /run/muos-prefs-data.??????) ;; *) exit 64;; esac
case "$operation:$#" in check:2|launch:2) ;; *) exit 64;; esac
[ "$(id -u)" = 0 ]
[ "$(findmnt -rn -T "$capsule" -o FSTYPE)" = tmpfs ]
for path in "$capsule" "$capsule/lib" "$capsule/provider-lib"; do
 [ -d "$path" ] && [ ! -L "$path" ]
 [ "$(stat -c '%u:%g:%a' "$path")" = 0:0:700 ]
done
while read -r digest name; do
 file=$capsule/$name
 [ -f "$file" ] && [ ! -L "$file" ]
 [ "$(stat -c '%u:%g:%a:%h' "$file")" = 0:0:700:1 ]
 [ "$(sha256sum "$file" | cut -d' ' -f1)" = "$digest" ]
done <<'C66_PROVIDER'
'''
text += ''.join(h + ' ' + n + '\n' for h, n in rows) + '''C66_PROVIDER
if [ "$operation" = launch ]; then
 [ "${LD_BIND_NOW:-}" = 1 ]
 [ "${LD_LIBRARY_PATH:-}" = "$capsule/provider-lib:/opt/muos/frontend/lib" ]
fi
printf 'C66_PROVIDER_VALID files=7 operation=%s\\n' "$operation"
'''
(NATIVE / 'frontend-libs.sh').write_text(text)
print('C66 guarded provider files rendered; historical guards unchanged')
