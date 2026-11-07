#!/usr/bin/env python3
"""Short graphics test against only the candidate rootfs, called in its jail."""


def render(command, env, root):
    env.update(SDL_VIDEODRIVER='KMSDRM', SDL_VIDEO_EGL_DRIVER='libEGL.so',
               SDL_VIDEO_GL_DRIVER='libGLESv2.so', LD_BIND_NOW='1')
    for probe in ('graphics-contract', 'gbm-contract', 'drm-mode-probe'):
        result = command(['/opt/port-probes/' + probe], capture=True, timeout=15)
        (root / (probe + '-native.txt')).write_text(result.stdout)
    command(['/lib/ld-linux-aarch64.so.1', '--list', '/opt/port-probes/sdl-video-probe'], capture=True)
    print('PHASE4_GRAPHICS_PATTERN_STARTING', flush=True)
    result = command(['/opt/port-probes/sdl-video-probe', '30'], capture=True, check=False, timeout=45)
    (root / 'sdl-video-native.txt').write_text(result.stdout)
    assert result.returncode == 0, 'SDL video probe returned ' + str(result.returncode)
    assert 'readback_red_pixel=PASS' in result.stdout
    assert 'sdl_probe_exit_status=0' in result.stdout
    print('PHASE4_GRAPHICS_PATTERN_FINISHED', flush=True)
