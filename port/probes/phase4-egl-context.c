/* SPDX-License-Identifier: MIT
 * Render a tiny GBM/EGL buffer without changing any KMS CRTC or connector.
 * This is a private diagnostic, not a display or firmware boot test.
 */
#include <EGL/egl.h>
#include <GLES2/gl2.h>
#include <gbm.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(void) {
    int result = 1;
    int fd = open("/dev/dri/card0", O_RDWR | O_CLOEXEC);
    struct gbm_device *device = NULL;
    struct gbm_surface *window = NULL;
    EGLDisplay display = EGL_NO_DISPLAY;
    EGLSurface surface = EGL_NO_SURFACE;
    EGLContext context = EGL_NO_CONTEXT;
    EGLConfig configs[32], config = NULL;
    EGLint count = 0, major = 0, minor = 0;
    const EGLint attributes[] = {EGL_SURFACE_TYPE, EGL_WINDOW_BIT,
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT, EGL_RED_SIZE, 8,
        EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_NONE};
    const EGLint context_attributes[] = {EGL_CONTEXT_CLIENT_VERSION, 2, EGL_NONE};
    setvbuf(stdout, NULL, _IOLBF, 0);
    if (fd < 0) { perror("DRM open"); goto done; }
    device = gbm_create_device(fd);
    if (!device) { fprintf(stderr, "gbm_create_device failed\n"); goto done; }
    display = eglGetDisplay((EGLNativeDisplayType)device);
    if (display == EGL_NO_DISPLAY || !eglInitialize(display, &major, &minor)) {
        fprintf(stderr, "eglInitialize failed: 0x%x\n", eglGetError()); goto done;
    }
    printf("EGL_version=%d.%d vendor=%s\n", major, minor, eglQueryString(display, EGL_VENDOR));
    if (!eglBindAPI(EGL_OPENGL_ES_API) || !eglChooseConfig(display, attributes, configs, 32, &count)) goto done;
    for (int i = 0; i < count; i++) {
        EGLint visual = 0;
        if (eglGetConfigAttrib(display, configs[i], EGL_NATIVE_VISUAL_ID, &visual)
            && (unsigned)visual == GBM_FORMAT_ARGB8888) { config = configs[i]; break; }
    }
    if (!config) { fprintf(stderr, "No ARGB8888 EGL window config\n"); goto done; }
    window = gbm_surface_create(device, 64, 64, GBM_FORMAT_ARGB8888,
                                GBM_BO_USE_RENDERING | GBM_BO_USE_SCANOUT);
    if (!window) { fprintf(stderr, "GBM surface failed\n"); goto done; }
    surface = eglCreateWindowSurface(display, config, (EGLNativeWindowType)window, NULL);
    context = eglCreateContext(display, config, EGL_NO_CONTEXT, context_attributes);
    if (surface == EGL_NO_SURFACE || context == EGL_NO_CONTEXT
        || !eglMakeCurrent(display, surface, surface, context)) {
        fprintf(stderr, "EGL context/surface failed: 0x%x\n", eglGetError()); goto done;
    }
    printf("GL_vendor=%s\nGL_renderer=%s\nGL_version=%s\n",
           glGetString(GL_VENDOR), glGetString(GL_RENDERER), glGetString(GL_VERSION));
    glViewport(0, 0, 64, 64);
    glClearColor(0.125f, 0.5f, 0.75f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);
    glFinish();
    unsigned char pixel[4] = {0};
    glReadPixels(0, 0, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE, pixel);
    GLenum error = glGetError();
    printf("readback_rgba=%u,%u,%u,%u gl_error=0x%x\n", pixel[0], pixel[1], pixel[2], pixel[3], error);
    if (error != GL_NO_ERROR || abs((int)pixel[0]-32) > 1 || abs((int)pixel[1]-128) > 1
        || abs((int)pixel[2]-191) > 1 || pixel[3] != 255 || !eglSwapBuffers(display, surface)) goto done;
    result = 0;
done:
    if (display != EGL_NO_DISPLAY) {
        eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
        if (context != EGL_NO_CONTEXT) eglDestroyContext(display, context);
        if (surface != EGL_NO_SURFACE) eglDestroySurface(display, surface);
        eglTerminate(display);
    }
    if (window) gbm_surface_destroy(window);
    if (device) gbm_device_destroy(device);
    if (fd >= 0) close(fd);
    printf("EGL_CONTEXT_READBACK_EXIT_STATUS=%d; no KMS modeset performed\n", result);
    return result;
}
