#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C122 native installed resident copy/adoption, zero uploads and no GUI."""
import argparse,ipaddress,json,os,re,subprocess,tempfile
from pathlib import Path
import phase4_resident_batch as m
from phase4_backup_core import write_new,sync_dir
from phase4_gambatte_install import INFRA

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True,type=ipaddress.IPv4Address);a=p.parse_args()
 def audit(event,args):
  if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):m.require('/port/roms/' not in os.fsdecode(args[0]),'No host ROM reads')
 os.umask(0o077);import sys;sys.addaudithook(audit)
 installed=Path((m.AREA/'latest-complete').read_text().strip());m.require(installed.resolve().is_relative_to(m.AREA),'Known C122 installed stage')
 r=json.loads((installed/'analysis.json').read_text());plan=json.loads((installed/'plan.json').read_text())
 m.require(r['passed'] is True and r['schema']==122 and r['plan_sha256']==m.sha(installed/'plan.json'),'Closed C122 install')
 for n,h in r['source_sha256'].items():m.require(m.sha(m.REPO/n)==h,'Installed source unchanged')
 boot=m.current_observation();guard=m.common()
 for n,h in plan['files'].items():
  guard+=f'''[ -f /{m.PREFIX}/{n} ];[ ! -L /{m.PREFIX}/{n} ];[ "$(stat -c %u:%g:%a:%h /{m.PREFIX}/{n})" = 0:0:644:1 ]
printf '%s  %s\\n' {h} /{m.PREFIX}/{n} | sha256sum -c - >/dev/null
'''
 guard+=f'''[ ! -L /{m.PREFIX} ];[ "$(stat -c %u:%g:%a /{m.PREFIX})" = 0:0:755 ]
[ "$(find /{m.PREFIX} -mindepth 1 -maxdepth 1 -print | wc -l)" = 9 ]
'''
 stage=Path(tempfile.mkdtemp(prefix='validate.',dir=m.AREA));(m.AREA/'latest-validation-attempt').write_text(str(stage)+'\n')
 ssh=['ssh','-p','2222','-i',str(m.WORK/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes',
 '-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(m.WORK/'private/c07-known_hosts'),'-oBatchMode=yes','-oConnectTimeout=6','root@'+str(a.host)]
 def remote(label,code):
  write_new(stage/(label+'.sh'),code.encode());x=subprocess.run(ssh+['sh -s'],input=code,capture_output=True,text=True,timeout=150)
  for n,v in [('stdout',x.stdout),('stderr',x.stderr),('exit',str(x.returncode)+'\n')]:write_new(stage/(label+'.'+n),v.encode())
  m.require(x.returncode==0,'C122 validation failed '+label+'; retain capsule and inspect '+str(stage));print('C122 validation:',label,flush=True);return x.stdout
 before=remote('before',guard+INFRA);mounts=remote('mounts-before',guard+'cat /proc/1/mountinfo\n')
 d=remote('allocate',guard+'mktemp -d /run/muos-prefs-data.XXXXXX\n').strip();m.graphics.session.previous.resident.capsule(d)
 write_new(stage/'intent.json',(json.dumps({'schema':122,'directory':d,'boot_sequence':boot['boot_sequence'],'kernel_boot_id':boot['kernel_boot_id'],
 'installed_analysis_sha256':m.sha(installed/'analysis.json'),'runtime_uploads':0},indent=2)+'\n').encode());sync_dir(stage)
 m.require(remote('prepare',guard+f'sh /usr/libexec/muos-resident/load.sh prepare {d}\n')=='C112_RESIDENT_PREPARED_ZERO_UPLOADS\n','Original resident prepare')
 m.require(remote('adopt',guard+f'sh /{m.PREFIX}/load.sh adopt {d}\n')=='C122_RESIDENT_BATCH_ADOPTED_ZERO_UPLOADS\n','Resident adoption')
 code=guard+f'sh {d}/contract-v3/caller.sh staged {d}\n'
 for n,h in {n:plan['files'][n] for n in m.graphics.contract.NAMES}.items():
  code+=f'''[ "$(stat -c %u:%g:%a:%h {d}/contract-v3/{n})" = 0:0:644:1 ]
cmp /{m.PREFIX}/{n} {d}/contract-v3/{n}
printf '%s  %s\\n' {h} {d}/contract-v3/{n} | sha256sum -c - >/dev/null
'''
 code+=f'''if sh /{m.PREFIX}/load.sh adopt {d};then exit 64;fi
if sh {d}/contract-v3/caller.sh run {d} save;then exit 64;fi
[ ! -e {d}/caller-v3-stage/run.once ];[ ! -L {d}/caller-v3-stage/run.once ]
sh {d}/contract-v3/caller.sh staged {d}
sh {d}/installed-host.sh {d} check
echo C122_EXACT_LOCAL_COPY_REPEAT_AND_SAVE_REFUSED_NO_UI
'''
 checked=remote('verify',code)
 m.require(checked.endswith('C122_EXACT_LOCAL_COPY_REPEAT_AND_SAVE_REFUSED_NO_UI\n') and checked.count('C120_HOST_BATCH_VALID files=40 operation=check')==1,'Complete adopted check')
 m.require(remote('after',guard+INFRA)==before,'Infrastructure unchanged')
 m.require(remote('mounts-after',guard+'cat /proc/1/mountinfo\n')==mounts,'Global mounts unchanged')
 remote('cleanup',guard+f'''[ -d {d} ];[ ! -L {d} ];[ "$(stat -c %u:%g:%a {d})" = 0:0:700 ]
[ ! -e {d}/data ];[ ! -L {d}/data ];! findmnt -rn -M {d} >/dev/null
rm -rf {d}
echo C122_CAPSULE_REMOVED_ROOT_RO
''')
 m.require(remote('post-cleanup-health',guard+INFRA)==before,'Final health unchanged')
 report={'passed':True,'schema':122,'boot_sequence':boot['boot_sequence'],'kernel_boot_id':boot['kernel_boot_id'],
 'installed_analysis_sha256':m.sha(installed/'analysis.json'),'inputs_and_contract_files_uploaded':0,'local_ROM_reads_prohibited':True,
 'exact_C120_bundle_copied_locally':True,'new_run_claim_absent':True,'repeat_and_save_refused':True,'adopted_host_check_passed':True,
 'GUI_core_audio_input_reboot_or_persistent_write_executed':False,'global_mounts_and_infrastructure_preserved':True,'RAM_removed':True,'root_readonly':True,
 'source_sha256':{str(Path(__file__).relative_to(m.REPO)):m.sha(Path(__file__))}}
 write_new(stage/'analysis.json',(json.dumps(report,indent=2)+'\n').encode());sync_dir(stage)
 (m.AREA/'latest-validated').write_text(str(stage)+'\n');sync_dir(m.AREA);print('C122 installed zero-upload validation complete:',stage)
if __name__=='__main__':main()
