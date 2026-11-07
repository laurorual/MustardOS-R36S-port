/* SPDX-License-Identifier: MIT
 * C50: distinguish a native hotkey request from internal/remote termination.
 */
#pragma once
#include <string.h>
typedef struct {
    int enabled;
    int native_hotkey;
} port_diagnostic_quit_source;
static inline void port_diagnostic_quit_configure(port_diagnostic_quit_source *s,int enabled) {
    s->enabled=!!enabled;s->native_hotkey=0;
}
static inline void port_diagnostic_quit_note(port_diagnostic_quit_source *s,const char *source) {
    s->native_hotkey=s->enabled && source && !strcmp(source,"hotkey");
}
enum port_diagnostic_exit_reason {
    port_diagnostic_exit_failure=0,
    port_diagnostic_exit_deadline,
    port_diagnostic_exit_hotkey
};
static inline enum port_diagnostic_exit_reason port_diagnostic_exit_classify(
    int allow_hotkey,int expired,int accepted_native_hotkey,unsigned long frames) {
    if(!frames)return port_diagnostic_exit_failure;
    if(expired)return port_diagnostic_exit_deadline;
    if(allow_hotkey && accepted_native_hotkey)return port_diagnostic_exit_hotkey;
    return port_diagnostic_exit_failure;
}
static inline const char *port_diagnostic_exit_name(enum port_diagnostic_exit_reason reason) {
    switch(reason) {
    case port_diagnostic_exit_deadline:return "deadline";
    case port_diagnostic_exit_hotkey:return "hotkey";
    default:return "failure";
    }
}
