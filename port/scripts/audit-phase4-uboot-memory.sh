#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Native host fixture against the exact allocator/board sources of latest-build.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
stage=$(cat "$work/uboot-sd/latest-build")
[[ "$stage" == "$work/uboot-sd"/probe.* ]]
mkdir -p "$stage/memory-audit"
podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
 --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev -v "$work:/work:rw,z" -v "$repo/port:/port:ro,z" \
 -e UBOOT_PROBE_REL="${stage#"$work/"}" "$(cat "$work/kernel-container.iid")" sh -eu -c '
 stage=/work/$UBOOT_PROBE_REL
 source=$stage/source
 gcc -std=gnu11 -O1 -g -Wall -Wextra -Wno-unused-parameter -Wno-format \
  -ffunction-sections -fdata-sections -fPIE -pie -fsanitize=undefined -fno-sanitize-recover=all \
  -I /port/probes/uboot-memory/shim -idirafter "$source/include" \
  /port/probes/uboot-memory/allocator.c "$source/lib/sysmem.c" "$source/lib/lmb.c" \
  "$source/arch/arm/mach-rockchip/memblk.c" "$source/board/rockchip/odroidgoa/muos-r35s-probe.c" \
  -Wl,--gc-sections -o "$stage/memory-audit/allocator-host" > "$stage/memory-audit/compile.log" 2>&1
 timeout 15 "$stage/memory-audit/allocator-host" > "$stage/memory-audit/run.log" 2>&1
 ' > "$stage/memory-audit/container.log" 2>&1
grep -q '^PASS: actual native allocators;' "$stage/memory-audit/run.log"
python3 - "$repo" "$stage" <<'PY'
from pathlib import Path
import hashlib,json,sys
repo,stage=map(Path,sys.argv[1:])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=json.loads((stage/'inputs.json').read_text())
for name,digest in record['source_files'].items():assert sha(stage/'source'/name)==digest,name
sources=['lib/sysmem.c','lib/lmb.c','arch/arm/mach-rockchip/memblk.c',
         'board/rockchip/odroidgoa/muos-r35s-probe.c','include/configs/muos-r35s-memory.h']
port_inputs=[p for p in (repo/'port/probes/uboot-memory').rglob('*') if p.is_file()]
port_inputs += [repo/'port/scripts/audit-phase4-uboot-memory.sh']
report={'scope':'actual native allocators on x86_64 with mocked gd/BIDRAM discovery and private anonymous mappings',
 'passed':True,'ubsan_passed':True,'hardware_tested':False,
 'control_fdt':{'base':'0x01e00000','bytes':262144,'name':'muos-control-fdt'},
 'visual_monitor_gates_and_formatted_lines_mocked':True,
 'native_display_renderer_exercised':False,
 'cases':['reject before init','early and post relocation reserve','idempotent same region',
          'reject collision','allow adjacent allocation','Linux FDT remains separate',
          'independent bootm LMB excludes buffer','installed Linux banks with ATF/TEE holes',
          'reject overlapping stack',
          'reject insufficient RAM','reject gap in available RAM banks'],
 'source_sha256':{name:sha(stage/'source'/name) for name in sources},
 'port_inputs':{str(p.relative_to(repo)):sha(p) for p in sorted(port_inputs)},
 'run_log_sha256':sha(stage/'memory-audit/run.log')}
(stage/'memory-audit/report.json').write_text(json.dumps(report,indent=2)+'\n')
print('Actual allocator fixture passed; no hardware test')
PY
