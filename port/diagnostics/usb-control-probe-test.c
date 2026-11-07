// SPDX-License-Identifier: MIT
#define USB_CONTROL_TEST
#include "usb-control-probe.c"
#include <assert.h>
static unsigned calls;
static int scenario;
static int fake_control(int fd, unsigned long op, void *arg) {
    (void)fd;
    struct usbdevfs_ctrltransfer *c=arg;
    assert(op==USBDEVFS_CONTROL && c->wIndex==0 && c->timeout==500);
    assert(c->bRequestType & 0x80); /* No OUT/control write is permitted. */
    calls++;
    unsigned char *b=c->data;
    if (scenario==2 || (scenario==1 && c->bRequestType==0xc0)) {
        errno=ETIMEDOUT;return -1;
    }
    if (c->bRequest==6) {
        assert(c->bRequestType==0x80 && c->wValue==0x100 && c->wLength==18);
        memset(b,0xa5,18);
        b[0]=18;b[1]=1;b[8]=0xda;b[9]=0x0b;b[10]=0x20;b[11]=0xc8;
        if (scenario==3) b[8]=0xff;
    } else if (c->bRequestType==0xc0) {
        assert(c->bRequest==5 && c->wValue==0xfc && c->wLength==1);
        b[0]=9;
        if (scenario==4) return 0;
    } else if (c->bRequest==8) {
        assert(c->bRequestType==0x80 && !c->wValue && c->wLength==1);
        b[0]=1;
    } else {
        assert(c->bRequestType==0x80 && c->bRequest==0 && !c->wValue && c->wLength==2);
        b[0]=0;b[1]=0;
    }
    return c->wLength;
}
int main(int argc,char **argv) {
    assert(argc==2);
    scenario=atoi(argv[1]);
    assert(scenario>=0 && scenario<=4);
    (void)transport;
    assert(board_guard()==64); /* The container is never the target board. */
    int rc=run_plan(-1,"baseline",fake_control);
    assert(calls==(scenario==3 ? 1u : 7u));
    assert(rc==(scenario==3 ? 64 : 0));
    return 0;
}
