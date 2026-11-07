/* SPDX-License-Identifier: MIT
 * Mandatory GBM entry points in SDL 2.30.12 SDL_kmsdrmsym.h.
 * Compile/link/relocation contract only; no function is called on a GPU.
 */
#include <gbm.h>
#include <stdio.h>

static void *volatile required[] = {
    (void *)gbm_device_is_format_supported, (void *)gbm_device_destroy,
    (void *)gbm_create_device, (void *)gbm_bo_get_width,
    (void *)gbm_bo_get_height, (void *)gbm_bo_get_stride,
    (void *)gbm_bo_get_format, (void *)gbm_bo_get_handle,
    (void *)gbm_bo_write, (void *)gbm_bo_get_device,
    (void *)gbm_bo_set_user_data, (void *)gbm_bo_get_user_data,
    (void *)gbm_bo_destroy, (void *)gbm_bo_create,
    (void *)gbm_surface_create, (void *)gbm_surface_destroy,
    (void *)gbm_surface_lock_front_buffer, (void *)gbm_surface_release_buffer,
};

_Static_assert(sizeof(((union gbm_bo_handle *)0)->u32) == 4, "GBM handle u32");

int main(void) {
    const unsigned format = GBM_FORMAT_ARGB8888;
    const unsigned usage = GBM_BO_USE_SCANOUT | GBM_BO_USE_RENDERING;
    for (unsigned i = 0; i < sizeof(required) / sizeof(required[0]); ++i)
        if (!required[i]) return 1;
    printf("GBM_REQUIRED_API=18 present; format=0x%x usage=0x%x; GPU runtime untested\n", format, usage);
    return 0;
}
