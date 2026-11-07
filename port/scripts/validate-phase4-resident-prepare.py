#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C114 automated resident preparation/CLI/ABI qualification, never starts GUI/core."""
import argparse,ipaddress,json,os,subprocess,sys,tempfile
from phase4_resident_runtime import *
from phase4_backup_core import write_new,sync_dir
from phase4_gambatte_install import INFRA

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True,type=ipaddress.IPv4Address);a=p.parse_args()
 # Enforce, rather than merely claim, that the local ROM is not an input.
 def audit(event,args):
  if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
   value=os.fsdecode(args[0]);require('/port/roms/' not in value,'Local ROM reads are forbidden in C114')
 sys.addaudithook(audit)
 os.umask(0o077);AREA.mkdir(mode=0o700,exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='validate.',dir=AREA))
 guard=common();import_stage,r,meta,_=qualified_rom()
 ssh=['ssh','-p','2222','-i',str(WORK/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes',
 '-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(WORK/'private/c07-known_hosts'),'-oBatchMode=yes','-oConnectTimeout=6','root@'+str(a.host)]
 def remote(label,code):
  write_new(stage/(label+'.sh'),code.encode());result=subprocess.run(ssh+['sh -s'],input=code,text=True,capture_output=True,timeout=150)
  for n,v in [('stdout',result.stdout),('stderr',result.stderr),('exit',str(result.returncode)+'\n')]:write_new(stage/(label+'.'+n),v.encode())
  require(result.returncode==0,'C114 failed: '+label+'; retain current capsule: '+str(stage));return result.stdout
 before=remote('before',guard+INFRA)
 d=capsule(remote('allocate',guard+'mktemp -d /run/muos-prefs-data.XXXXXX\n').strip())
 write_new(stage/'intent.json',(json.dumps({'schema':114,'directory':d,'boot_sequence':r['boot_sequence'],
 'C113_analysis_sha256':sha(import_stage/'analysis.json'),'source_sha256':{str(p.relative_to(REPO)):sha(p) for p in [Path(__file__),Path(store.__file__),REPO/'port/scripts/phase4_resident_runtime.py']}},indent=2)+'\n').encode());sync_dir(stage)
 remote('mounts-before',guard+f'cat /proc/1/mountinfo > {d}/c114.mounts\n')
 # Loader requires a completely empty capsule: keep baseline mountinfo on host.
 mounts=(stage/'mounts-before.sh').read_text()
 baseline=remote('mount-baseline',guard+f'cat {d}/c114.mounts\nrm {d}/c114.mounts\n')
 require(remote('prepare',guard+f'sh /usr/libexec/muos-resident/load.sh prepare {d}\n')=='C112_RESIDENT_PREPARED_ZERO_UPLOADS\n','Authentic internal preparation')
 require(remote('validate',validation_commands(d))=='C114_RESIDENT_ASSETS_ROM_IDENTITY_METADATA_VALIDATED_NO_UI\n','Exact qualified capsule')
 remote('host-cli',guard+f'/bin/sh {d}/installed-host.sh {d} check\n')
 names=['libui.so','libmuxcom.so','libmuxmod.so','libplutosvg.so'];args=' '.join(d+'/provider-lib/'+n for n in names)
 abi=remote('provider-ABI',guard+f'''LD_BIND_NOW=1 LD_LIBRARY_PATH={d}/provider-lib:/opt/muos/frontend/lib {d}/provider-probe {args}
LD_BIND_NOW=1 LD_LIBRARY_PATH={d}/provider-lib:/opt/muos/frontend/lib /opt/muos/frontend/muxretro --version
LD_BIND_NOW=1 LD_LIBRARY_PATH={d}/provider-lib:/opt/muos/frontend/lib /opt/muos/frontend/muxretro --help
''')
 require(abi.count('C65 eager load: ')==4 and 'muxretro interface 1' in abi,'Native eager ABI/CLI compatibility')
 require(remote('after',guard+INFRA)==before,'Infrastructure preserved')
 require(remote('mounts-after',guard+'cat /proc/1/mountinfo\n')==baseline,'Global mounts unchanged')
 remote('cleanup',guard+f'''[ -d {d} ];[ ! -L {d} ];[ "$(stat -c %u:%g:%a {d})" = 0:0:700 ]
[ ! -e {d}/data ];[ ! -L {d}/data ]
rm -rf {d}
echo C114_RAM_REMOVED_ROOT_RO_NO_UI
''')
 require(remote('post-cleanup-health',guard+INFRA)==before,'Final native health preserved')
 result={'passed':True,'schema':114,'boot_sequence':r['boot_sequence'],'kernel_boot_id':meta['kernel_boot_id'],
 'inputs_uploaded':0,'local_ROM_reads_prohibited':True,'ROM_internal_p3_verified':True,
 'public_RAM_assets_verified':11,'caller_RAM_scripts_verified':10,'identity_and_metadata_match_C109':True,
 'native_eager_ABI_and_host_CLI_passed':True,'root_read_only':True,'data_unmounted':True,'RAM_removed':True,
 'global_mountinfo_and_infrastructure_preserved':True,'GUI_core_input_audio_or_reboot_executed':False,
 'physical_graphical_test_pending':True,'C113_analysis_sha256':sha(import_stage/'analysis.json'),
 'source_sha256':json.loads((stage/'intent.json').read_text())['source_sha256']}
 write_new(stage/'analysis.json',(json.dumps(result,indent=2)+'\n').encode());sync_dir(stage)
 (AREA/'latest-complete').write_text(str(stage)+'\n');sync_dir(AREA)
 print('C114 zero-upload internal ROM preparation and ABI passed; no UI:',stage)
if __name__=='__main__':main()
