/* SPDX-License-Identifier: MIT */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "startup.h"
#include "phase4-diagnostic-exit.h"
int main(void) {
    startup_options o;unsigned parser=0,policy=0;
    char *ok[]={"muxretro","core.so","private.gb","--diagnostic-content","--diagnostic-seconds=45","--diagnostic-hotkey-exit",NULL};
    assert(startup_options_parse(6,ok,&o) && o.diagnostic_hotkey_exit && o.diagnostic_content && o.fresh && o.diagnostic_seconds==45);parser++;
    char *reordered[]={ok[0],ok[1],ok[2],ok[5],"--diagnostic-seconds=60",ok[3],NULL};
    assert(startup_options_parse(6,reordered,&o) && o.diagnostic_hotkey_exit && o.diagnostic_seconds==60);parser++;
    char *without_content[]={ok[0],ok[1],ok[2],ok[4],ok[5],NULL};
    assert(!startup_options_parse(5,without_content,&o));parser++;
    char *without_deadline[]={ok[0],ok[1],ok[2],ok[3],ok[5],NULL};
    assert(!startup_options_parse(5,without_deadline,&o));parser++;
    char *none[]={ok[0],ok[1],"--no-content",ok[3],ok[4],ok[5],NULL};
    assert(!startup_options_parse(6,none,&o));parser++;
    const char *bad[]={"--restart","--netplay-host","--netplay-join=example:1234","--single-screen","--subsystem=foo"};
    for(unsigned i=0;i<5;i++) {
        char *a[]={ok[0],ok[1],ok[2],ok[3],ok[4],ok[5],(char *)bad[i],NULL};
        assert(!startup_options_parse(7,a,&o));parser++;
    }
    assert(startup_options_parse(5,ok,&o) && !o.diagnostic_hotkey_exit);parser++;
    char *ordinary[]={ok[0],ok[1],ok[2],ok[5],NULL};
    assert(!startup_options_parse(4,ordinary,&o));parser++;
    const struct {int allow,expired,hotkey;unsigned long frames;enum port_diagnostic_exit_reason want;} cases[]={
        {0,0,0,1,port_diagnostic_exit_failure},{0,0,1,1,port_diagnostic_exit_failure},
        {1,0,0,1,port_diagnostic_exit_failure},{1,0,1,1,port_diagnostic_exit_hotkey},
        {0,1,0,1,port_diagnostic_exit_deadline},{0,1,1,1,port_diagnostic_exit_deadline},
        {1,1,0,1,port_diagnostic_exit_deadline},{1,1,1,1,port_diagnostic_exit_deadline},
        {0,0,0,0,port_diagnostic_exit_failure},{0,0,1,0,port_diagnostic_exit_failure},
        {1,0,0,0,port_diagnostic_exit_failure},{1,0,1,0,port_diagnostic_exit_failure},
        {0,1,0,0,port_diagnostic_exit_failure},{0,1,1,0,port_diagnostic_exit_failure},
        {1,1,0,0,port_diagnostic_exit_failure},{1,1,1,0,port_diagnostic_exit_failure}};
    for(unsigned i=0;i<sizeof(cases)/sizeof(cases[0]);i++) {
        assert(port_diagnostic_exit_classify(cases[i].allow,cases[i].expired,cases[i].hotkey,cases[i].frames)==cases[i].want);policy++;
    }
    port_diagnostic_quit_source source;
    port_diagnostic_quit_configure(&source,0);port_diagnostic_quit_note(&source,"hotkey");assert(!source.native_hotkey);policy++;
    port_diagnostic_quit_configure(&source,1);
    const char *rejected[]={"internal","remote",NULL,"Hotkey","hotkey-extra"};
    for(unsigned i=0;i<5;i++){port_diagnostic_quit_note(&source,rejected[i]);assert(!source.native_hotkey);policy++;}
    port_diagnostic_quit_note(&source,"hotkey");assert(source.native_hotkey);policy++;
    port_diagnostic_quit_note(&source,"remote");assert(!source.native_hotkey);policy++;
    port_diagnostic_quit_note(&source,"hotkey");port_diagnostic_quit_configure(&source,0);assert(!source.native_hotkey);policy++;
    assert(!strcmp(port_diagnostic_exit_name(port_diagnostic_exit_hotkey),"hotkey"));policy++;
    printf("C50_EXIT_CHECK_OK parser=%u policy=%u\n",parser,policy);
    return 0;
}
