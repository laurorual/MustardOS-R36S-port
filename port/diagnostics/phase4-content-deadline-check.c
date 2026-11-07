/* SPDX-License-Identifier: MIT */
#include "startup.h"
#include <assert.h>
#include <stdio.h>
int main(void){startup_options o;unsigned n=0;
 char *ok[]={"muxretro","core.so","/tmp/flight.nes","--diagnostic-content","--diagnostic-seconds=30",NULL};
 assert(startup_options_parse(5,ok,&o)&&o.diagnostic_content&&!o.no_content&&o.fresh&&o.diagnostic_seconds==30);n++;
 const char *bad[]={"--restart","--netplay-host","--netplay-host=0","--netplay-join=example:1234","--single-screen","--subsystem=foo","--unknown"};
 for(unsigned i=0;i<7;i++){char *a[]={ok[0],ok[1],ok[2],ok[3],ok[4],(char*)bad[i],NULL};assert(!startup_options_parse(6,a,&o));n++;}
 char *none[]={ok[0],ok[1],"--no-content",ok[3],ok[4],NULL};assert(!startup_options_parse(5,none,&o));n++;
 char *no_deadline[]={ok[0],ok[1],ok[2],ok[3],NULL};assert(!startup_options_parse(4,no_deadline,&o));n++;
 char *ordinary[]={ok[0],ok[1],ok[2],NULL};assert(startup_options_parse(3,ordinary,&o)&&!o.diagnostic_content&&!o.diagnostic_seconds);n++;
 printf("C47_CONTENT_PARSER_OK cases=%u\n",n);return 0;}
