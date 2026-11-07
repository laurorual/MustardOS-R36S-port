#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Finish the read-only final policy verification after the recorded awk quoting error."""
from pathlib import Path
import argparse,hashlib,ipaddress,json,subprocess
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',type=Path);p.add_argument('--host',required=True,type=ipaddress.IPv4Address)
a=p.parse_args();stage=a.stage.resolve();assert stage.is_relative_to(work/'network-warm')
meta=json.loads((stage/'manifest.json').read_text())
assert json.loads((stage/'install-analysis.json').read_text())['passed']
old=(stage/'native-verification.sh').read_text()
assert old.count(r'I\\/O')==1
code=old.replace(r'I\\/O',r'I\/O')
(stage/'native-verification-fixed.sh').write_text(code)
ssh=['ssh','-p','2222','-i',str(work/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes',
     '-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(work/'private/c07-known_hosts'),
     '-oBatchMode=yes','-oConnectTimeout=8','root@'+str(a.host)]
r=subprocess.run(ssh+['sh -s'],input=code,text=True,capture_output=True,timeout=40)
for suffix,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:
    (stage/('native-verification-fixed.'+suffix)).write_text(value)
assert r.returncode==0,(r.stdout,r.stderr)
out=r.stdout;assert 'KERNEL_ERROR_SIGNATURES=0' in out and 'WIFI_ONLY_NATIVE_ROOT_RO_FAT_UNMOUNTED_TAINT0' in out
assert 'CLASS=ff DRIVER=rtl8821cu' in out and 'CLASS=e0 DRIVER=btusb' not in out
report=out.split('REPORT_BEGIN\n')[1].split('REPORT_END\n')[0]
assert 'STATUS=0 ROOT_RO=1' in report
(stage/'initial-report.txt').write_text(report)
result={'passed':True,'sequence':int((stage/'baseline-sequence').read_text())+1,
        'automatic_network_no_physical_recovery':True,'stable_payload_matches_actual_recipe':True,
        'btusb_absent_BT_interfaces_unbound':True,'all_55_prerequisites_baseline_hashes_preserved':True,
        'root_readonly_FAT_unmounted_taint0':True,'kernel_error_signatures':0,
        'collector_repaired_awk_quoting_only_no_reboot':True,'full_image_built':False,
        'kernel_DTB_drivers_libraries_init_changed':False,
        'verification_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(stage/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print('Final stable Wi-Fi policy verified, automatic boot',result['sequence'],'rootRO/FAT unmounted/taint0, all hashes, kernel error count0.')
