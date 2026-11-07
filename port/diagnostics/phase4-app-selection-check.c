/* SPDX-License-Identifier: MIT */
#include <assert.h>
#include <stdint.h>
static unsigned idle;static uint32_t ticks;static uint64_t serial;static int stops,quits;static char action[64];
static void ui_common_handle_idle(void){idle++;}
static uint32_t lv_tick_get(void){return ticks;}
static uint64_t display_present_serial(void){return serial;}
#include <string.h>
static void load_mux(const char *s){strcpy(action,s);}
static void safe_quit(int n){assert(!n);quits++;}
static void mux_input_stop(void){stops++;}
#include "phase4-app-selection.h"
int main(void){
 assert(port_app_configure(0)==0);port_app_idle();assert(idle==1&&!stops);
 assert(port_app_configure("0")==-1);assert(port_app_configure("yes")==-1);
 assert(port_app_configure("1")==1);ticks=200000;serial=0;port_app_idle();assert(!stops);
 serial=7;port_app_idle();assert(port_app_painted&&!stops);
 ticks+=119999;port_app_idle();assert(!stops);ticks++;port_app_idle();assert(stops==1&&!strcmp(action,"port-app-timeout"));
 port_app_cancel();assert(stops==1&&quits==1);
 assert(port_app_configure("1")==1);port_app_cancel();assert(stops==2&&!strcmp(action,"port-app-cancel"));
 assert(port_app_configure("1")==1);ticks=UINT32_MAX-99;port_app_idle();ticks+=120000;port_app_idle();assert(stops==3);
 puts("C46_APP_HOOK_OK disabled invalid presentation deadline once cancel wrap idle_delegate");
}
