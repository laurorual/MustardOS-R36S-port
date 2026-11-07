#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C19 host-only build and real-filesystem AArch64 fixtures for the typed store."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'preferences'
area.mkdir(exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area));stage.chmod(0o755)
source=repo/'port/utils/muos-preferences.c';shutil.copyfile(source,stage/source.name)
baseline=work/'network-tools/baseline.config';assert (work/'graphics-config/output/.config').read_bytes()==baseline.read_bytes()
container=(work/'rootfs-container.iid').read_text().strip();rel=lambda p:'/work/'+str(p.relative_to(work))
cc='/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc'
flags='-O2 -g0 -march=armv8-a -mtune=cortex-a35 -std=c11 -Wall -Wextra -Werror -fPIE -pie -Wl,-z,relro,-z,now'
code=f'''set -eu
cd {rel(stage)}
{cc} {flags} muos-preferences.c -o muos-preferences
{cc} {flags} -DPREFS_TEST muos-preferences.c -o muos-preferences-fixture
readelf -h -l -d -n --version-info muos-preferences > elf.txt
'''
r=subprocess.run(['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z',container,'sh','-c',code],capture_output=True,text=True,timeout=30)
(stage/'build.stdout').write_text(r.stdout);(stage/'build.stderr').write_text(r.stderr);assert r.returncode==0,r.stderr
fixture=r'''
set -eu
prefs() { qemu-aarch64 -cpu cortex-a35 -L / /sysroot/lib/ld-linux-aarch64.so.1 --inhibit-cache --library-path /sysroot/lib:/sysroot/usr/lib /payload/muos-preferences --dir "$store" "$@"; }
injected() { qemu-aarch64 -cpu cortex-a35 -L / /sysroot/lib/ld-linux-aarch64.so.1 --inhibit-cache --library-path /sysroot/lib:/sysroot/usr/lib /payload/muos-preferences-fixture --dir "$store" "$@"; }
refuse() { if "$@" >/tmp/refused.stdout 2>/tmp/refused.stderr;then echo unexpected-success >&2;exit 1;fi; }
pass() { echo "PASS $1"; }
reset() {
 rm -rf /tmp/store /tmp/alias /tmp/outside
 mkdir -m 700 /tmp/store
 store=/tmp/store
 printf 'MUOS-R35S-PREFS-V1\n' >"$store/.muos-preferences-v1"
 chmod 600 "$store/.muos-preferences-v1"
 unset PREFS_TEST_FAILURE
}
snapshot() { sha256sum "$store/preferences" | cut -d' ' -f1; }
reset;prefs init >/tmp/default
printf 'MUOS-PREFS-1\nVOLUME=100\nBRIGHTNESS=80\n' >/tmp/expected
cmp /tmp/default /tmp/expected;pass first-use-defaults
prefs save 60 75 >/tmp/saved;prefs init >/tmp/again;cmp /tmp/saved /tmp/again
prefs load >/tmp/loaded;cmp /tmp/saved /tmp/loaded;pass saved-pair-survives-new-process-and-init
ino=$(stat -c %i "$store/preferences");prefs save 60 75 >/dev/null
[ "$(stat -c %i "$store/preferences")" = "$ino" ];pass unchanged-save-no-rewrite
before=$(snapshot)
for args in '101 80' '60 161' '60 39' '-1 80' '060 80' '60 080' '60 x';do refuse prefs save $args;done
[ "$(snapshot)" = "$before" ];pass ranges-and-canonical-numbers-no-change
printf 'MUOS-PREFS-2\nVOLUME=60\nBRIGHTNESS=75\n' >"$store/preferences"
before=$(snapshot);refuse prefs init;refuse prefs save 10 80
[ "$(snapshot)" = "$before" ];pass unknown-schema-not-overwritten
reset;prefs init >/dev/null;cp "$store/preferences" /tmp/outside;rm "$store/preferences"
ln -s /tmp/outside "$store/preferences";refuse prefs save 60 75
cmp /tmp/outside /tmp/expected;pass symlink-preference-refused
reset;prefs init >/dev/null;ln "$store/preferences" /tmp/outside;refuse prefs save 60 75
cmp "$store/preferences" /tmp/outside;pass hardlink-preference-refused
reset;prefs init >/dev/null;ln -s "$store" /tmp/alias;store=/tmp/alias
refuse prefs save 60 75;pass symlink-ancestor-refused
reset;prefs init >/dev/null;before=$(snapshot)
ln -s /tmp/outside "$store/.preferences.new";refuse prefs save 60 75
[ "$(snapshot)" = "$before" ] && [ ! -e /tmp/outside ];pass stale-staging-symlink-preserved
reset;printf WRONG >"$store/.muos-preferences-v1"
refuse prefs init;[ ! -e "$store/.lock" ];pass marker-before-any-write
reset;chmod 777 "$store";refuse prefs init
[ ! -e "$store/.lock" ];pass directory-permissions-before-write
reset;prefs init >/dev/null
exec 9>"$store/.lock";flock -n 9
set +e;prefs save 60 75 >/dev/null;rc=$?;set -e
[ "$rc" = 75 ];exec 9>&-;pass busy-lock-nonblocking
reset;prefs init >/dev/null;before=$(snapshot)
export PREFS_TEST_FAILURE=file-sync
set +e;injected save 60 75 >/dev/null;rc=$?;set -e
[ "$rc" = 74 ] && [ "$(snapshot)" = "$before" ] && [ ! -e "$store/.preferences.new" ]
pass failure-before-rename-preserves-old
export PREFS_TEST_FAILURE=directory-sync
set +e;injected save 60 75 >/dev/null;rc=$?;set -e
[ "$rc" = 74 ]
unset PREFS_TEST_FAILURE
prefs load >/tmp/new;grep -qx VOLUME=60 /tmp/new;grep -qx BRIGHTNESS=75 /tmp/new
pass post-rename-sync-failure-reported-no-false-rollback
reset;rm "$store/.muos-preferences-v1";refuse prefs init
[ ! -e "$store/.lock" ];pass missing-marker-no-self-authorisation
reset;prefs init >/dev/null;printf 'MUOS-PREFS-1\nVOLUME=60\nBRIGHTNESS=75\nready=1\n' >"$store/preferences"
before=$(snapshot);refuse prefs init
[ "$(snapshot)" = "$before" ];pass runtime-flags-and-extra-fields-rejected
'''
(stage/'fixture.sh').write_text(fixture)
root=work/'linux-diagnostic/network-recovery.zz7sq2ve/extracted'
args=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--user=0','--tmpfs','/tmp:rw,nosuid,nodev',
      '-v',f'{stage}:/payload:ro,z','-v',f'{root}:/sysroot:ro,z',container,'sh','/payload/fixture.sh']
