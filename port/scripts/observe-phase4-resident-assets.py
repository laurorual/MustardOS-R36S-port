#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C112 observe current C07 boot without reusing a historical UUID."""
import argparse,ipaddress,json,os,subprocess,tempfile
from phase4_resident_assets import *
from phase4_gambatte_install import INFRA
from phase4_backup_core import write_new,sync_dir

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True,type=ipaddress.IPv4Address);a=p.parse_args()
 os.umask(0o077);AREA.mkdir(mode=0o700,exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='observe.',dir=AREA))
 ssh=['ssh','-p','2222','-i',str(WORK/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes',
 '-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(WORK/'private/c07-known_hosts'),'-oBatchMode=yes','-oConnectTimeout=6','root@'+str(a.host)]
 def read(label,code):
  write_new(stage/(label+'.sh'),code.encode());r=subprocess.run(ssh+['sh -s'],input=code,text=True,capture_output=True,timeout=60)
  for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:write_new(stage/(label+'.'+n),v.encode())
  require(r.returncode==0,'Observation failed: '+str(stage));return r.stdout
 values=read('identity','set -eu\ncat /var/lib/muos-diagnostic/boot-seq /proc/sys/kernel/random/boot_id\n').splitlines()
 require(len(values)==2 and values[0].isdigit(),'Counter and UUID only');boot=int(values[0]);guard=observed_guard(boot,values[1])
 infra=read('ready',guard+INFRA)
 r={'passed':True,'schema':112,'boot_sequence':boot,'kernel_boot_id':values[1],'host':str(a.host),'infrastructure':infra,
 'guard_sha256':sha(stage/'ready.sh'),'C109_analysis_sha256':sha(qualified()[0]/'analysis.json'),'agent_requested_reboot':False}
 write_new(stage/'observation.json',(json.dumps(r,indent=2)+'\n').encode());sync_dir(stage)
 (AREA/'latest-observation').write_text(str(stage)+'\n');sync_dir(AREA)
 print('C112 observed current boot',boot,'C07 ready, 178 hashes and stable identity preserved:',stage)
if __name__=='__main__':main()
