# SPDX-License-Identifier: MIT
# Numeric status only; no input line, identifiers, or register data emitted.
NR==1 {s=$0;sub(/^\[/,"",s);sub(/\].*$/,"",s);if(s ~ /^[ 0-9.]+$/)printf "BUFFER_FIRST_TIMESTAMP=%.3f\n",s+0}
/halmac_init_adapter fail!\(status=[0-9]+\)/ {s=$0;sub(/^.*halmac_init_adapter fail!\(status=/,"",s);sub(/\).*$/,"",s);if(s ~ /^[0-9]+$/ && s+0<65536)printf "HALMAC_INIT_STATUS=%d\n",s+0}
/reg 0xfc, usb read 1 fail, status:/ {s=$0;sub(/^.*status:/,"",s);sub(/ .*/,"",s);if(s ~ /^-?[0-9]+$/ && s+0>=-4095 && s+0<=65535)printf "CHIP_ID_READ_USB_STATUS=%d\n",s+0}
/reg 0xf1, usb read 1 fail, status:/ {s=$0;sub(/^.*status:/,"",s);sub(/ .*/,"",s);if(s ~ /^-?[0-9]+$/ && s+0>=-4095 && s+0<=65535)printf "CHIP_VERSION_READ_USB_STATUS=%d\n",s+0}
/Chip id is undefined/ {undefined++}
END {printf "CHIP_ID_UNDEFINED_COUNT=%d\n",undefined}
