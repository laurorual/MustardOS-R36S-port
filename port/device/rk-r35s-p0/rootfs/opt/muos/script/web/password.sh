#!/bin/sh
# SPDX-License-Identifier: MIT
# Port adapter for upstream script/web/password.sh: muxnetprofile already stores
# the PSK (derive_psk); the worker writes the wpa_supplicant config from the
# profiles at connect time, so there is nothing to do here.
exit 0
