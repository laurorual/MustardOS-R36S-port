#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C24 exact-plan apply/rollback and refusal fixtures using the real transaction."""
from pathlib import Path
import json,subprocess,tempfile
from phase4_candidate import sha

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'rootfs-candidate'
prepared=Path((area/'latest-update').read_text().strip());plan=json.loads((prepared/'plan.json').read_text());candidate=Path(plan['candidate_stage'])
descriptor=json.loads((prepared/'backup-descriptor.json').read_text());backup=Path(descriptor['path']);assert sha(backup)==descriptor['sha256']
stage=Path(tempfile.mkdtemp(prefix='update-checks.',dir=area));rel=lambda p:'/work/'+str(p.relative_to(work))
script=r'''
set -eu
. /port/device/rk-r35s-p0/candidate-update/transaction.sh
reset() {
 rm -rf /tmp/root /tmp/payload
 mkdir /tmp/root
 cp -rP --preserve=mode "$TARGET"/. /tmp/root/
 cp -rP --preserve=mode "$PREPARED/payload" /tmp/payload
 update_root=/tmp/root;update_payload=/tmp/payload;update_rw=0
 while read -r before old after mode name;do [ "$before" != - ] || rm -f "$update_root/$name";done < "$update_payload/FILES"
 awk '{a[NR]=$0} END{for(i=NR;i>0;i--)print a[i]}' "$update_payload/DIRS" >/tmp/dirs
 while read -r mode name;do rmdir "$update_root/$name";done </tmp/dirs
 tar --no-same-owner -xf "$BACKUP" -C "$update_root"
 mkdir -p "$update_root/var/lib/muos-seedrng" "$update_root/var/lib/muos-network"
 printf 'fixture seed, not entropy\n' > "$update_root/var/lib/muos-seedrng/seed"
 printf 'fixture credentials, not an account\n' > "$update_root/var/lib/muos-network/config"
 cp "$update_payload/boot-seq" "$update_root/var/lib/muos-diagnostic/boot-seq";chmod 600 "$update_root/var/lib/muos-diagnostic/boot-seq"
 GUARD_FAIL=0;FAIL_STAGE=0;FAIL_INSTALL=0;staged=0;installed=0;RO_FAIL=0;ro_calls=0;VERIFY_FAIL=0
 snapshot >/tmp/before
}
snapshot() {
 PYTHONPATH=/port/scripts python3 - "$update_root" <<'PY_SNAPSHOT'
import sys,json
sys.dont_write_bytecode=True
from pathlib import Path
from phase4_candidate import inventory
print(json.dumps(inventory(Path(sys.argv[1])),sort_keys=True))
PY_SNAPSHOT
}
update_exec() {
 case "$1" in
 guard) [ "$GUARD_FAIL" = 0 ] ;;
 rw|sync) return 0 ;;
 ro) ro_calls=$((ro_calls+1));[ "$RO_FAIL" != "$ro_calls" ] ;;
 file-staged) staged=$((staged+1));[ "$FAIL_STAGE" != "$staged" ] ;;
 file-installed) installed=$((installed+1));[ "$FAIL_INSTALL" != "$installed" ] ;;
 verify-after)
  [ "$VERIFY_FAIL" = 0 ] || return 1
  . "$update_root/usr/libexec/muos-candidate-boot-checks"
  candidate_boot_check "$update_root" ;;
 verify-before) return 0 ;;
 *) return 1 ;;
 esac
}
refuse() { rc=0;c24_preflight || rc=$?;[ "$rc" = 64 ];[ "$update_rw" = 0 ]; }
restored() { [ "$update_rw" = 0 ];snapshot >/tmp/after;cmp /tmp/before /tmp/after; }
pass() { echo "PASS_$1"; }
reset;GUARD_FAIL=1;refuse;restored;pass media_guard_before_writes
reset;first=$(awk 'NR==1{print $5}' "$update_payload/FILES");printf bad >>"$update_payload/new/$first";refuse;restored;pass bad_payload_before_writes
reset;first=$(awk '$1!="-"{print $5;exit}' "$update_payload/FILES");touch "$update_root/$first.muos-c24-new";snapshot >/tmp/before;refuse;restored;pass stale_sibling_preserved
reset;first=$(awk '$1!="-"{print $5;exit}' "$update_payload/FILES");parent=$(dirname "$update_root/$first");mkdir /tmp/outside;mv "$parent" /tmp/original-general;ln -s /tmp/outside "$parent";snapshot >/tmp/before;refuse;restored;rm -r /tmp/outside /tmp/original-general;pass symlink_parent_refused
reset;c24_backup;c24_apply;[ "$update_rw" = 0 ];[ "$installed" = "$COUNT" ];pass complete_exact_plan_apply
# Recovery can run on a later boot without restoring the old counter/seed.
printf '%s\n' "$NEXT" > "$update_root/var/lib/muos-diagnostic/boot-seq"
update_rw=1;c24_rollback
cp /tmp/before /tmp/old-before
# Compare a fresh before-state with only its counter advanced to46.
snapshot >/tmp/recovered
reset;printf '%s\n' "$NEXT" > "$update_root/var/lib/muos-diagnostic/boot-seq";snapshot >/tmp/expected-recovered
cmp /tmp/recovered /tmp/expected-recovered;pass explicit_recovery_preserves_new_counter_and_private_state
for position in $STAGE_POSITIONS;do
 reset;c24_backup;FAIL_STAGE=$position
 if c24_apply;then exit 1;fi
 [ "$update_rw" = 1 ];c24_rollback;restored;pass staging_failure_$position
 done
for position in $COMMIT_POSITIONS;do
 reset;c24_backup;FAIL_INSTALL=$position
 if c24_apply;then exit 1;fi
 [ "$update_rw" = 1 ];c24_rollback;restored;pass commit_failure_$position
 done
reset;c24_backup;VERIFY_FAIL=1
if c24_apply;then exit 1;fi
c24_rollback;restored;pass final_verification_failure_rolls_back
reset;c24_backup;RO_FAIL=1
if c24_apply;then exit 1;fi
c24_rollback;restored;pass final_remount_failure_rolls_back
# A forbidden mutable path must never be accepted even with a matching digest.
reset;cp "$update_payload/FILES" /tmp/original-FILES
printf '%s\n' '- 0 0000000000000000000000000000000000000000000000000000000000000000 600 var/lib/muos-diagnostic/boot-seq' >> "$update_payload/FILES"
refuse;restored;pass mutable_counter_path_refused
reset
printf '%s\n' '- 0 0000000000000000000000000000000000000000000000000000000000000000 644 opt/muos/device/control/unplanned.conf' >> "$update_payload/FILES"
refuse;restored;pass neighboring_device_control_path_refused
'''
count=len(plan['files'])
args=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=1g','-v',f'{work}:/work:ro,z','-v',f'{repo}/port:/port:ro,z','-e','TARGET='+rel(candidate/'target'),'-e','PREPARED='+rel(prepared),'-e','BACKUP='+rel(backup),'-e','COUNT='+str(count),'-e','PENULTIMATE='+str(count-1),'-e','NEXT='+str(plan['boot_sequence']+1),'-e','STAGE_POSITIONS='+' '.join(map(str,sorted({1,min(15,count),count}))),'-e','COMMIT_POSITIONS='+' '.join(map(str,sorted({1,min(15,count),max(1,count-1),count}))),(work/'rootfs-container.iid').read_text().strip(),'sh','-c',script]
(stage/'fixtures.sh').write_text(script)
with (stage/'stdout').open('w') as out,(stage/'stderr').open('w') as err:
 r=subprocess.run(args,stdout=out,stderr=err,text=True,timeout=240)
stdout=(stage/'stdout').read_text();stderr=(stage/'stderr').read_text()
assert r.returncode==0,(stage,stdout[-2000:],stderr[-2000:])
cases=[s for s in stdout.splitlines() if s.startswith('PASS_')];assert len(cases)==10+len({1,min(15,count),count})+len({1,min(15,count),max(1,count-1),count}),len(cases)
inputs=[Path(__file__),repo/'port/device/rk-r35s-p0/candidate-update/transaction.sh',repo/'port/device/rk-r35s-p0/candidate-update/native.sh']
report={'passed':True,'cases':cases,'plan_sha256':sha(prepared/'plan.json'),'tested_public_files':count,'real_device_written':False,'sources':{str(p.relative_to(repo)):sha(p) for p in inputs}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-update-checks').write_text(str(stage)+'\n')
print('C24 exact-plan transaction/rollback cases passed:',len(cases),stage)
