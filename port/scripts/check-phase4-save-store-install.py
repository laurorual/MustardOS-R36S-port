#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Exercise C57 exact-scope installation, failure rollback and refusal policy."""
from pathlib import Path
import json,subprocess
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'save-store-install'
plan_stage=Path((area/'latest-plan').read_text().strip());plan=json.loads((plan_stage/'plan.json').read_text())
for n,h in plan['source_sha256'].items():assert sha(repo/n)==h
stage=plan_stage/'checks';stage.mkdir();rel='/work/'+str(plan_stage.relative_to(work))
script=r'''
set -eu
. /port/device/rk-r35s-p0/save-store-install/transaction.sh
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
 rm -rf /tmp/c57-root /tmp/c57-state /tmp/c57-payload
 mkdir -p /tmp/c57-root/usr/libexec /tmp/c57-root/usr/share/licenses /tmp/c57-state
 cp -rP --preserve=mode "$PREPARED/payload" /tmp/c57-payload
 install_root=/tmp/c57-root;install_payload=/tmp/c57-payload;install_state=/tmp/c57-state;install_rw=0
 printf 'synthetic private data must survive\n' > "$install_root/sentinel"
 (cd "$install_root" && sha256sum sentinel) > "$install_payload/foundation.sha256"
 GUARD_FAIL=0;DIR_FAIL=0;STAGE_FAIL=0;FILE_FAIL=0;VERIFY_FAIL=0;RO_FAIL=0;dirs=0;staged=0;files=0;ro_calls=0
 snapshot >/tmp/c57-before
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
restored() { [ "$install_rw" = 0 ];snapshot >/tmp/c57-after;cmp /tmp/c57-before /tmp/c57-after; }
refuse() { rc=0;c57_preflight || rc=$?;[ "$rc" = 64 ];restored; }
pass() { echo "C57_PASS_$1"; }
reset;GUARD_FAIL=1;refuse;pass guard_before_write
reset;echo bad >> "$install_payload/new/usr/share/muos-save-store/contract.json";refuse;pass corrupted_source
reset;chmod 600 "$install_payload/new/usr/share/muos-save-store/contract.json";refuse;pass wrong_source_mode
reset;echo 'invalid 644 var/lib/muos-diagnostic/boot-seq' >> "$install_payload/FILES";refuse;pass extra_mutable_path
reset;sed -i 's@usr/share/muos-save-store/contract.json@usr/share/muos-save-store/neighbor.json@' "$install_payload/FILES";refuse;pass neighboring_path
reset;mkdir "$install_root/usr/libexec/muos-save-store";snapshot >/tmp/c57-before;refuse;pass existing_directory_preserved
reset;ln -s /tmp "$install_root/usr/libexec/muos-save-store";snapshot >/tmp/c57-before;refuse;pass leaf_symlink
reset;mv "$install_root/usr/libexec" "$install_root/usr/original-libexec";ln -s /tmp "$install_root/usr/libexec";snapshot >/tmp/c57-before;refuse;pass parent_symlink
reset;printf bad >> "$install_root/sentinel";snapshot >/tmp/c57-before;refuse;pass foundation_drift
reset;c57_apply;c57_verify;[ "$files" = 4 ];[ "$install_rw" = 0 ];pass complete_apply
install_rw=1;c57_rollback;restored;pass explicit_rollback_to_absence
for pos in 1 2 3; do
 reset;DIR_FAIL=$pos
 if c57_apply; then exit 1; fi
 c57_rollback;restored;pass directory_failure_$pos
done
for pos in 1 2 3 4; do
 reset;STAGE_FAIL=$pos
 if c57_apply; then exit 1; fi
 c57_rollback;restored;pass staging_failure_$pos
 reset;FILE_FAIL=$pos
 if c57_apply; then exit 1; fi
 c57_rollback;restored;pass publication_failure_$pos
done
reset;VERIFY_FAIL=1
if c57_apply; then exit 1; fi
VERIFY_FAIL=0;c57_rollback;restored;pass final_verification_failure
reset;RO_FAIL=1
if c57_apply; then exit 1; fi
c57_rollback;restored;pass remount_failure
# A changed published leaf is never removed by recovery.
reset;c57_apply;echo unexpected >> "$install_root/usr/share/muos-save-store/contract.json"
snapshot >/tmp/c57-before;install_rw=1
if c57_rollback; then exit 1; fi
snapshot >/tmp/c57-after;cmp /tmp/c57-before /tmp/c57-after;pass rollback_preserves_unexpected_content
# BusyBox preserves dirname('//') == '//'; GNU dirname normalizes it to '/'.
# Exercise the target implementation to prevent an infinite native preflight.
dirname() { qemu-aarch64 -cpu cortex-a35 -L "$SYSROOT" "$SYSROOT/bin/busybox" dirname "$1"; }
install_root=/;c57_parents //usr/libexec/muos-save-store/muos-save-store
pass native_busybox_double_slash_parent_walk
'''
(stage/'fixtures.sh').write_text(script)
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
 '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=128m',
 '-v',f'{work}:/work:ro,z','-v',f'{repo}/port:/port:ro,z','-e','PREPARED='+rel,
 '-e','SYSROOT=/work/save-store-image/image.nlnmgzzb/target',
 (work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',script]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/n).write_text(v)
assert r.returncode==0,(stage,r.stdout[-2000:],r.stderr[-2000:])
cases=[s for s in r.stdout.splitlines() if s.startswith('C57_PASS_')];assert len(cases)==26,len(cases)
sources=[Path(__file__),repo/'port/device/rk-r35s-p0/save-store-install/transaction.sh',repo/'port/device/rk-r35s-p0/save-store-install/native.sh']
report={'passed':True,'plan_sha256':sha(plan_stage/'plan.json'),'case_count':len(cases),'cases':cases,'device_written':False,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');print('C57 transaction/rollback fixtures passed:',len(cases),stage)
