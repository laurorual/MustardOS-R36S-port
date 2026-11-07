# SPDX-License-Identifier: MIT
"""C16 public parser and explicit observation actions. Never collect raw USB data."""
import json,re
from pathlib import Path

ORDER=['descriptor','configuration','status','chip_id','descriptor_after','configuration_after','status_after']
def parse_report(text,phase):
    if not text.strip():return {'complete':False,'no_output':True,'reads':{}}
    lines=text.splitlines()
    assert lines[:2]==['MUOS-C16-USB-CONTROL-V1','PHASE='+phase],lines[:2]
    reads={}
    for line in lines[2:]:
        if line.startswith('READ_FAILURES='):
            assert re.fullmatch(r'READ_FAILURES=[0-9]+',line)
            continue
        m=re.fullmatch(r'READ=([a-z_]+) RC=(-?[0-9]+) EXPECTED=([0-9]+) ELAPSED_MS=([0-9]+) MATCH=(-1|0|1)',line)
        assert m and m[1] not in reads,line
        reads[m[1]]={'rc':int(m[2]),'expected':int(m[3]),'elapsed_ms':int(m[4]),'match':int(m[5])}
    assert list(reads)==ORDER[:len(reads)]
    return {'complete':list(reads)==ORDER,'reads':reads}

def observer_actions(action,stage,meta,guard,remote):
    if action=='baseline':
        seq=int((stage/'baseline-sequence').read_text())
        code=guard('installed_after')+f'''
[ "$(cat /var/lib/muos-diagnostic/boot-seq)" = {seq} ]
[ ! -e /run/muos/c07/c16-baseline.txt ] && [ ! -L /run/muos/c07/c16-baseline.txt ]
set +e
/usr/libexec/muos-run-bounded 10 /usr/libexec/muos-c16/usb-control-probe baseline > /run/muos/c07/c16-baseline.txt 2>/run/muos/c07/c16-baseline.stderr
probe_rc=$?
set -e
echo BASELINE_BEGIN
cat /run/muos/c07/c16-baseline.txt
echo BASELINE_END
echo BASELINE_PROBE_RC=$probe_rc
# Save only the fixed public read report. Existing C07 archive must match.
trap 'umount /boot' EXIT
mount -t vfat -o ro,nosuid,nodev,noexec "$boot_partition" /boot
[ "$(cat /boot/DIAG.ID)" = MUOS-R35S-EXT4-P4-B01 ]
destination=/boot/DIAG09/BOOT{seq:04d}
[ -f "$destination/REPORT.TXT" ]
[ ! -e "$destination/C16PRE.TXT" ] && [ ! -e "$destination/C16PRE.TMP" ]
mount -o remount,rw,nosuid,nodev,noexec /boot
cp /run/muos/c07/c16-baseline.txt "$destination/C16PRE.TMP"
mv "$destination/C16PRE.TMP" "$destination/C16PRE.TXT"
sync
cmp /run/muos/c07/c16-baseline.txt "$destination/C16PRE.TXT"
umount /boot;trap - EXIT
c12_guard;c12_root_ro
set +e
/usr/libexec/muos-c07-network status
network_rc=$?
set -e
echo NETWORK_STATUS_AFTER=$network_rc
'''
        out=remote('baseline-read',code,timeout=40)
        value=out.split('BASELINE_BEGIN\n')[1].split('BASELINE_END\n')[0]
        (stage/'baseline.txt').write_text(value)
        parsed=parse_report(value,'baseline')
        passed=parsed['complete'] and all(v['match']==1 and v['rc']==v['expected'] for v in parsed['reads'].values()) and 'BASELINE_PROBE_RC=0' in out and 'NETWORK_STATUS_AFTER=0' in out
        (stage/'baseline-analysis.json').write_text(json.dumps({'passed':passed,'sequence':seq,'reads':parsed,'FAT_saved_readback_unmounted':True},indent=2)+'\n')
        print(value,end='');assert passed,'Baseline read failed: do not reboot; inspect and restore the trial'
        return
    assert action=='collect'
    seq=int((stage/'baseline-sequence').read_text())+1
    code=guard('installed_after')+f'''
[ "$(cat /var/lib/muos-diagnostic/boot-seq)" = {seq} ]
[ ! -e /var/lib/muos-diagnostic/c16.once ]
[ "$(cat /var/lib/muos-diagnostic/c16.used)" = MUOS-C16-ONCE ]
for phase in before after;do
echo PROBE_BEGIN=$phase
[ ! -f /run/muos/c07/control-probe/$phase.txt ] || cat /run/muos/c07/control-probe/$phase.txt
echo PROBE_END=$phase
done
echo REPORT_BEGIN
cat /run/muos/c07/report.txt
echo REPORT_END
echo RECOVERY_BEGIN
if [ -f /run/muos/c07/recovery.txt ];then cat /run/muos/c07/recovery.txt;fi
echo RECOVERY_END
echo REPLUG_BEGIN
if [ -f /run/muos/c07/recovery.txt ] && grep -q '^RECOVERY=physical-removal-observed$' /run/muos/c07/recovery.txt;then
 /usr/libexec/muos-run-bounded 10 /usr/libexec/muos-c16/usb-control-probe replug
fi
echo REPLUG_END
trap 'umount /boot' EXIT
mount -t vfat -o ro,nosuid,nodev,noexec "$boot_partition" /boot
[ "$(cat /boot/DIAG.ID)" = MUOS-R35S-EXT4-P4-B01 ]
cmp /run/muos/c07/report.txt /boot/DIAG09/BOOT{seq:04d}/REPORT.TXT
echo BASELINE_FAT_BEGIN
cat /boot/DIAG09/BOOT{seq-1:04d}/C16PRE.TXT
echo BASELINE_FAT_END
umount /boot;trap - EXIT
c12_guard;c12_root_ro
echo C16_ALL_PUBLIC_REPORTS_DURABLE_ROOT_RO
'''
    out=remote('collection',code,timeout=45)
    values={}
    for label in ['before','after']:
        value=out.split('PROBE_BEGIN='+label+'\n')[1].split('PROBE_END='+label+'\n')[0]
        values[label]=value;(stage/(label+'.txt')).write_text(value)
    for label,marker in [('initial-report','REPORT'),('recovery','RECOVERY'),('replug','REPLUG'),('baseline-fat','BASELINE_FAT')]:
        value=out.split(marker+'_BEGIN\n')[1].split(marker+'_END\n')[0]
        values[label]=value;(stage/(label+'.txt')).write_text(value)
    assert values['baseline-fat']==(stage/'baseline.txt').read_text()
    parsed={k:parse_report(values[k],phase) for k,phase in [('before','retained-pre'),('after','retained-post'),('replug','replug')]}
    result={'collected':True,'sequence':seq,'observations':parsed,'baseline_survived_reboot':True,
            'failed_boot_report_matches_FAT':True,'root_readonly_FAT_unmounted_taint0':True,
            'new_recovery_operation_added':False,'raw_payload_dmesg_or_private_material_collected':False}
    (stage/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(parsed,indent=2))
