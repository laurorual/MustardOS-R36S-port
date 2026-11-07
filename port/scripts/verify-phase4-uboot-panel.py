#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compare the display contract only; this is not a complete U-Boot board audit."""
from pathlib import Path
import hashlib
import json
import runpy
import struct
import sys

properties = runpy.run_path(str(Path(__file__).with_name('verify-phase4-dtb.py')))['properties']


def verify(candidate_path, reference_path):
    candidate, digest = properties(candidate_path)
    reference, ref_digest = properties(reference_path)
    assert ref_digest == 'e65ccee748de35597c3f7f5e3032ed33e8312abba886bd3dba1aa0dbf662d102'
    assert candidate[('/', 'model')] == b'R36S-V12 2023-08-18 Panel 0\0'
    panel = '/dsi@ff450000/panel@0'
    prefixes = [panel, '/backlight']
    ignore = {'phandle', 'linux,phandle'}

    def canonical(tree, key):
        value = tree[key]
        handles = {struct.unpack('>I', v)[0]: node for (node, prop), v in tree.items() if prop == 'phandle'}
        name = key[1]
        if name in {'backlight', 'native-mode'} or name.endswith('-supply'):
            assert len(value) == 4, key
            return handles[struct.unpack('>I', value)[0]]
        if name in {'reset-gpios', 'pwms'}:
            cells = list(struct.unpack('>'+'I'*(len(value)//4), value))
            return [handles[cells[0]], *cells[1:]]
        return value

    selected = {key for key in reference if any(key[0] == p or key[0].startswith(p+'/') for p in prefixes) and key[1] not in ignore}
    actual = {key for key in candidate if any(key[0] == p or key[0].startswith(p+'/') for p in prefixes) and key[1] not in ignore}
    assert selected == actual, (selected-actual, actual-selected)
    for key in sorted(selected):
        assert canonical(candidate, key) == canonical(reference, key), key
    # Validate the referenced regulator voltage/on-state and GPIO/PWM enablement,
    # rather than comparing numeric phandle allocations.
    providers = {}
    for name in ['backlight-supply', 'power-supply', 'reset-gpios']:
        key = (panel, name)
        provider = canonical(reference, key)
        if isinstance(provider, list):
            provider = provider[0]
        providers[provider] = name
    providers[canonical(reference, ('/backlight', 'pwms'))[0]] = 'pwms'
    critical = ['status', 'compatible', 'regulator-name', 'regulator-min-microvolt',
                'regulator-max-microvolt', 'regulator-always-on', 'regulator-boot-on', '#pwm-cells', '#gpio-cells']
    checked = []
    for node in providers:
        for name in critical:
            key = (node, name)
            assert candidate.get(key) == reference.get(key), key
            if key in reference:
                checked.append({'node': node, 'property': name})
    init = candidate[(panel, 'panel-init-sequence')]
    assert len(init) == 370
    timing = panel+'/display-timings/60Hz'
    values = {name: struct.unpack('>I', candidate[(timing, name)])[0] for name in
              ['clock-frequency', 'hactive', 'vactive', 'hfront-porch', 'hsync-len', 'hback-porch',
               'vfront-porch', 'vsync-len', 'vback-porch']}
    return {'scope': 'Panel 0 U-Boot display/backlight properties, typed references and selected provider properties only',
            'passed': True, 'candidate_sha256': digest, 'reference_sha256': ref_digest,
            'panel_init_sha256': hashlib.sha256(init).hexdigest(), 'panel_init_bytes': len(init),
            'display_properties_compared': len(selected), 'provider_properties': checked, 'timing': values,
            'model_changed_from_generic_rg351mp': True,
            'complete_board_equivalence_checked': False, 'uboot_executable_built': False, 'boot_tested': False}


if __name__ == '__main__':
    print(json.dumps(verify(*sys.argv[1:]), indent=2))
