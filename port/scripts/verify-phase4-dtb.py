#!/usr/bin/env python3
"""Compare the port DTB with the pinned installed Panel 0, without hardware I/O."""
import hashlib
import json
from pathlib import Path
import struct
import sys


def properties(path):
    data = Path(path).read_bytes()
    if len(data) < 40:
        raise ValueError('Truncated FDT header')
    magic, size, start, strings, _, _, _, _, strings_size, struct_size = struct.unpack_from('>10I', data)
    if magic != 0xD00DFEED or size > len(data) or start + struct_size > size or strings + strings_size > size:
        raise ValueError('Invalid FDT bounds')
    names = data[strings:strings + strings_size]
    pos, stack, result = start, [], {}
    end = start + struct_size
    while pos + 4 <= end:
        token, = struct.unpack_from('>I', data, pos)
        pos += 4
        if token == 1:
            stop = data.index(b'\0', pos, end)
            stack.append(data[pos:stop].decode())
            pos = (stop + 4) & ~3
        elif token == 2:
            stack.pop()
        elif token == 3:
            length, offset = struct.unpack_from('>II', data, pos)
            pos += 8
            if not stack or pos + length > end or offset >= len(names):
                raise ValueError('Invalid FDT property')
            name = names[offset:names.index(b'\0', offset)].decode()
            result[('/' + '/'.join(stack[1:]), name)] = data[pos:pos + length]
            pos = (pos + length + 3) & ~3
        elif token == 9:
            if stack:
                raise ValueError('Unclosed FDT node')
            return result, hashlib.sha256(data).hexdigest()
        elif token != 4:
            raise ValueError('Unknown FDT token')
    raise ValueError('Missing FDT end token')


