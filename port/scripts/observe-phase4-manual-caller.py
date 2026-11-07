#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C105 fresh observation, or one normal reboot after proven USB recovery."""
import argparse,ipaddress,json,os,subprocess,tempfile
from phase4_manual_caller import *
from phase4_backup_core import write_new,sync_dir
from phase4_gambatte_install import INFRA

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['reboot-recovered','observe'])
    parser.add_argument('--host',required=True,type=ipaddress.IPv4Address);args=parser.parse_args()
    os.umask(0o077);prior,previous=qualified()
    checks=Path((AREA/'latest-checks').read_text().strip());require(checks.resolve().is_relative_to(AREA),'Known checks')
    tested=json.loads((checks/'analysis.json').read_text());require(tested['passed'] is True,'C105 checks required')
    for n,h in tested['source_sha256'].items():require(sha(REPO/n)==h,'Tested C105 sources changed')
    stage=Path(tempfile.mkdtemp(prefix='reboot-recovered.' if args.operation=='reboot-recovered' else 'observe.',dir=AREA))
    ssh=['ssh','-p','2222','-i',str(WORK/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes',
        '-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(WORK/'private/c07-known_hosts'),
        '-oBatchMode=yes','-oConnectTimeout=8','root@'+str(args.host),'sh -s']
    def write(n,data):write_new(stage/n,data.encode() if isinstance(data,str) else data)
    def remote(label,code):
        write(label+'.sh',code);r=subprocess.run(ssh,input=code,capture_output=True,text=True,timeout=120)
        for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:write(label+'.'+n,v)
        return r
    probe='''set -eu
export PATH=/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
c25_store=/var/lib/muos-diagnostic;c25_state=/run/muos/c25
. /usr/libexec/muos-c25/policy.sh
. /usr/libexec/muos-c25/card-guard.sh
. /usr/libexec/muos-c25/native.sh
c25_media && c25_root_mode ro && c25_quiet && c25_foundation
cat "$c25_store/boot-seq" /proc/sys/kernel/random/boot_id
'''
    r=remote('identity',probe);require(r.returncode==0,'Identity probe refused; no reboot or install')
    fields=r.stdout.splitlines();require(len(fields)==2 and fields[0].isdigit(),'Exact two-field identity')
    boot,boot_id=int(fields[0]),fields[1];boot_identity(boot,boot_id,previous)
    guard=observed_common(boot,boot_id)
    if args.operation=='reboot-recovered':
        require(boot<9998,'Next counter within qualified range')
        claim=AREA/'recovered-reboot.claim';require(not claim.exists(),'Never automatically repeat reboot request')
        code=recovered_reboot_guard(guard)
        r=remote('preflight',code+INFRA);require(r.returncode==0,'Recovered USB reboot preflight refused')
        intent={'schema':105,'kind':'NORMAL_REBOOT_MAY_HAVE_BEEN_REQUESTED','host':str(args.host),
            'previous_boot_sequence':boot,'previous_kernel_boot_id':boot_id,'expected_boot_sequence':boot+1,
            'C104_analysis_sha256':sha(prior/'analysis.json'),'automatic_retry_allowed':False,
            'guard_sha256':sha(stage/'preflight.sh'),'source_sha256':tested['source_sha256']}
        write('intent.json',json.dumps(intent,indent=2)+'\n');sync_dir(stage)
        write_new(claim,(str(stage)+'\n').encode());sync_dir(AREA)
        r=remote('request',code+'sync\nprintf "C105_REQUEST_NORMAL_REBOOT\\n"\n/sbin/reboot\n')
        require(r.returncode in (0,255) and r.stdout=='C105_REQUEST_NORMAL_REBOOT\n',
            'Request uncertain: preserve claim and inspect, never repeat')
        write('request.json',json.dumps({'requested':True,'return_verified':False,'expected_boot_sequence':boot+1})+'\n')
        sync_dir(stage);print('C105 normal reboot requested once; expected boot',boot+1,stage);return
    r=remote('ready',guard+INFRA);require(r.returncode==0,'C07-ready observation refused; no install')
    claim=AREA/'recovered-reboot.claim'
    if claim.exists():
        request=Path(claim.read_text().strip());require(request.resolve().is_relative_to(AREA),'Known request')
        intent=json.loads((request/'intent.json').read_text())
        require(boot==intent['expected_boot_sequence'] and boot_id!=intent['previous_kernel_boot_id'],
            'Observe the exact requested next boot, never silently skip another reboot')
        require(intent['source_sha256']==tested['source_sha256'],'Request source binding')
    report={'passed':True,'schema':105,'boot_sequence':boot,'kernel_boot_id':boot_id,'host':str(args.host),
        'C07_ready_without_recovery':True,'C104_analysis_sha256':sha(prior/'analysis.json'),
        'module_sha256':sha(REPO/'port/scripts/phase4_manual_caller.py'),
        'checks_sha256':sha(checks/'analysis.json'),'guard_sha256':sha(stage/'ready.sh'),
        'source_sha256':tested['source_sha256'],'infrastructure':r.stdout,'seed_files_read':False}
    write('observation.json',json.dumps(report,indent=2)+'\n');sync_dir(stage)
    (AREA/'latest-observation').write_text(str(stage)+'\n');sync_dir(AREA)
    print('C105 C07-ready boot observed:',boot,stage)

if __name__=='__main__':main()
