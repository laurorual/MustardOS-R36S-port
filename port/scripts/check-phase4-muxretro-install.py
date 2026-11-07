#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Exercise C62 exact-scope installation, failure rollback and refusal policy."""
from pathlib import Path
import json,subprocess
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'muxretro-install'
plan_stage=Path((area/'latest-plan').read_text().strip());plan=json.loads((plan_stage/'plan.json').read_text())
for n,h in plan['source_sha256'].items():assert sha(repo/n)==h
stage=plan_stage/'checks';stage.mkdir();rel='/work/'+str(plan_stage.relative_to(work))
script=r'''
set -eu
. /port/device/rk-r35s-p0/muxretro-install/transaction.sh
snapshot() {
 PYTHONPATH=/port/scripts python3 - "$install_root" <<'PY_SNAPSHOT'
import sys,json
sys.dont_write_bytecode=True
from pathlib import Path
from phase4_candidate import inventory
print(json.dumps(inventory(Path(sys.argv[1])),sort_keys=True))
PY_SNAPSHOT
}
reset() {
 rm -rf /tmp/c62-root /tmp/c62-state /tmp/c62-payload
 mkdir -p /tmp/c62-root/opt/muos/frontend /tmp/c62-root/usr/share/licenses /tmp/c62-state
 cp -rP --preserve=mode "$PREPARED/payload" /tmp/c62-payload
 install_root=/tmp/c62-root;install_payload=/tmp/c62-payload;install_state=/tmp/c62-state;install_rw=0
 printf 'synthetic private data must survive\n' > "$install_root/sentinel"
 (cd "$install_root" && sha256sum sentinel) > "$install_payload/foundation.sha256"
 GUARD_FAIL=0;DIR_FAIL=0;STAGE_FAIL=0;FILE_FAIL=0;VERIFY_FAIL=0;RO_FAIL=0;dirs=0;staged=0;files=0;ro_calls=0
 snapshot >/tmp/c62-before
}
install_exec() {
 case "$1" in
 guard) [ "$GUARD_FAIL" = 0 ] ;;
 rw|sync) return 0 ;;
 ro) ro_calls=$((ro_calls+1));[ "$RO_FAIL" != "$ro_calls" ] ;;
 directory-created) dirs=$((dirs+1));[ "$DIR_FAIL" != "$dirs" ] ;;
 file-staged) staged=$((staged+1));[ "$STAGE_FAIL" != "$staged" ] ;;
 file-installed) files=$((files+1));[ "$FILE_FAIL" != "$files" ] ;;
 verify) [ "$VERIFY_FAIL" = 0 ] || return 1
 (cd "$install_root" && sha256sum -c "$install_payload/foundation.sha256") >/dev/null ;;
 *) return 64 ;;
 esac
}
restored() { [ "$install_rw" = 0 ];snapshot >/tmp/c62-after;cmp /tmp/c62-before /tmp/c62-after; }
refuse() { rc=0;c62_preflight || rc=$?;[ "$rc" = 64 ];restored; }
pass() { echo "C62_PASS_$1"; }
reset;GUARD_FAIL=1;refuse;pass guard_before_write
reset;echo bad >> "$install_payload/new/usr/share/muos-muxretro/provenance.json";refuse;pass corrupted_source
reset;chmod 600 "$install_payload/new/usr/share/muos-muxretro/provenance.json";refuse;pass wrong_source_mode
reset;echo 'invalid 644 var/lib/muos-diagnostic/boot-seq' >> "$install_payload/FILES";refuse;pass extra_mutable_path
reset;sed -i 's@usr/share/muos-muxretro/provenance.json@usr/share/muos-muxretro/neighbor.json@' "$install_payload/FILES";refuse;pass neighboring_path
reset;mkdir "$install_root/usr/share/muos-muxretro";snapshot >/tmp/c62-before;refuse;pass existing_directory_preserved
reset;ln -s /tmp "$install_root/usr/share/muos-muxretro";snapshot >/tmp/c62-before;refuse;pass leaf_symlink
reset;mv "$install_root/opt/muos/frontend" "$install_root/opt/muos/original-frontend";ln -s /tmp "$install_root/opt/muos/frontend";snapshot >/tmp/c62-before;refuse;pass parent_symlink
reset;printf bad >> "$install_root/sentinel";snapshot >/tmp/c62-before;refuse;pass foundation_drift
reset;c62_apply;c62_verify;[ "$files" = 13 ];[ "$install_rw" = 0 ];pass complete_apply
install_rw=1;c62_rollback;restored;pass explicit_rollback_to_absence
for pos in $(seq 1 13); do
 reset;DIR_FAIL=$pos
 if c62_apply; then exit 1; fi
 c62_rollback;restored;pass directory_failure_$pos
done
for pos in $(seq 1 13); do
 reset;STAGE_FAIL=$pos
 if c62_apply; then exit 1; fi
 c62_rollback;restored;pass staging_failure_$pos
 reset;FILE_FAIL=$pos
 if c62_apply; then exit 1; fi
 c62_rollback;restored;pass publication_failure_$pos
done
reset;VERIFY_FAIL=1
if c62_apply; then exit 1; fi
VERIFY_FAIL=0;c62_rollback;restored;pass final_verification_failure
reset;RO_FAIL=1
if c62_apply; then exit 1; fi
c62_rollback;restored;pass remount_failure
# A changed published leaf is never removed by recovery.
reset;c62_apply;echo unexpected >> "$install_root/usr/share/muos-muxretro/provenance.json"
snapshot >/tmp/c62-before;install_rw=1
if c62_rollback; then exit 1; fi
snapshot >/tmp/c62-after;cmp /tmp/c62-before /tmp/c62-after;pass rollback_preserves_unexpected_content
# Shared parents and unrelated files survive both success and rollback.
reset;printf neighbor > "$install_root/opt/muos/frontend/sibling"
snapshot >/tmp/c62-before;c62_apply;install_rw=1;c62_rollback;restored;pass shared_parent_and_neighbor_preserved
reset;chmod 777 "$install_root/opt/muos/frontend";snapshot >/tmp/c62-before;refuse;pass wrong_shared_parent_mode
reset;printf collision > "$install_root/opt/muos/frontend/muxretro.c62-new";snapshot >/tmp/c62-before;refuse;pass preexisting_temporary_preserved
reset;c62_apply;printf unknown > "$install_root/usr/share/muos-muxretro/extra"
snapshot >/tmp/c62-before;install_rw=1
if c62_rollback;then exit 1;fi
snapshot >/tmp/c62-after;cmp /tmp/c62-before /tmp/c62-after;pass rollback_preserves_neighbor_inside_new_directory
reset;c62_apply;mkdir "$install_root/usr/share/muos-muxretro/empty-neighbor"
snapshot >/tmp/c62-before;install_rw=1
if c62_rollback;then exit 1;fi
snapshot >/tmp/c62-after;cmp /tmp/c62-before /tmp/c62-after;pass rollback_preserves_unexpected_empty_directory
reset;STAGE_FAIL=1
if c62_apply;then exit 1;fi
printf partial >> "$install_root/opt/muos/frontend/muxretro.c62-new"
snapshot >/tmp/c62-before
if c62_rollback;then exit 1;fi
snapshot >/tmp/c62-after;cmp /tmp/c62-before /tmp/c62-after;pass rollback_preserves_corrupt_temporary
reset;chmod 600 "$install_payload/new/opt/muos/frontend/muxretro";refuse;pass executable_mode_required
# BusyBox preserves dirname('//') == '//'; GNU dirname normalizes it to '/'.
# Exercise the target implementation to prevent an infinite native preflight.
dirname() { qemu-aarch64 -cpu cortex-a35 -L "$SYSROOT" "$SYSROOT/bin/busybox" dirname "$1"; }
install_root=/;c62_parents //opt/muos/frontend/muxretro
pass native_busybox_double_slash_parent_walk
'''
(stage/'fixtures.sh').write_text(script)
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
 '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=128m',
 '-v',f'{work}:/work:ro,z','-v',f'{repo}/port:/port:ro,z','-e','PREPARED='+rel,
 '-e','SYSROOT=/work/save-store-image/image.nlnmgzzb/target',
 (work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',script]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/n).write_text(v)
assert r.returncode==0,(stage,r.stdout[-2000:],r.stderr[-2000:])
cases=[s for s in r.stdout.splitlines() if s.startswith('C62_PASS_')];assert len(cases)==61,len(cases)
sources=[Path(__file__),repo/'port/device/rk-r35s-p0/muxretro-install/transaction.sh',repo/'port/device/rk-r35s-p0/muxretro-install/native.sh']
report={'passed':True,'plan_sha256':sha(plan_stage/'plan.json'),'case_count':len(cases),'cases':cases,'device_written':False,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');print('C62 transaction/rollback fixtures passed:',len(cases),stage)
