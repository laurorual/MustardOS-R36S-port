#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate C76 exact additive policy from C62; never relax the historical scope."""
from pathlib import Path
import re
from phase4_gambatte_install import context, REPO, NATIVE, ROOTS

source,r,added,names,dirs,_,_,_=context()
NATIVE.mkdir(exist_ok=True)
parent=REPO/'dist/phase4/muxretro-installed/source/port/device/rk-r35s-p0/muxretro-install'
old=REPO/'port/device/rk-r35s-p0/muxretro-install'
for name in ['transaction.sh','native.sh']:
    assert (parent/name).read_bytes()==(old/name).read_bytes()
text=(old/'transaction.sh').read_text().replace('c62','c76').replace('C62','C76')
text=re.sub(r"c76_dirs\(\) \{.*?\n\}", "c76_dirs() {\n    printf '%s\\n' "+' '.join(dirs)+"\n}",text,count=1,flags=re.S)
text=re.sub(r"c76_names\(\) \{.*?\n\}", "c76_names() {\n    printf '%s\\n' "+' '.join(names)+"\n}",text,count=1,flags=re.S)
text=text.replace('"$install_payload/FILES")" = 13','"$install_payload/FILES")" = 9')
start=text.index('        if [ "$c76_name" = opt/muos/frontend/muxretro ];then')
end=text.index('        c76_file=$install_payload/new/',start)
text=text[:start]+'        [ "$c76_mode" = 644 ] || return 64\n'+text[end:]
text=text.replace('opt/muos/frontend/muxretro usr/share/muos-muxretro usr/share/licenses/muos-muxretro',' '.join(ROOTS))
text=text.replace('for c76_top in usr/share/muos-muxretro usr/share/licenses/muos-muxretro;', 'for c76_top in '+' '.join(ROOTS)+';')
text=text.replace('# C76 exact C60 additions;', '# C76 exact C75 core additions;')
(NATIVE/'transaction.sh').write_text(text)
text=(old/'native.sh').read_text().replace('c62','c76').replace('C62','C76')
start=text.index('        if [ "$action" = rollback ]; then')
end=text.index('        [ ! -e "$c25_store/c25.once" ]',start)
text=text[:start]+'''        [ "$(cat "$c25_store/boot-seq")" = "$(cat "$install_payload/boot-seq")" ] || return 64
        [ "$(cat /proc/sys/kernel/random/boot_id)" = "$(cat "$install_payload/boot-uuid")" ] || return 64
'''+text[end:]
text=text.replace('# The existing lifetime lock excludes any frontend/runtime writer.', '''# Cold C07 boots need the shared runtime lock directory prepared in RAM.
if [ ! -e /run/muos/session ] && [ ! -L /run/muos/session ];then mkdir -m 700 /run/muos/session || exit 64;fi
[ ! -L /run/muos/session ] && [ "$(stat -c '%u:%g:%a' /run/muos/session)" = 0:0:700 ] || exit 64''')
(NATIVE/'native.sh').write_text(text)
print('C76 additive policy/native adapter rendered; C62 unchanged')
