#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C91 read-only first-boot qualification after independently verified C89."""
from pathlib import Path
import argparse,importlib,ipaddress,json,os,re,subprocess,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_candidate import sums
from phase4_root_migration import require
import phase4_root_recovery as recovery
import phase4_installed_core_session as installed

REPO=Path(__file__).resolve().parents[2];WORK=REPO/'build/phase4';AREA=WORK/'recovery-boot'

def render(common,expected,stable,old_seeds):
    require(type(expected) is int and 2<=expected<=9999,'Expected first recovery boot counter')
    require(set(stable)<=recovery.STABLE and set(stable),'Known stable identity required')
    for h in old_seeds:recovery.digest(h)
    code=common+f'''[ "$(cat /var/lib/muos-diagnostic/boot-seq)" = {expected} ]
for name in /var/lib/muos-network /var/lib/muos-seedrng /var/lib/muos-diagnostic;do
 [ ! -L "$name" ] && [ "$(stat -c '%u:%g:%a' "$name")" = 0:0:700 ]
done
[ -z "$(find /var/lib/muos-diagnostic -name '*.once' -print)" ]
[ "$(cat /proc/asound/card0/pcm0p/sub0/status)" = closed ]
[ "$(cat /run/muos/entropy/mode)" = seedless ]
grep -qx 'Seeding 2048 bits without crediting' /run/muos/entropy/start.log
if grep -Eq '^Seeding [0-9]+ bits and crediting$' /run/muos/entropy/start.log;then exit 64;fi
grep -Eq '^Saving [0-9]+ bits of creditable seed for next boot$' /run/muos/entropy/start.log
grep -Eq '^Saving [0-9]+ bits of creditable seed for next boot$' /run/muos/entropy/stop.log
grep -Eq '^rng_ready=1 wait_ms=[0-9]+$' /run/muos/entropy/after.txt
grep -Eq '^rng_ready=1 wait_ms=[0-9]+$' /run/muos/entropy/stop-ready.txt
[ -f /run/muos/entropy/stopped ] && [ ! -e /run/muos/entropy/ready ]
[ ! -e /var/lib/muos-seedrng/seed.no-credit ] && [ ! -L /var/lib/muos-seedrng/seed.no-credit ]
credit=/var/lib/muos-seedrng/seed.credit
[ -f "$credit" ] && [ ! -L "$credit" ]
[ "$(stat -c '%u:%g:%a:%h' "$credit")" = 0:0:400:1 ]
bytes=$(stat -c %s "$credit");[ "$bytes" -ge 32 ] && [ "$bytes" -le 256 ]
credit_hash=$(sha256sum "$credit" | cut -d' ' -f1)
'''
    for h in old_seeds:code+=f'[ "$credit_hash" != {h} ]\n'
    for name,row in sorted(stable.items()):
        require(re.fullmatch(r'[a-zA-Z0-9_./-]+',name) and '..' not in Path(name).parts,'Stable identity path')
        recovery.digest(row['sha256'])
        code+=f'''[ -f /{name} ] && [ ! -L /{name} ]
[ "$(stat -c '%u:%g:%a:%h:%s' /{name})" = 0:0:{row['mode']:o}:1:{row['bytes']} ]
[ "$(sha256sum /{name} | cut -d' ' -f1)" = {row['sha256']} ]
'''
    return code+f'''printf 'boot_sequence|{expected}\\n'
printf 'boot_id|';cat /proc/sys/kernel/random/boot_id
printf 'credit_bytes|%s\\n' "$bytes"
printf 'no_credit_consumed_without_credit|1\\n'
'''

def decoded(text,expected):
    rows={}
    for line in text.splitlines():
        fields=line.split('|');require(len(fields)==2 and fields[0] not in rows,'Unexpected/duplicate boot evidence')
        rows[fields[0]]=fields[1]
    require(set(rows)=={'boot_sequence','boot_id','credit_bytes','no_credit_consumed_without_credit'},'Boot evidence schema')
    require(rows['boot_sequence']==str(expected) and re.fullmatch('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',rows['boot_id']),
        'First-boot counter/ID mismatch')
    require(rows['credit_bytes'].isdigit() and 32<=int(rows['credit_bytes'])<=256
        and rows['no_credit_consumed_without_credit']=='1','Seed rotation evidence incomplete')
    return rows