def main():
    if len(sys.argv) != 3:
        raise ValueError('Usage: verify-phase4-dtb.py PORT.dtb INSTALLED-PANEL0.dtb')
    candidate, digest = properties(sys.argv[1])
    reference, ref_digest = properties(sys.argv[2])
    lock = json.loads((Path(__file__).resolve().parents[1] / 'device/rk-r35s-p0/phase4-sources.json').read_text())
    if ref_digest != lock['running_reference']['linux_dtb_sha256']:
        raise ValueError('Reference is not the pinned installed Panel 0')
    expected_model = b'R36S-V12 2023-08-18 Panel 0\0'
    if candidate.get(('/', 'model')) != expected_model:
        raise ValueError('Port DTB has a different model')
    panel = '/dsi@ff450000/panel@0'
    init = candidate[(panel, 'panel-init-sequence')]
    if init != reference[(panel, 'panel-init-sequence')] or len(init) != 370:
        raise ValueError('Panel initialization differs')
    timing = panel + '/display-timings/60Hz'
    values = {name: struct.unpack('>I', candidate[(timing, name)])[0] for name in
              ['clock-frequency', 'hactive', 'vactive', 'hfront-porch', 'hsync-len',
               'hback-porch', 'vfront-porch', 'vsync-len', 'vback-porch']}
    limits = {}
    for table, ceiling in [('/cpu0-opp-table', 1296000000), ('/gpu-opp-table', 520000000)]:
        frequencies = [struct.unpack('>Q', value)[0] for (node, name), value in candidate.items()
                       if node.startswith(table + '/') and name == 'opp-hz']
        if not frequencies or max(frequencies) > ceiling:
            raise ValueError('Unexpected OPP ceiling for ' + table)
        limits[table] = max(frequencies)
    allowed_properties = {
        ('/cpu0-opp-table', 'rockchip,max-volt'),
        ('/i2c@ff180000/pmic@20/regulators/DCDC_REG2', 'regulator-max-microvolt')
    }
    allowed_subtrees = [panel + '/display-timings/' + rate for rate in ['50Hz', '75Hz']]
    allowed_subtrees += ['/cpu0-opp-table/opp-' + str(hz) for hz in
                         [1368000000, 1416000000, 1440000000, 1464000000, 1488000000, 1512000000]]
    allowed_subtrees += ['/gpu-opp-table/opp-600000000']

    def canonical(tree, key):
        """Resolve typed references; numeric hardware values remain numeric."""
        value = tree.get(key)
        if value is None:
            return None
        name = key[1]
        handles = {struct.unpack('>I', v)[0]: node for (node, prop), v in tree.items()
                   if prop == 'phandle'}
        tuples = {'clocks': '#clock-cells', 'assigned-clocks': '#clock-cells',
                  'assigned-clock-parents': '#clock-cells', 'resets': '#reset-cells',
                  'phys': '#phy-cells', 'iommus': '#iommu-cells', 'dmas': '#dma-cells',
                  'pwms': '#pwm-cells', 'power-domains': '#power-domain-cells',
                  'thermal-sensors': '#thermal-sensor-cells', 'cooling-device': '#cooling-cells',
                  'io-channels': '#io-channel-cells', 'sound-dai': '#sound-dai-cells',
                  'interrupts-extended': '#interrupt-cells'}
        references = {'native-mode', 'extcon', 'memory-region', 'backlight', 'devfreq',
                      'devfreq-events', 'operating-points-v2', 'trip', 'ddr_timing',
                      'rockchip,pmu', 'rockchip,pmugrf', 'rockchip,grf', 'rockchip,boost',
                      'rockchip,sub', 'remote-endpoint', 'cpu-idle-states', 'nvmem-cells',
                      'interrupt-parent', 'interrupt-affinity'}
        if name.endswith(('-gpios', '-gpio', '_gpio')) or name in ['gpios', 'gpio']:
            cells = '#gpio-cells'
        elif name in tuples:
            cells = tuples[name]
        elif name in references or name.startswith('pinctrl-') and name[-1:].isdigit() or name.endswith('-supply'):
            cells = None
        elif name != 'rockchip,pins':
            return value
        values = list(struct.unpack('>' + 'I' * (len(value) // 4), value))
        if name == 'rockchip,pins':
            for index in range(3, len(values), 4):
                values[index] = handles[values[index]]
            return values
        result, index = [], 0
        while index < len(values):
            handle = values[index]
            index += 1
            if not handle:
                result.append(None)
                continue
            provider = handles[handle]
            count = struct.unpack('>I', tree[(provider, cells)])[0] if cells else 0
            if index + count > len(values):
                raise ValueError('Truncated phandle arguments for ' + str(key))
            result.append((provider, values[index:index + count]))
            index += count
        return result

    differences = []
    for key in sorted(candidate.keys() | reference.keys()):
        node, name = key
        if node.startswith(('/__symbols__', '/__fixups__', '/__local_fixups__')) or name in ['phandle', 'linux,phandle']:
            continue
        if candidate.get(key) == reference.get(key) or canonical(candidate, key) == canonical(reference, key):
            continue
        if key in allowed_properties:
            if struct.unpack('>I', candidate[key])[0] != 1350000:
                raise ValueError('Unexpected voltage ceiling')
        elif any(node == prefix or node.startswith(prefix + '/') for prefix in allowed_subtrees):
            if key in candidate:
                raise ValueError('Expected removed alternate mode or overclock OPP: ' + str(key))
        else:
            raise ValueError('Unexplained hardware property difference: ' + str(key))
        differences.append({'node': node, 'property': name})
    refresh = values['clock-frequency'] / (
        (values['hactive'] + values['hfront-porch'] + values['hsync-len'] + values['hback-porch']) *
        (values['vactive'] + values['vfront-porch'] + values['vsync-len'] + values['vback-porch']))
    print(json.dumps({'status': 'host property comparison passed; no boot validation',
                      'candidate_sha256': digest, 'reference_sha256': ref_digest,
                      'panel_init_sha256': hashlib.sha256(init).hexdigest(),
                      'timing': values, 'nominal_refresh_hz': refresh,
                      'opp_ceilings_hz': limits, 'intentional_differences': differences}, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, IndexError, struct.error) as error:
        raise SystemExit('DTB verification failed: ' + str(error))
