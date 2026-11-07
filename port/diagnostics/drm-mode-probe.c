/* SPDX-License-Identifier: MIT */
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>
#include <xf86drmMode.h>

int main(void) {
    int fd = open("/dev/dri/card0", O_RDONLY | O_CLOEXEC);
    if (fd < 0) { perror("open DRM"); return 1; }
    drmModeRes *resources = drmModeGetResources(fd);
    if (!resources) { perror("drmModeGetResources"); close(fd); return 1; }
    for (int i = 0; i < resources->count_crtcs; ++i) {
        drmModeCrtc *crtc = drmModeGetCrtc(fd, resources->crtcs[i]);
        if (!crtc) continue;
        if (crtc->mode_valid) {
            drmModeModeInfo *mode = &crtc->mode;
            double refresh = mode->htotal && mode->vtotal ? mode->clock * 1000.0 / mode->htotal / mode->vtotal : 0;
            printf("crtc=%u mode=%s size=%ux%u clock_khz=%u htotal=%u vtotal=%u hsync_len=%u vsync_len=%u calculated_hz=%.6f\n",
                crtc->crtc_id, mode->name, mode->hdisplay, mode->vdisplay, mode->clock,
                mode->htotal, mode->vtotal, mode->hsync_end-mode->hsync_start,
                mode->vsync_end-mode->vsync_start, refresh);
        }
        drmModeFreeCrtc(crtc);
    }
    drmModeFreeResources(resources);
    close(fd);
    return 0;
}
