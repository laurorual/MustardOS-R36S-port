#!/usr/bin/env python3
"""Local Hardkernel diagnostic, separate from the rejected firmware candidate."""
import runpy


def probe(command, env, root, display):
    env['LD_BIND_NOW'] = '1'
    for name in ('graphics-contract', 'gbm-contract', 'egl-context'):
        result = command(['/opt/port-probes/' + name], capture=True, check=False, timeout=20)
        (root / (name + '-native.txt')).write_text(result.stdout)
        assert result.returncode == 0, name + ': exit ' + str(result.returncode)
    print('PHASE4_R13_EGL_CONTEXT_AND_READBACK=OK', flush=True)
    if display:
        diagnostic = runpy.run_path(str(root / 'phase4-graphics-native.py'))
        diagnostic['render'](command, env, root)
