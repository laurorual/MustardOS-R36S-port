/* SPDX-License-Identifier: MIT */
#include <assert.h>
#include <stdint.h>
#include <string.h>
static uint32_t ticks;static uint64_t serial;static int stopped,quit,idle_calls,repaint;static char action[64];
static void ui_common_handle_idle(void){idle_calls++;if(repaint)serial++;}
static uint64_t display_present_serial(void){return serial;}
static uint32_t lv_tick_get(void){return ticks;}
static void load_mux(const char *s){strcpy(action,s);}
static void safe_quit(int n){assert(n==0);quit++;}
static void mux_input_stop(void){stopped++;}
#include "phase4-launcher-cycle.h"
int main(void){
 const char *bad[]={"0","31","-1","+2","2x","", "999999999999999999999"};
 for(unsigned i=0;i<sizeof(bad)/sizeof(*bad);i++)assert(port_cycle_configure("dispatch",bad[i])==-1);
 assert(port_cycle_configure(NULL,NULL)==0);port_cycle_tick();assert(!stopped);
 assert(port_cycle_configure(NULL,"2")==-1);
 assert(port_cycle_configure("shutdown","2")==-1);
 assert(port_cycle_configure("dispatch",NULL)==-1);
 assert(port_cycle_configure("dispatch","2")==1);
 ticks=10000;serial=0;port_cycle_tick();assert(!stopped);
 serial=4;port_cycle_tick();assert(!stopped);
 repaint=1; ticks=11999;port_cycle_tick();assert(!stopped);
 ticks=12000;port_cycle_tick();assert(port_cycle_first_serial==4&&serial==6);assert(stopped==1&&quit==1&&!strcmp(action,"port-retro-diagnostic"));
 int before_idle=idle_calls;port_cycle_tick();assert(stopped==1 && idle_calls==before_idle+1);
 assert(port_cycle_configure("return","1")==1);
 ticks=UINT32_MAX-500;port_cycle_tick();ticks+=999;port_cycle_tick();assert(stopped==1);
 ticks++;port_cycle_tick();assert(stopped==2&&quit==2&&!strcmp(action,"port-cycle-done"));
 puts("C45_LAUNCHER_HOOK_OK invalid=11 normal_disabled=1 presentation_gate=1 deadline=1 once=1 wrap=1 return=1");
}
