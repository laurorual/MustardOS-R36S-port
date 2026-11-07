# SPDX-License-Identifier: MIT
# Never emit input text, network identifiers, register/efuse dumps or raw logs.
function event(label, t, prefix) {
    t=0
    if (match($0, /^\[[ 0-9.]+\]/)) {
        prefix=substr($0,RSTART,RLENGTH)
        gsub(/[^0-9.]/,"",prefix); t=prefix+0
    }
    if (!counts[label]) first[label]=t
    counts[label]++; last[label]=t
}
BEGIN {
    n=split("module_start module_ready chip_version chip_info primary_fail halmac_init_fail halmac_tuning_fail halmac_phy_fail halmac_ops_fail efuse_invalid efuse_empty hidden_report_fail power_fail firmware_fail vendor_io_fail transport_fail netdev_fail driver_fail_any",labels," ")
}
/RTW:.*module init start/ {event("module_start")}
/RTW:.*module init ret=0/ {event("module_ready")}
/Chip Version Info/ {event("chip_version")}
/rtw_hal_read_chip_info in/ {event("chip_info")}
/rtw_usb_primary_adapter_init Failed/ {event("primary_fail")}
/halmac_init_adapter fail/ {event("halmac_init_fail")}
/halmac_interface_integration_tuning fail/ {event("halmac_tuning_fail")}
/halmac_phy_cfg fail/ {event("halmac_phy_fail")}
/HALMAC initialize FAIL/ {event("halmac_ops_fail")}
/EEPROM ID is invalid/ {event("efuse_invalid")}
/Empty EFUSE with unknown REF type/ {event("efuse_empty")}
/hal_read_mac_hidden_rpt.*(fail|Fail|FAIL|timeout)/ {event("hidden_report_fail")}
/Power ON Fail|rtw_hal_power_on.*fail/ {event("power_fail")}
/Download Firmware.*failed/ {event("firmware_fail")}
/usbctrl_vendorreq.*(fail|status)/ {event("vendor_io_fail")}
/error -71|error -110|error -32|error -19/ {event("transport_fail")}
/register_netdev.*(fail|error)|rtw_os_ndev.*(fail|error)/ {event("netdev_fail")}
/RTW:.*(fail|Fail|FAIL|error|ERROR|timeout)/ {event("driver_fail_any")}
END {
    print "MUOS-C13-DRIVER-EVENTS-V1"
    for (i=1;i<=n;i++) {
        label=labels[i]
        printf "EVENT=%s COUNT=%d FIRST=%.3f LAST=%.3f\n",label,counts[label],first[label],last[label]
    }
}
