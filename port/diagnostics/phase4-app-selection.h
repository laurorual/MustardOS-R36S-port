/* SPDX-License-Identifier: MIT */
#ifndef PHASE4_APP_SELECTION_H
#define PHASE4_APP_SELECTION_H
#include <stdint.h>
#include <stdio.h>
#include <string.h>
static int port_app_diagnostic,port_app_painted,port_app_finished;
static uint32_t port_app_started;
static int port_app_configure(const char *value) {
    port_app_diagnostic=port_app_painted=port_app_finished=0;
    if (!value) return 0;
    if (strcmp(value,"1")) return -1;
    return port_app_diagnostic=1;
}
static void port_app_leave(const char *action) {
    if (!port_app_diagnostic || port_app_finished) return;
    load_mux(action);safe_quit(0);mux_input_stop();port_app_finished=1;
    printf("C46_APP_LEAVE action=%s\n",action);fflush(stdout);
}
static void port_app_cancel(void) {port_app_leave("port-app-cancel");}
static void port_app_idle(void) {
    ui_common_handle_idle();
    if (!port_app_diagnostic || port_app_finished || !display_present_serial()) return;
    if (!port_app_painted) {
        port_app_painted=1;port_app_started=lv_tick_get();
        printf("C46_APP_PRESENT serial=%llu\n",(unsigned long long)display_present_serial());fflush(stdout);
    }
    if ((uint32_t)(lv_tick_get()-port_app_started)>=120000U) port_app_leave("port-app-timeout");
}
#endif
