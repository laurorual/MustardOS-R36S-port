/* SPDX-License-Identifier: MIT */
#include <assert.h>
#include <stdio.h>
#include "startup.h"
int main(void) {
    unsigned cases = 0;
    startup_options options;
    const char *good[] = {"--diagnostic-seconds=1", "--diagnostic-seconds=45", "--diagnostic-seconds=60"};
    const unsigned expected[] = {1,45,60};
    for (unsigned i=0;i<3;++i) {
        char *argv[]={"muxretro","core.so","--no-content",(char *)good[i],NULL};
        assert(startup_options_parse(4,argv,&options) && options.diagnostic_seconds==expected[i]);++cases;
    }
    const char *bad[]={"--diagnostic-seconds=0","--diagnostic-seconds=61","--diagnostic-seconds=-1",
        "--diagnostic-seconds=+2","--diagnostic-seconds=","--diagnostic-seconds=5junk"};
    for(unsigned i=0;i<6;++i) {
        char *argv[]={"muxretro","core.so","--no-content",(char *)bad[i],NULL};
        assert(!startup_options_parse(4,argv,&options));++cases;
    }
    char *legacy[]={"muxretro","core.so","game.rom","--diagnostic-seconds=1",NULL};
    assert(!startup_options_parse(4,legacy,&options));++cases;
    char *normal[]={"muxretro","core.so","--no-content",NULL};
    assert(startup_options_parse(3,normal,&options) && !options.diagnostic_seconds);++cases;
    printf("C44_DEADLINE_CASES_OK=%u\n",cases);return 0;
}
