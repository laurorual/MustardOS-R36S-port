#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C12 controller, quiescence and identity fixtures in a disposable container.

No device, host service, seed or power operation is used. Only the generated
controller fixture overrides the board guard and step dispatcher; native
functions are also exercised separately against synthetic runtime state.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import tempfile

repo = Path(__file__).resolve().parents[2]
work = repo / "build/phase4"
area = work / "boot-order"
area.mkdir(exist_ok=True)
stage = Path(tempfile.mkdtemp(prefix="adapters-checks.", dir=area))
script = r'''
set -eu
mkdir -p /tmp/boot/bin /tmp/session /run/muos /tmp/mock
cp /port/device/rk-r35s-p0/boot/*.sh /tmp/boot/
# Fixture only: native board guard still runs unmodified in the separate audit.
printf '\nc12_guard() { return 0; }\n' >> /tmp/boot/native-functions.sh
cat > /tmp/boot/bin/muos-run-bounded <<'EOF'
#!/bin/sh
shift
exec "$@"
EOF
cat > /tmp/boot/step.sh <<'EOF'
#!/bin/sh
echo "$1" >> /tmp/events
case " $FAIL " in *" $1 "*) exit 1 ;; esac
exit 0
EOF
chmod 755 /tmp/boot/*.sh /tmp/boot/bin/*
export MUOS_BOOT_CONFIG=/tmp/boot.conf FAIL=
printf 'enabled=0\nallow_power=0\n' > /tmp/boot.conf
chmod 600 /tmp/boot.conf
# Replace power commands only INSIDE this disposable, networkless container.
for action in reboot poweroff; do
    rm -f /sbin/$action
    printf '#!/bin/sh\necho %s >> /tmp/power-events\n' "$action" > /sbin/$action
    chmod 755 /sbin/$action
done
pass() { echo "PASS $1"; }
refuse() { if "$@"; then echo 'unexpected success' >&2; exit 1; fi; }
reset() { rm -rf /run/muos/boot; : > /tmp/events; : > /tmp/power-events; export FAIL=; }
reset
/tmp/boot/service.sh start
[ ! -e /run/muos/boot ]
pass disabled-no-state
refuse /tmp/boot/service.sh reboot
[ ! -s /tmp/events ] && [ ! -s /tmp/power-events ]
pass power-default-denied
printf 'enabled=1\nallow_power=1\n' > /tmp/boot.conf
refuse /tmp/boot/service.sh prepare-stop
pass no-adoption-of-C07
reset
/tmp/boot/service.sh start
[ "$(wc -l < /tmp/events)" = 8 ]
/tmp/boot/service.sh start
[ "$(tail -n 1 /tmp/events)" = session.status ]
[ "$(grep -c '^entropy.start$' /tmp/events)" = 1 ]
pass start-idempotent-no-reseed
/tmp/boot/service.sh prepare-stop
cp /tmp/events /tmp/stop-first
/tmp/boot/service.sh shutdown
cmp /tmp/stop-first /tmp/events
pass prepare-and-inittab-stop-idempotent
for failed in session.stop session.quiescent network.stop udev.stop root.sync root.seal; do
    reset
    mkdir -p /run/muos/boot/start-once
    export FAIL=$failed
    refuse /tmp/boot/service.sh prepare-stop
    [ ! -s /tmp/power-events ]
    [ "$(tail -n 1 /tmp/events)" = "$failed" ]
    [ ! -e /run/muos/boot/power-request ]
    pass stop-block-$failed
done
reset
mkdir -p /run/muos/boot/start-once
exec 7>/run/muos/boot/control.lock; flock -n 7
refuse /tmp/boot/service.sh start
[ ! -s /tmp/events ]
exec 7>&-
pass concurrent-control-refused
chmod 666 /tmp/boot.conf
refuse /tmp/boot/service.sh start
chmod 600 /tmp/boot.conf
pass writable-config-refused

# Test real native functions, not the fixture's replacement guard/dispatcher.
. /port/device/rk-r35s-p0/boot/native-functions.sh
boot_package=/tmp/boot; boot_state=/run/muos/boot; session_package=/tmp/session
refuse c12_guard
pass non-board-native-guard-refused
cp /port/device/rk-r35s-p0/session/control-functions.sh /tmp/session/
cat > /tmp/session/service.sh <<'EOF'
#!/bin/sh
exit "${SESSION_STATUS:-3}"
EOF
chmod 755 /tmp/session/service.sh
cat > /tmp/mock/pidof <<'EOF'
#!/bin/sh
[ "${FOUND_PROCESS:-}" = "$1" ] || exit 1
echo 99999
EOF
cat > /tmp/mock/findmnt <<'EOF'
#!/bin/sh
[ "${FOUND_MOUNT:-}" = "$3" ] && [ -n "${FOUND_MOUNT:-}" ]
EOF
chmod 755 /tmp/mock/*
PATH=/tmp/mock:$PATH; export PATH
export SESSION_STATUS=3 FOUND_PROCESS= FOUND_MOUNT=
rm -rf /run/muos/session
c12_session_quiescent || exit 1
pass quiescent-without-session
export SESSION_STATUS=0
refuse c12_session_quiescent
pass ready-session-refused
export SESSION_STATUS=2
refuse c12_session_quiescent
pass status-error-refused
export SESSION_STATUS=3
mkdir -p /run/muos/session/run-0001
echo run-0001 > /run/muos/session/current
refuse c12_session_quiescent
pass incomplete-cleanup-refused
touch /run/muos/session/run-0001/done
echo 1 > /run/muos/session/run-0001/result
refuse c12_session_quiescent
pass failed-cleanup-refused
echo 0 > /run/muos/session/run-0001/result
c12_session_quiescent || exit 1
pass successful-cleanup-accepted
touch /run/muos/session/run-0001/attempted
refuse c12_session_quiescent
rm /run/muos/session/run-0001/attempted
pass attempted-chain-refused
exec 6>/run/muos/session/lifetime.lock; flock -n 6
refuse c12_session_quiescent
exec 6>&-
pass held-worker-lock-refused
export FOUND_PROCESS=pipewire
refuse c12_session_quiescent
export FOUND_PROCESS=
pass orphan-audio-refused
mkdir -p /run/muos/core; touch /run/muos/core/ready
refuse c12_session_quiescent
rm /run/muos/core/ready
pass stale-core-ready-refused
export FOUND_MOUNT=/opt/muos/config
refuse c12_session_quiescent
export FOUND_MOUNT=
pass retained-bind-refused

# PID guards use actual process metadata, without signaling the foreign process.
sleep 60 & foreign=$!
sleep 0.05
echo "$foreign" > /tmp/test.pid
exe=$(readlink /proc/$foreign/exe)
c12_record_pid /tmp/test.pid /tmp/test.identity "$exe"
c12_check_pid /tmp/test.pid /tmp/test.identity "$exe"
pass live-identity-matches
echo "$foreign 1" > /tmp/test.identity
refuse c12_check_pid /tmp/test.pid /tmp/test.identity "$exe"
kill -0 "$foreign"
pass reused-PID-never-adopted
rm /tmp/test.identity
refuse c12_check_pid /tmp/test.pid /tmp/test.identity "$exe"
pass missing-live-identity-refused
c12_record_pid /tmp/test.pid /tmp/test.identity "$exe"
rm /tmp/test.pid
refuse c12_check_pid /tmp/test.pid /tmp/test.identity "$exe"
pass missing-pidfile-with-live-daemon-refused
kill "$foreign"; wait "$foreign" 2>/dev/null || :
c12_check_pid /tmp/test.pid /tmp/test.identity "$exe"
pass stopped-identity-idempotent

# Existing C07 RNG/network must be refused before any native helper invocation.
mkdir -p /etc/init.d /usr/libexec /run/muos/entropy /run/muos/c07
printf '#!/bin/sh\necho seed-helper >> /tmp/forbidden\n' > /etc/init.d/S05muos-entropy
printf '#!/bin/sh\necho network-helper >> /tmp/forbidden\n' > /usr/libexec/muos-c07-network
chmod 755 /etc/init.d/S05muos-entropy /usr/libexec/muos-c07-network
: > /tmp/forbidden
refuse c12_native_step entropy.start
refuse c12_native_step entropy.stop
[ ! -s /tmp/forbidden ]
pass C07-seed-never-reloaded-or-stopped
touch /run/muos/c07/ready
refuse c12_native_step network.start
refuse c12_native_step network.stop
[ ! -s /tmp/forbidden ]
pass C07-network-never-adopted-or-stopped
'''
container = [
    "podman", "run", "--rm", "--network=none", "--cap-drop=all",
    "--security-opt=no-new-privileges", "--userns=keep-id", "--user=0",
    "--tmpfs", "/run:rw,nosuid,nodev", "--tmpfs", "/tmp:rw,nosuid,nodev",
    "-v", f"{repo}/port:/port:ro,z",
    (work / "rootfs-container.iid").read_text().strip(),
    "sh", "-c", script,
]
(stage / "fixture.sh").write_text(script)
result = subprocess.run(container, capture_output=True, text=True, timeout=60)
(stage / "stdout").write_text(result.stdout)
(stage / "stderr").write_text(result.stderr)
assert result.returncode == 0, (stage, result.stdout, result.stderr)
cases = [line[5:] for line in result.stdout.splitlines() if line.startswith("PASS ")]
assert len(cases) == 32, cases
sources = sorted((repo / "port/device/rk-r35s-p0/boot").glob("*")) + [Path(__file__)]
report = {
    "passed": True, "case_count": len(cases), "cases": cases,
    "real_device_network_seed_or_power_executed": False,
    "controller_fixture_guard_and_dispatcher_overridden": True,
    "native_functions_tested_separately": True,
    "limits_enforced_by_real_bounded_tool_in_these_fixtures": False,
    "sources": {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sources if p.is_file()},
}
(stage / "report.json").write_text(json.dumps(report, indent=2) + "\n")
(area / "latest-adapter-checks").write_text(str(stage) + "\n")
print(f"C12 host adapters/controller: {len(cases)} cases passed; {stage}")
