# SPDX-License-Identifier: MIT
"""Measure a PCM pointer rate only across one uninterrupted running stream."""
from decimal import Decimal
import re


def measure(text):
    first, second = text.split('FIRST\n', 1)[1].split('SECOND\n', 1)

    def field(sample, name):
        values = re.findall(r'^' + re.escape(name) + r'\s*:\s*(.+)$', sample, re.M)
        assert len(values) == 1, ('missing or duplicate PCM field', name)
        return values[0].strip()

    rate = int(field(first, 'rate').split()[0])
    assert rate > 0
    for name in ['owner_pid', 'trigger_time']:
        assert field(first, name) == field(second, name), ('stream reset', name)
    assert all(field(s, 'state') == 'RUNNING' for s in [first, second])
    seconds = Decimal(field(second, 'tstamp')) - Decimal(field(first, 'tstamp'))
    frames = int(field(second, 'hw_ptr')) - int(field(first, 'hw_ptr'))
    assert seconds >= 1 and frames > 0, 'invalid or insufficient PCM interval'
    actual = float(Decimal(frames) / seconds)
    return {'declared_rate': rate, 'actual_frames_per_second': actual,
            'interval_seconds': float(seconds), 'frames': frames,
            'same_owner_and_trigger': True,
            'within_two_percent': abs(actual / rate - 1) <= .02}
