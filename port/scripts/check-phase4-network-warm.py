#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check the public driver classifier using the actual AArch64 BusyBox awk."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,tempfile

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
area=work/'network-warm';area.mkdir(exist_ok=True)
stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area))
source=repo/'port/device/rk-r35s-p0/network-warm-diagnostic/driver-events.awk'
shutil.copyfile(source,stage/'driver-events.awk')
root=work/'linux-diagnostic/network-recovery.zz7sq2ve/extracted'
rel=lambda p:'/work/'+str(p.relative_to(work))
command=['podman','run','--rm','-i','--network=none','--read-only','--cap-drop=all',
         '--security-opt=no-new-privileges','--userns=keep-id','-v',f'{work}:/work:ro,z',
         (work/'rootfs-container.iid').read_text().strip(),'qemu-aarch64','-cpu','cortex-a35',
         '-L',rel(root),rel(root/'bin/busybox'),'awk','-f',rel(stage/'driver-events.awk')]
cases={
    'private-input-not-exported':('SSID=PRIVATE_WIFI\nPSK=PRIVATE_SECRET\nMAC=11:22:33:44:55:66\n',{}),
    'warm-failure-with-private-suffix':('[ 12.125] RTW: rtw_usb_primary_adapter_init Failed! PRIVATE_SECRET\n[ 14.500] RTW: rtw_usb_primary_adapter_init Failed! SSID=PRIVATE_WIFI\n',{'primary_fail':(2,12.125,14.5),'driver_fail_any':(2,12.125,14.5)}),
    'halmac-versus-efuse':('[ 8.0] RTW: halmac_init_adapter fail!(status=5)\n[ 9.0] RTW: HALMAC initialize FAIL!\n[ 10.0] RTW: EEPROM ID is invalid!!\n',{'halmac_init_fail':(1,8,8),'halmac_ops_fail':(1,9,9),'efuse_invalid':(1,10,10)}),
    'untimestamped-input':('RTW: Power ON Fail!! MAC=11:22:33:44:55:66\n',{'power_fail':(1,0,0)}),
    'successful-checkpoints':('[ 1.0] RTW: module init start\n[ 2.0] RTW: module init ret=0\n[ 3.0] Chip Version Info SECRET\n[ 4.0] RTW: rtw_hal_read_chip_info in 10 ms\n',{'module_start':(1,1,1),'module_ready':(1,2,2),'chip_version':(1,3,3),'chip_info':(1,4,4)}),
}
for label,(data,expected) in cases.items():
    r=subprocess.run(command,input=data,text=True,capture_output=True,timeout=15)
    assert r.returncode==0,r.stderr
    lines=r.stdout.splitlines();assert lines[0]=='MUOS-C13-DRIVER-EVENTS-V1' and len(lines)==19
    values={}
    for line in lines[1:]:
        m=re.fullmatch(r'EVENT=([a-z_]+) COUNT=([0-9]+) FIRST=([0-9]+\.[0-9]{3}) LAST=([0-9]+\.[0-9]{3})',line);assert m,line
        values[m[1]]=(int(m[2]),float(m[3]),float(m[4]))
    for key,value in expected.items():assert values[key]==value,(label,key,values[key])
    assert not any(s in r.stdout for s in ['PRIVATE','SSID','PSK','MAC=','SECRET','11:22:33'])
    if not expected:assert all(v==(0,0,0) for v in values.values())
    (stage/(label+'.stdout')).write_text(r.stdout)
report={'passed':True,'cases':list(cases),'actual_AArch64_BusyBox_awk':True,
        'classifier_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'raw_device_log_collected':False,'real_network_or_device_changed':False}
(stage/'report.json').write_text(json.dumps(report,indent=2)+'\n')
(area/'latest-checks').write_text(str(stage)+'\n')
print('C13 public driver classifier: 5 AArch64 cases passed;',stage)
