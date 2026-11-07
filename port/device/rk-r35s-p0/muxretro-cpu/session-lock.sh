# SPDX-License-Identifier: MIT
# C07 has no session directory until its first opt-in workload.
cpu_lock_base=/run/muos/session
if [ ! -e "$cpu_lock_base" ] && [ ! -L "$cpu_lock_base" ]; then
    mkdir -m 700 "$cpu_lock_base"
fi
[ -d "$cpu_lock_base" ] && [ ! -L "$cpu_lock_base" ]
[ "$(stat -c '%u:%g:%a' "$cpu_lock_base")" = 0:0:700 ]
exec 8>"$cpu_lock_base/lifetime.lock"
flock -n 8
