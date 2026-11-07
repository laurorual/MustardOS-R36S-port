# SPDX-License-Identifier: MIT
"""Name a forward-only repeat without replacing the first qualified boot."""
def repeat_name(prefix, operation, trial, reference, previous_fallback):
    assert prefix == 'primed-launcher'
    assert operation in ['session', 'fallback']
    assert reference['passed'] and reference['audio_passed']
    assert reference['direct_zero_PCM_priming']
    assert previous_fallback['passed'] and previous_fallback['audio_passed']
    assert previous_fallback['direct_zero_PCM_priming']
    assert previous_fallback['boot_sequence'] == reference['boot_sequence'] + 1
    assert trial['experiment'] == reference['experiment'] == previous_fallback['experiment'] == 'C37_PRIMED_LAUNCHER_BOOT'
    assert trial['before_boot'] >= previous_fallback['boot_sequence']
    assert trial['expected_boot'] == trial['before_boot'] + 1
    assert trial['expected_fallback'] == trial['expected_boot'] + 1
    sequence = trial['expected_boot' if operation == 'session' else 'expected_fallback']
    assert 1 <= sequence <= 9999
    return prefix + ('-boot-' if operation == 'session' else '-fallback-') + f'{sequence:04d}'
