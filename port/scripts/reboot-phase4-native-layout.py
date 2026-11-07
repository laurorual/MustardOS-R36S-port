#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C104 one normal PID1 reboot, only from the physically qualified C103 boot."""
from pathlib import Path
import argparse,ipaddress,json,os,subprocess,tempfile
import phase4_reboot_layout_session as session
from phase4_backup_core import write_new,sync_dir

def request_code(guard):
    return guard+'sync\nprintf "C104_REQUEST_NORMAL_C07_REBOOT\\n"\n/sbin/reboot\n'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True,type=ipaddress.IPv4Address)
    a=p.parse_args();os.umask(0o077);stage_old,prior=session.qualified()
    area=session.AREA;area.mkdir(mode=0o700,exist_ok=True)
    checks=Path((area/'latest-checks').read_text().strip());assert checks.resolve().is_relative_to(area)
    tested=json.loads((checks/'analysis.json').read_text());assert tested['passed']
    for n,h in tested['source_sha256'].items():assert session.sha(session.REPO/n)==h,n
    assert not (area/'reboot-request.claim').exists(),'Never dispatch a second reboot after an interrupted request'
    guard=session.native.current_common('',prior['boot_sequence'],prior['boot_sequence'])
    stage=Path(tempfile.mkdtemp(prefix='reboot.',dir=area))
    ssh=['ssh','-p','2222','-i',str(session.WORK/'private/c07-client'),'-oIdentitiesOnly=yes',
        '-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222',
        '-oUserKnownHostsFile='+str(session.WORK/'private/c07-known_hosts'),'-oBatchMode=yes',
        '-oConnectTimeout=8','root@'+str(a.host),'sh -s']
    def remote(label,code):
        write_new(stage/(label+'.sh'),code.encode())
        r=subprocess.run(ssh,input=code,capture_output=True,text=True,timeout=90)
        for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:write_new(stage/(label+'.'+n),v.encode())
        return r
    r=remote('preflight',guard+'sync\necho C104_NORMAL_REBOOT_PREFLIGHT_OK\n')
    assert r.returncode==0 and r.stdout=='C104_NORMAL_REBOOT_PREFLIGHT_OK\n',('Preflight refused; no reboot',stage)
    intent={'schema':104,'kind':'NORMAL_REBOOT_MAY_HAVE_BEEN_REQUESTED','host':str(a.host),
        'previous_boot_sequence':prior['boot_sequence'],'previous_kernel_boot_id':prior['kernel_boot_id'],
        'expected_boot_sequence':prior['boot_sequence']+1,'C103_analysis_sha256':session.sha(stage_old/'analysis.json'),
        'C103_proof_sha256':session.sha(session.proof('native-layout-session')/'SHA256SUMS'),
        'checks_sha256':session.sha(checks/'analysis.json'),'automatic_retry_allowed':False}
    write_new(stage/'intent.json',(json.dumps(intent,indent=2)+'\n').encode());sync_dir(stage)
    write_new(area/'reboot-request.claim',(str(stage)+'\n').encode());sync_dir(area)
    (area/'latest-reboot-request').write_text(str(stage)+'\n');sync_dir(area)
    result=remote('request',request_code(guard))
    assert result.returncode in (0,255) and result.stdout=='C104_REQUEST_NORMAL_C07_REBOOT\n',(
        'Request uncertain; inspect recorded attempt, never automatically repeat',stage)
    write_new(stage/'request.json',(json.dumps({'requested':True,'return_verified':False,'schema':104,
        'previous_boot_sequence':prior['boot_sequence'],'expected_boot_sequence':prior['boot_sequence']+1,
        'normal_PID1':True,'token_rearmed':False,'source_sha256':{str(Path(__file__).relative_to(session.REPO)):session.sha(Path(__file__))}},indent=2)+'\n').encode())
    sync_dir(stage);print('C104 one normal reboot requested; expected boot',prior['boot_sequence']+1,stage)

if __name__=='__main__':main()