def main(host):
    os.umask(0o077);host=str(ipaddress.IPv4Address(host));AREA.mkdir(exist_ok=True)
    tests=Path((AREA/'latest-checks').read_text().strip());require(tests.resolve().is_relative_to(AREA),'Boot checks location')
    checks=json.loads((tests/'analysis.json').read_text());require(checks['passed'] is True,'Boot qualification checks required')
    for n,h in checks['source_sha256'].items():require(sha(REPO/n)==h,'Tested boot collector source changed')
    collector=importlib.import_module('collect-phase4-p2-recovery');prep=collector.prep
    record=prep.prep.prep.latest(prep.AREA,'latest-complete-recover');ack=json.loads((record/'host-copy.json').read_text())
    require(ack['passed'] is True and ack['physical_p2_recovery_verified'] is True and
        ack['new_fence_independent_host_copy_verified'] is True,'Collected physical recovery required before SSH')
    for n,h in ack['files'].items():require(sha(record/n)==h,'Recovery evidence changed')
    proof=REPO/'dist/phase4/p2-recovery-native'
    for n,h in sums(proof/'SHA256SUMS').items():require(sha(proof/n)==h,'Native proof changed')
    package=prep.prep.prep.latest(prep.AREA,'latest-package-recover');bundle=package/'bundle'
    require(sha(bundle/'package.json')==ack['package_manifest_sha256'],'Recovered package binding')
    ctx=json.loads((bundle/'context.json').read_text());manifest=json.loads((bundle/'package.json').read_text())
    report=json.loads((record/'analysis.json').read_text())
    intent=recovery.load_attempt(record/'handoff',ack['next_attempt_id'],ack['next_attempt_sha256'])
    journal={n:json.loads((record/'write-journal'/f'{n}.json').read_text()) for n in ['unlock-intent','write-intent','complete']}
    collector.validate(report,ctx,manifest,journal,intent)
    expected=intent['counter_floor']+1
    composed=Path(json.loads((package/'analysis.json').read_text())['C85_composition'])
    require(composed.resolve().is_relative_to(WORK/'recovery-image'),'Known composition')
    plan=json.loads((composed/'plan.json').read_text());require(plan['recovery_counter']==intent['counter_floor'],'Seed/counter plan binding')
    stable={n:row for n,row in ctx['physical_capture']['backup_private_files'].items() if n in recovery.STABLE}
    common=installed.current_common('',intent['counter_floor'],expected)
    code=render(common,expected,stable,plan['old_seed_sha256'])
    stage=Path(tempfile.mkdtemp(prefix='collect.',dir=AREA));write_new(stage/'checks.sh',code.encode())
    write_new(stage/'binding.json',recovery.encoded({'host':host,'recovery_host_copy':str(record),
        'recovery_host_copy_sha256':sha(record/'host-copy.json'),'next_attempt_id':ack['next_attempt_id'],
        'next_attempt_sha256':ack['next_attempt_sha256'],'expected_counter':expected}))
    (AREA/'latest-attempt').write_text(str(stage)+'\n')
    ssh=['ssh','-p','2222','-i',str(WORK/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes',
        '-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(WORK/'private/c07-known_hosts'),
        '-oBatchMode=yes','-oConnectTimeout=8','root@'+host,'sh -s']
    result=subprocess.run(ssh,input=code.encode(),capture_output=True,timeout=60)
    for n,data in [('stdout',result.stdout),('stderr',result.stderr),('exit',(str(result.returncode)+'\n').encode())]:write_new(stage/n,data)
    require(result.returncode==0,'Boot qualification failed; inspect private evidence, do not reboot or rewrite automatically')
    observed=decoded(result.stdout.decode(),expected)
    analysis={'passed':True,'schema':91,'experiment':'C91_FIRST_BOOT_AFTER_NATIVE_P2_RECOVERY',
        'boot_sequence':expected,'kernel_boot_id':observed['boot_id'],'stable_identity_files_verified':len(stable),
        'C76_installed_files_and_C07_ready_verified':True,'first_boot_from_recovery_counter_verified':True,
        'entropy_seedless_path_verified':True,'no_credit_2048bits_consumed_without_crediting':True,
        'rng_ready_and_new_creditable_seed_saved_and_old_seed_hashes_absent':True,
        'root_readonly_mode0755_and_p3_unmounted_and_PCM_closed':True,'active_once_absent':True,
        'physical_boot_after_recovery_qualified':True,'device_written_or_rebooted_by_collector':False,
        'C79_migration_authorized':False,'recovery_host_copy_sha256':sha(record/'host-copy.json'),
        'checks_sha256':sha(tests/'analysis.json'),'source_sha256':checks['source_sha256']}
    write_new(stage/'analysis.json',recovery.encoded(analysis));sync_dir(stage)
    (AREA/'latest-complete').write_text(str(stage)+'\n');sync_dir(AREA)
    print('C91 first recovery boot qualified:',stage,'boot',expected)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True);main(p.parse_args().host)
