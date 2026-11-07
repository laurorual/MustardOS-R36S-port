#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C22 opt-in integrity guard fixtures without hardware, boot package or UI."""
from pathlib import Path
import hashlib,json,subprocess,tempfile

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'runtime-session'
stage=Path(tempfile.mkdtemp(prefix='package-checks.',dir=area))
script=r'''
set -eu
[ ! -e /usr/libexec/muos-boot ]
mkdir -p /tmp/package
cp /port/device/rk-r35s-p0/session/service.sh /port/device/rk-r35s-p0/session/control-functions.sh /tmp/package/
cp /port/device/rk-r35s-p0/preferences/data-functions.sh /port/device/rk-r35s-p0/linux-diagnostic/card-guard.sh /tmp/package/
cat > /tmp/package/mount-namespace <<'EOF'
#!/bin/sh
exec "$@"
EOF
cat > /tmp/package/worker.sh <<'EOF'
#!/bin/sh
set -eu
state=$1
printf '%s %s\n' "$$" "$(awk '{print $22}' /proc/$$/stat)" > "$state/manager"
trap 'rm -f "$state/ready"; echo 0 > "$state/result"; touch "$state/done"; exit 0' TERM HUP INT
touch "$state/ready"
while :; do sleep 0.1; done
EOF
chmod 755 /tmp/package/*
export MUOS_SESSION_CONFIG=/tmp/config
printf 'enabled=0\npreferences_enabled=1\nlease_seconds=30\n' >/tmp/config
chmod 600 /tmp/config
sh /tmp/package/service.sh start
[ ! -e /run/muos/session/current ];echo PASS_disabled_no_manifest_needed
printf 'enabled=1\npreferences_enabled=1\nlease_seconds=30\n' >/tmp/config
reject() {
 rc=0;sh /tmp/package/service.sh start >/tmp/rejected.stdout 2>/tmp/rejected.stderr || rc=$?
 [ "$rc" = 64 ];[ ! -e /run/muos/session/current ];[ ! -e /run/muos/session/sequence ]
}
reject;echo PASS_missing_manifest_no_generation
manifest() { (cd /tmp/package;find . -type f ! -name payload.sha256 | sort | while IFS= read -r f;do sha256sum "$f";done) >/tmp/package/payload.sha256; }
manifest
cp /tmp/package/payload.sha256 /tmp/manifest
rm /tmp/package/payload.sha256;ln -s /tmp/manifest /tmp/package/payload.sha256
reject;echo PASS_symlink_manifest_no_generation
rm /tmp/package/payload.sha256;cp /tmp/manifest /tmp/package/payload.sha256
cp /tmp/package/data-functions.sh /tmp/original-data
printf '\n# altered\n' >> /tmp/package/data-functions.sh
reject;echo PASS_tampered_helper_no_generation
cp /tmp/original-data /tmp/package/data-functions.sh
mv /tmp/package/mount-namespace /tmp/namespace
reject;echo PASS_missing_executable_no_generation
mv /tmp/namespace /tmp/package/mount-namespace
sh /tmp/package/service.sh start;sh /tmp/package/service.sh status
sh /tmp/package/service.sh stop
echo PASS_valid_payload_start_stop_without_boot_package
(
 . /tmp/package/data-functions.sh
 id() { touch /tmp/hardware-check-reached;return 1; }
 rc=0;prefs_data_source || rc=$?
 [ "$rc" = 64 ];[ ! -e /tmp/hardware-check-reached ]
)
echo PASS_missing_card_function_refused_before_hardware
. /tmp/package/card-guard.sh
command -v diag_card >/dev/null
echo PASS_local_card_function_available
'''
args=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--user=0','--tmpfs','/tmp:rw,nosuid,nodev','--tmpfs','/run:rw,nosuid,nodev','-v',f'{repo}/port:/port:ro,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-c',script]
r=subprocess.run(args,capture_output=True,text=True,timeout=30)
(stage/'fixtures.sh').write_text(script);(stage/'stdout').write_text(r.stdout);(stage/'stderr').write_text(r.stderr)
assert r.returncode==0,(stage,r.stdout,r.stderr)
cases=[line[5:] for line in r.stdout.splitlines() if line.startswith('PASS_')];assert len(cases)==8
report={'passed':True,'cases':cases,'hardware_tested':False,'boot_package_present':False,'source_sha256':{str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),repo/'port/device/rk-r35s-p0/session/service.sh',repo/'port/device/rk-r35s-p0/preferences/data-functions.sh']}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-package-checks').write_text(str(stage)+'\n')
print('C22 integrity/dependency fixtures passed:',len(cases),stage)
