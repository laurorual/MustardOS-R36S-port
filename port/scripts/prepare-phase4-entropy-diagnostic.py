#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C02: native SeedRNG policy/readiness payload; no seed material in artifacts."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,tempfile

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
base=work/'linux-diagnostic/services.kd5t73ez';base_meta=json.loads((base/'manifest.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(base/'rootfs.ext4')==base_meta['rootfs_sha256']
assert not (base/'extracted/var/lib/muos-seedrng').exists()
stage=Path(tempfile.mkdtemp(prefix='entropy.',dir=work/'linux-diagnostic'));assets=stage/'assets';assets.mkdir()
shutil.copyfile(base/'rootfs.ext4',stage/'rootfs.ext4')
bootstrap=(repo/'port/device/rk-r35s-p0/service-diagnostic/bootstrap').read_text().replace('C01','C02')
chain=(repo/'port/device/rk-r35s-p0/service-diagnostic/chain.sh').read_text().replace('for service in S10udev','for service in S05muos-entropy S10udev')
run=(repo/'port/device/rk-r35s-p0/service-diagnostic/run').read_text().replace('C01','C02').replace('/run/muos/c01','/run/muos/c02').replace('DIAG03','DIAG04')
old='c01_exec() { /usr/libexec/muos-run-bounded 45 "$@"; }'
assert old in run
run=run.replace(old,'''c01_exec() {
    case "$1" in */S05muos-entropy) seconds=90 ;; *) seconds=45 ;; esac
    /usr/libexec/muos-run-bounded "$seconds" "$@"
}''')
run=run.replace('Checking coldplug, D-Bus and normalized input...','Waiting for RNG, then checking services/input...')
run=run.replace("    echo 'MAPPING'; cat",'''    echo 'ENTROPY START'
    for file in mode before.txt after.txt start.log start-metadata.txt; do
        echo "$file"; cat "/run/muos/entropy/$file" 2>/dev/null
    done
    echo 'MAPPING'; cat''')
run=run.replace("    echo 'FINAL STATUS';",'''    echo 'ENTROPY STOP'
    for file in stop-ready.txt stop.log stop-metadata.txt; do
        echo "$file"; cat "/run/muos/entropy/$file" 2>/dev/null
    done
    echo 'FINAL STATUS';''')
run=run.replace('C02: BUSYBOX_INIT / COLDPLUG / INPUT OK','C02: RNG_READY / INPUT OK / SEED SAVED')
run=run.replace('status=0\nc01_start_chain', '''# Public monotonic diagnostic sequence; contains no RNG or private seed data.
sequence_dir=/var/lib/muos-diagnostic
[ ! -L "$sequence_dir" ] || fail 'Sequence directory is a symlink'
mkdir -p -m 700 "$sequence_dir" || fail 'Cannot create sequence directory'
[ "$(stat -c '%u:%g:%a' "$sequence_dir")" = 0:0:700 ] || fail 'Sequence permissions'
sequence=0
if [ -e "$sequence_dir/boot-seq" ]; then
    [ -f "$sequence_dir/boot-seq" ] && [ ! -L "$sequence_dir/boot-seq" ] || fail 'Invalid sequence file'
    sequence=$(cat "$sequence_dir/boot-seq")
fi
case "$sequence" in ''|*[!0-9]*|?????*) fail 'Invalid sequence value' ;; esac
[ "$sequence" -lt 9999 ] || fail 'Sequence exhausted'
sequence=$((sequence + 1))
printf '%s\\n' "$sequence" > "$sequence_dir/boot-seq.tmp" || fail 'Cannot save sequence'
mv "$sequence_dir/boot-seq.tmp" "$sequence_dir/boot-seq" || fail 'Cannot commit sequence'
sync
archive=$(printf 'BOOT%04d' "$sequence")
status=0
c01_start_chain''')
run=run.replace("echo 'MUOS-R35S-INIT-P4-C02'; uname -a", "echo 'MUOS-R35S-INIT-P4-C02'; uname -a; echo 'POLICY_REVISION'; echo 1; echo 'BOOT_SEQ'; echo \"$sequence\"")
old_save='''cp "$state/report.txt" /boot/DIAG04/REPORT.TXT || fail 'Cannot save report'
cp "$state/dmesg.txt" /boot/DIAG04/DMESG.TXT || fail 'Cannot save kernel log'
printf 'C02_DIAGNOSTIC_STATUS=%s\\n' "$status" > /boot/DIAG04/RESULT.TXT'''
assert old_save in run
run=run.replace(old_save, '''mkdir "/boot/DIAG04/$archive" || fail 'Archive exists or cannot be created'
for destination in "/boot/DIAG04/$archive" /boot/DIAG04; do
    cp "$state/report.txt" "$destination/REPORT.TXT" || fail 'Cannot save report'
    cp "$state/dmesg.txt" "$destination/DMESG.TXT" || fail 'Cannot save kernel log'
    printf 'C02_DIAGNOSTIC_STATUS=%s\\n' "$status" > "$destination/RESULT.TXT" || fail 'Cannot save status'
done''')
payload={
 'sbin/muos-ext4-diag':bootstrap,
 'usr/libexec/muos-c01-chain':chain,
 'usr/libexec/muos-c01-run':run,
 'usr/libexec/muos-entropy-functions':(repo/'port/device/rk-r35s-p0/entropy-diagnostic/functions.sh').read_text(),
 'etc/init.d/S05muos-entropy':(repo/'port/device/rk-r35s-p0/S05muos-entropy').read_text(),
 'etc/default/seedrng':'SEEDRNG_ARGS="-d /var/lib/muos-seedrng"\n',
 'etc/muos-services-diagnostic':'MUOS-R35S-INIT-P4-C02\n'}
for name,data in payload.items():(assets/name.replace('/','_')).write_text(data)
image=(work/'rootfs-container.iid').read_text().strip()
container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev',
 '-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z','-e','STAGE_REL='+str(stage.relative_to(work)),image,'sh','-eu','-c']
compile=r'''
stage=/work/$STAGE_REL
cc=/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc
"$cc" -std=c11 -O2 -Wall -Wextra -march=armv8-a -mtune=cortex-a35 -fPIE -pie -Wl,-z,relro,-z,now /port/utils/muos-rng-ready.c -o "$stage/assets/usr_libexec_muos-rng-ready"
gcc -std=c11 -O2 -Wall -Wextra /port/probes/rng-ready-fixture.c -o "$stage/rng-ready-fixture"
readelf -h -l -d "$stage/assets/usr_libexec_muos-rng-ready" > "$stage/rng-ready-elf.txt"
'''
with (stage/'compile.log').open('w') as f:subprocess.run(container+[compile],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=30)
# Activation differs from C01: install the fail-closed C02 bootstrap FIRST,
# and its marker LAST. A partial update cannot run altered C01 helpers.
targets=['sbin/muos-ext4-diag','usr/libexec/muos-rng-ready','usr/libexec/muos-entropy-functions',
         'etc/init.d/S05muos-entropy','etc/default/seedrng','usr/libexec/muos-c01-chain',
         'usr/libexec/muos-c01-run','etc/muos-services-diagnostic']
entries=[];commands=[]
for target in targets:
    source=assets/target.replace('/','_');old_path=base/'extracted'/target
    mode=0o755 if target.startswith(('sbin/','usr/libexec/','etc/init.d/')) else 0o644
    entries.append({'path':target,'asset':source.name,'sha256':sha(source),'mode':mode,'old_sha256':sha(old_path) if old_path.is_file() else None})
    if old_path.exists():commands.append('rm /'+target)
    commands += [f'write assets/{source.name} /{target}',f'set_inode_field /{target} mode 0{mode|0o100000:o}']
(stage/'debugfs.commands').write_text('\n'.join(commands)+'\n')
audit=r'''
cd /work/$STAGE_REL
debugfs -w -f debugfs.commands rootfs.ext4 > debugfs.log 2>&1
e2fsck -fn rootfs.ext4 > fsck.log 2>&1
mkdir extracted
/work/graphics-config/output/host/bin/fakeroot debugfs -R "rdump / $PWD/extracted" rootfs.ext4 > extract.log 2>&1
root=$PWD/extracted
for script in sbin/muos-ext4-diag usr/libexec/muos-c01-run usr/libexec/muos-c01-chain usr/libexec/muos-entropy-functions etc/init.d/S05muos-entropy; do
 qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" sh -n "$root/$script"
done
qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/usr/libexec/muos-rng-ready" 0 > rng-qemu.txt
qemu-aarch64 -cpu cortex-a35 -L "$root" "$root/bin/busybox" seedrng --help > seedrng-help.txt 2>&1
'''
with (stage/'audit.log').open('w') as f:subprocess.run(container+[audit],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=90)
for e in entries:assert sha(stage/'extracted'/e['path'])==e['sha256']
assert not (stage/'extracted/var/lib/muos-seedrng').exists()
assert 'rng_ready=1' in (stage/'rng-qemu.txt').read_text()
assert '-d DIR' in (stage/'seedrng-help.txt').read_text()
# Exercise the compiled actual readiness code with only getrandom stubbed.
rng_cases={}
for scenario,wait,expected in [('ready','0',0),('again','0',3),('again','1',3),('interrupted','1',0),('unsupported','0',2),('short','0',3),('ready','61',2)]:
    r=subprocess.run(container+[f'/work/{stage.relative_to(work)}/rng-ready-fixture {scenario} {wait}'],capture_output=True,text=True,timeout=10)
    assert r.returncode==expected,(scenario,r.returncode,r.stderr)
    assert 'a7' not in r.stdout.lower()
    rng_cases[scenario+'-'+wait]={'exit':r.returncode,'stdout':r.stdout.strip(),'stderr':r.stderr.strip()}
# Policy fixtures call the original library with fixed test paths/executables.
# Dummy zero bytes are fixture data only; no kernel RNG or seed credit is used.
fixtures=stage/'policy-fixtures';fixtures.mkdir();policy_cases={}
for name in ['seedless','persisted','legacy-refresh','legacy-delayed','legacy-never-ready','legacy-bad-metadata','legacy-masked-refresh','never-ready','masked-native-failure','bad-directory-mode','symlink-seed','bad-seed-mode','unsupported-probe']:
    f=fixtures/name;f.mkdir();seed=f/'seed';seed.mkdir(mode=0o700);state=f/'state';state.mkdir()
    seed_file=seed/'seed.credit'
    if name in ['persisted','masked-native-failure','bad-directory-mode','bad-seed-mode'] or name.startswith('legacy-'):
        seed_file.write_bytes(b'\0'*32);seed_file.chmod(0o644 if name=='bad-seed-mode' else 0o400)
    if name=='symlink-seed':
        outside=f/'outside';outside.write_bytes(b'\0'*32);outside.chmod(0o400);seed_file.symlink_to(outside)
    if name=='bad-directory-mode':seed.chmod(0o755)
    probe=f/'probe';probe.write_text('''#!/bin/sh
[ "$CASE" != unsupported-probe ] || exit 2
if [ -e "$FIXTURE/ready" ]; then echo 'rng_ready=1 wait_ms=0'; exit 0; fi
if [ "$1" = 60 ] && [ "$CASE" != never-ready ] && [ "$CASE" != legacy-never-ready ]; then touch "$FIXTURE/ready"; echo 'rng_ready=1 wait_ms=6001'; exit 0; fi
echo 'rng_ready=0 wait_ms=0'; exit 3
''');probe.chmod(0o755)
    native=f/'native';native.write_text('''#!/bin/sh
echo "$1" >> "$FIXTURE/native-calls"
[ "$CASE" != masked-native-failure ] || exit 0
if [ -f "$FIXTURE/seed/seed.no-credit" ]; then
    [ "$CASE" != legacy-masked-refresh ] || exit 0
    [ -f "$FIXTURE/ready" ] || exit 9
    echo 'Seeding 256 bits without crediting'
    rm "$FIXTURE/seed/seed.no-credit"
elif [ "$1" = start ] && [ ! -e "$FIXTURE/legacy-used" ]; then
    case "$CASE" in legacy-*)
        echo 'Seeding 256 bits and crediting'
        rm "$FIXTURE/seed/seed.credit"
        head -c 32 /dev/zero > "$FIXTURE/seed/seed.no-credit"
        chmod 400 "$FIXTURE/seed/seed.no-credit"
        [ "$CASE" != legacy-bad-metadata ] || chmod 644 "$FIXTURE/seed/seed.no-credit"
        touch "$FIXTURE/legacy-used"
        case "$CASE" in legacy-never-ready|legacy-delayed) : ;; *) touch "$FIXTURE/ready" ;; esac
        echo 'Saving 256 bits of non-creditable seed for next boot'
        exit 0
    ;; esac
fi
if [ -f "$FIXTURE/seed/seed.credit" ]; then echo 'Seeding 256 bits and crediting'; fi
rm -f "$FIXTURE/seed/seed.credit"
head -c 32 /dev/zero > "$FIXTURE/seed/seed.credit"
chmod 400 "$FIXTURE/seed/seed.credit"
touch "$FIXTURE/ready"
echo 'Saving 256 bits of creditable seed for next boot'
''');native.chmod(0o755)
    test='''set -eu
. "$1"
seed_dir=$FIXTURE/seed
entropy_state=$FIXTURE/state
seed_uid=$(id -u);seed_gid=$(id -g)
rng_probe=$FIXTURE/probe;native_seedrng=$FIXTURE/native
entropy_start
entropy_status
entropy_stop
entropy_stop
test -f "$entropy_state/stopped"
'''
    r=subprocess.run(['sh','-c',test,'test',str(repo/'port/device/rk-r35s-p0/entropy-diagnostic/functions.sh')],env={**os.environ,'FIXTURE':str(f),'CASE':name},capture_output=True,text=True)
    ok=name in ['seedless','persisted','legacy-refresh','legacy-delayed'];assert (r.returncode==0)==ok,(name,r.stdout,r.stderr)
    calls=(f/'native-calls').read_text().splitlines() if (f/'native-calls').exists() else []
    if ok:assert calls==(['start','start','stop'] if name in ['legacy-refresh','legacy-delayed'] else ['start','stop']),calls
    elif name.startswith('legacy-'):assert calls==(['start','start'] if name=='legacy-masked-refresh' else ['start']),calls
    elif name!='masked-native-failure':assert not calls,(name,calls)
    policy_cases[name]={'passed_expected_outcome':True,'exit':r.returncode,'native_calls':calls}
record={'experiment':'MUOS-R35S-INIT-P4-C02','base_media':'MUOS-R35S-EXT4-P4-B01',
 'scope':'native SeedRNG readiness/persistence before selected services; no UI/audio',
 'policy_revision':1,'diagnostic_boot_archives':True,
 'entries':entries,'kernel_release':'4.4.189-muos-r35s-p4','root_partuuid':'4d554432-02',
 'rootfs_sha256':sha(stage/'rootfs.ext4'),'rootfs_base_sha256':base_meta['rootfs_sha256'],
 'host_audit_passed':True,'rng_cases':rng_cases,'policy_cases':policy_cases,
 'seed_material_included':False,'kernel_or_dtb_changed':False,'native_boot_tested':False,
 'port_inputs':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/utils/muos-rng-ready.c',repo/'port/probes/rng-ready-fixture.c',repo/'port/device/rk-r35s-p0/S05muos-entropy',repo/'port/device/rk-r35s-p0/entropy-diagnostic/functions.sh',repo/'port/device/rk-r35s-p0/service-diagnostic/bootstrap',repo/'port/device/rk-r35s-p0/service-diagnostic/run',repo/'port/device/rk-r35s-p0/service-diagnostic/chain.sh']}}
(stage/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
(work/'linux-diagnostic/latest-entropy').write_text(str(stage)+'\n')
print('C02 payload audited without seed material:',stage)
