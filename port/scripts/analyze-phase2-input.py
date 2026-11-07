#!/usr/bin/env python3
"""Check coverage, releases and directions from the two physical test sequences."""
import json
from pathlib import Path
import sys
from collections import Counter

raw = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines()]
normalized = [json.loads(line) for line in Path(sys.argv[2]).read_text().splitlines()]
recheck_after = float(sys.argv[3]) if len(sys.argv) > 3 else float("inf")
recheck = [event for event in normalized if event["elapsed"] >= recheck_after]
normalized = [event for event in normalized if event["elapsed"] < recheck_after]
raw_expected = [544,545,546,547,305,304,307,308,310,311,312,313,704,705,708,706,707,114,115,116]
normal_expected = [305,304,307,308,310,311,312,313,314,315,316,317,318,114,115]
report = {"raw_event_count": len(raw), "normalized_event_count": len(normalized), "checks": {}}
checks = report["checks"]
for label, events, expected in [("raw", raw, raw_expected), ("normalized", normalized, normal_expected)]:
    presses = [e["code"] for e in events if e["type"] == 1 and e["value"] == 1]
    releases = [e["code"] for e in events if e["type"] == 1 and e["value"] == 0]
    checks[label + "_button_order"] = presses == expected
    checks[label + "_balanced_releases"] = Counter(releases) == Counter(presses)
    checks[label + "_no_syn_dropped"] = not any(e["type"] == 0 and e["code"] == 3 for e in events)
    state = {}
    for event in events:
        if event["type"] == 1 and event["value"] != 2:
            state[event["code"]] = event["value"]
    checks[label + "_no_stuck_keys"] = not any(state.values())
    report[label + "_press_codes"] = presses
report["axes"] = {}
for code in [0,1,3,4]:
    entries = [e for e in normalized if e["type"] == 3 and e["code"] == code]
    values = [e["value"] for e in entries]
    report["axes"][str(code)] = {"count": len(values), "min": min(values) if values else None, "max": max(values) if values else None, "last": values[-1] if values else None}
    checks["axis_" + str(code) + "_negative_then_positive"] = bool(values) and next((v for v in values if v), 0) < 0 and min(values) < -25000 and max(values) > 25000
    checks["axis_" + str(code) + "_centered"] = bool(values) and values[-1] == 0
for code, expected in [(17,[-1,0,1,0]),(16,[-1,0,1,0])]:
    values = [e["value"] for e in normalized if e["type"] == 3 and e["code"] == code]
    checks["hat_" + str(code)] = values == expected
    report["hat_" + str(code)] = values
report["pass"] = all(checks.values())
if recheck:
    report["l3_recheck"] = {"events": recheck, "single_pair": [(e["type"],e["code"],e["value"]) for e in recheck] == [(1,317,1),(1,317,0)]}
report["note"] = "A false strict button-order result is retained; no duplicates are silently removed."
print(json.dumps(report, indent=2))
sys.exit(0 if report["pass"] else 1)