r=subprocess.run(args,capture_output=True,text=True,timeout=45)
(stage/'stdout').write_text(r.stdout);(stage/'stderr').write_text(r.stderr)
assert r.returncode==0,(stage,r.stdout,r.stderr)
cases=[line[5:] for line in r.stdout.splitlines() if line.startswith('PASS ')];assert len(cases)==16,cases
elf=(stage/'elf.txt').read_text();assert 'AArch64' in elf and '/lib/ld-linux-aarch64.so.1' in elf and 'ABI: 4.4.0' in elf
assert (work/'graphics-config/output/.config').read_bytes()==baseline.read_bytes()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
meta={'host_passed':True,'cases':cases,'case_count':16,'AArch64_on_real_tmpfs_via_QEMU':True,
      'target_device_modified':False,'block_devices_or_partitions_touched':False,
      'native_data_mount_or_power_loss_durability_tested':False,'runtime_integration_enabled':False,
      'SDK_config_unchanged':True,'flags':flags,'production_binary_sha256':sha(stage/'muos-preferences'),
      'test_binary_must_never_be_deployed':True,
      'sources':{str(p.relative_to(repo)):sha(p) for p in [source,Path(__file__)]}}
(stage/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n');(area/'latest-checks').write_text(str(stage)+'\n')
print('C19 preferences store:',len(cases),'AArch64 filesystem cases passed;',stage)
