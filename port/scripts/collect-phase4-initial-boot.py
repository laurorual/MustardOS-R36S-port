#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C97 read-only first C79 boot qualification, after independently collected C94.

Reuses only C91's render/decoder; its unqualified recovery main is never called.
The C76 guard is allowed only after matching every pinned file to C79's tree.
"""
from pathlib import Path
import argparse,importlib,ipaddress,json,os,re,subprocess,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_root_migration import require
from phase4_candidate import sums
import phase4_root_recovery as recovery
import phase4_installed_core_session as installed

collector=importlib.import_module('collect-phase4-p2-initial');prep=collector.prep
entropy=importlib.import_module('collect-phase4-recovery-boot')
REPO=prep.REPO;WORK=prep.WORK;AREA=WORK/'initial-boot'

def matched_common(common,tree):
    rows=re.findall(r"printf '[^']+' ([0-9a-f]{64}) /([A-Za-z0-9_./+-]+) \| sha256sum -c - >/dev/null",common)
    require(len(rows)==141 and len({n for _,n in rows})==141,'Complete unique reviewed C76 guard inventory')
    extra='';public_count=0
    for digest,name in rows:
        require('..' not in Path(name).parts and name in tree,'Guard path missing from C79')
        row=tree[name]
        require(row['type']=='regular' and row['sha256']==digest and row['uid']==row['gid']==0 and
            row['links']==1 and type(row['mode']) is int and
            (row['mode']==0o4755 if name=='bin/busybox' else row['mode'] in (0o644,0o755)) and
            type(row['bytes']) is int and row['bytes']>0,'C76 guard must match C79 bytes and safe metadata')
        extra+=f'''[ -f /{name} ] && [ ! -L /{name} ]
[ "$(stat -c '%u:%g:%a:%h:%s' /{name})" = 0:0:{row['mode']:o}:1:{row['bytes']} ]
'''
        if name not in recovery.PRIVATE_FILES|recovery.OPTIONAL_PRIVATE:public_count+=1
    require(public_count==140,'Guard public/identity split changed')
    basics='''[ "$(stat -c '%u:%g:%a' /)" = 0:0:755 ]
awk '$2=="/" { n++; if ($3=="ext4" && ("," $4 ",") ~ /,ro,/) ok++ } END { exit !(n==1 && ok==1) }' /proc/mounts
[ -z "$(awk '$1 ~ /mmcblk0p[13]$/ { print }' /proc/mounts)" ]
[ -z "$(ps | sed -n '/[m]uxlaunch\\|[m]uxretro\\|[r]etroarch\\|[m]uos-ui-supervisor/p')" ]
[ -z "$(awk '$1 ~ /^(bluetooth|btusb|btrtl|btbcm|btintel|hci_uart)$/ { print }' /proc/modules)" ]
'''
    return common+extra+basics,{'guard_file_count':141,'C79_public_file_count':public_count,'stable_identity_guard_file_count':1}

def lineage():
    require((prep.AREA/'latest-complete').is_file(),'C94 must complete and its next fence be independently collected before SSH')
    stage=prep.initial.latest(prep.AREA,'latest-complete');ack=json.loads((stage/'host-copy.json').read_text())
    for n in ['passed','physical_initial_p2_migration_verified','new_fence_independent_host_copy_verified',
        'all_receipts_and_directory_fsynced','all_card_aliases_RO_and_automount_guard_verified']:require(ack[n] is True,'Independent native C94 collection required')
    for n,h in ack['files'].items():require(sha(stage/n)==h,'Native initial evidence changed')
    root=REPO/'dist/phase4/p2-initial-native'
    for n,h in sums(root/'SHA256SUMS').items():require(sha(root/n)==h,'Native initial proof changed')
    package=prep.initial.latest(prep.AREA,'latest-package');record=json.loads((package/'analysis.json').read_text());bundle=package/'bundle'
    require(record['passed'] is True and ack['package_manifest_sha256']==record['package_manifest_sha256']==sha(bundle/'package.json'),'Native initial package binding')
    manifest=json.loads((bundle/'package.json').read_text());ctx=json.loads((bundle/'context.json').read_text())
    for n,h in manifest['files'].items():require(sha(bundle/n)==h,'Initial package changed')
    report=json.loads((stage/'analysis.json').read_text());intent=recovery.load_attempt(stage/'handoff',ack['next_attempt_id'],ack['next_attempt_sha256'])
    journal={n:json.loads((stage/'write-journal'/f'{n}.json').read_text()) for n in ['unlock-intent','write-intent','complete']}
    collector.validate(report,ctx,manifest,journal,intent)
    require(ack['next_attempt_id']==ctx['next_attempt_id'] and Path(ack['next_attempt_directory'])==stage/'handoff','Independent handoff fence location')
    composed=Path(record['C93_composition']);require(composed.resolve().is_relative_to(WORK/'initial-migration'),'Known C93 composition')
    h=json.loads((composed/'host-analysis.json').read_text());co=json.loads((composed/'analysis.json').read_text())
    request=json.loads((composed/'request.json').read_text());plan=json.loads((composed/'plan.json').read_text())
    require(h['passed'] is True and sha(composed/'analysis.json')==h['consumer_analysis_sha256'] and
        sha(composed/'request.json')==h['request_sha256'] and co['candidate_sha256']==ctx['candidate_sha256']==intent['candidate_root_sha256'] and
        co['migration_counter']==plan['recovery_counter']==intent['counter_floor'] and co['fresh_no_credit_seed_verified'] is True and
        co['seed_loaded_or_credited'] is False,'C93 composition/entropy binding')
    require(sha(composed/'candidate.ext4')==ctx['candidate_sha256'],'Candidate image changed after migration')
    for n,digest in h['source_sha256'].items():require(sha(REPO/n)==digest,'Composed source changed')
    rows=json.loads((composed/'private-files.json').read_text());recovery.manifest(rows,intent['counter_floor'])
    require(recovery.CREDIT not in rows and recovery.NO_CREDIT in rows,'Initial candidate no-credit inventory')
    old=sorted(set(plan['old_seed_sha256'])|{rows[recovery.NO_CREDIT]['sha256']})
    stable={n:r for n,r in ctx['physical_capture']['backup_private_files'].items() if n in recovery.STABLE}
    expected=intent['counter_floor']+1;common=installed.current_common('',intent['counter_floor'],expected)
    common,matching=matched_common(common,json.loads((composed/'tree.json').read_text()))
    return stage,ack,expected,stable,old,common,matching

def main(host):
    os.umask(0o077);host=str(ipaddress.IPv4Address(host))
    # No stage, token, SSH or device action before this precondition.
    stage,ack,expected,stable,old,common,matching=lineage()
    tests=prep.initial.latest(AREA,'latest-checks');checks=json.loads((tests/'analysis.json').read_text())
    require(checks['passed'] is True,'C97 checks required')
    for n,h in checks['source_sha256'].items():require(sha(REPO/n)==h,'Tested boot collector source changed')
    require(not (AREA/'latest-complete').exists(),'First boot already qualified; do not repeat')
    code=entropy.render(common,expected,stable,old)
    result=Path(tempfile.mkdtemp(prefix='collect.',dir=AREA));write_new(result/'checks.sh',code.encode())
    write_new(result/'binding.json',recovery.encoded({'host':host,'initial_host_copy':str(stage),'initial_host_copy_sha256':sha(stage/'host-copy.json'),
        'next_attempt_id':ack['next_attempt_id'],'next_attempt_sha256':ack['next_attempt_sha256'],'expected_counter':expected,'guard_match':matching}))
    (AREA/'latest-attempt').write_text(str(result)+'\n');sync_dir(AREA)
    ssh=['ssh','-p','2222','-i',str(WORK/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes',
        '-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(WORK/'private/c07-known_hosts'),
        '-oBatchMode=yes','-oConnectTimeout=8','root@'+host,'sh -s']
    r=subprocess.run(ssh,input=code.encode(),capture_output=True,timeout=90)
    for n,data in [('stdout',r.stdout),('stderr',r.stderr),('exit',(str(r.returncode)+'\n').encode())]:write_new(result/n,data)
    require(r.returncode==0,'First C79 boot check failed; preserve evidence, do not reboot/rewrite automatically')
    observed=entropy.decoded(r.stdout.decode(),expected)
    report={'passed':True,'schema':97,'experiment':'C97_FIRST_C79_BOOT_AFTER_NATIVE_INITIAL_MIGRATION','boot_sequence':expected,
        'kernel_boot_id':observed['boot_id'],'initial_host_copy_sha256':sha(stage/'host-copy.json'),'checks_sha256':sha(tests/'analysis.json'),
        'guard_match':matching,'stable_identity_files_verified':len(stable),'physical_boot_after_initial_migration_qualified':True,
        'seedless_no_credit_2048bits_path_verified':True,'rng_ready_before_new_creditable_seed_and_stop_verified':True,
        'candidate_and_known_old_seed_hashes_absent':True,'root0755_readonly_p3_unmounted_PCM_closed_no_UI_or_once':True,
        'device_written_rebooted_or_tests_rearmed_by_collector':False,'source_sha256':checks['source_sha256']}
    write_new(result/'analysis.json',recovery.encoded(report));sync_dir(result);(AREA/'latest-complete').write_text(str(result)+'\n');sync_dir(AREA)
    print('C97 first native C79 boot qualified:',result,'boot',expected)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True);main(p.parse_args().host)
