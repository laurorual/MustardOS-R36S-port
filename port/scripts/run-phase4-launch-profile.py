#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C117 autonomous check-only profiling using resident inputs and rootRO."""
import argparse,ipaddress,json,os,subprocess,sys,tempfile
from pathlib import Path
import phase4_launch_profile as model
from phase4_backup_core import write_new,sync_dir
from phase4_gambatte_install import INFRA

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host',required=True,type=ipaddress.IPv4Address)
    p.add_argument('--boot',required=True,type=int);p.add_argument('--boot-id',required=True);a=p.parse_args()
    def audit(event,args):
        if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            model.require('/port/roms/' not in os.fsdecode(args[0]),'C117 cannot read the host ROM')
    sys.addaudithook(audit)
    os.umask(0o077);model.AREA.mkdir(mode=0o700,exist_ok=True)
    prior,previous=model.qualified();guard=model.session.current_common('',0,a.boot,a.boot_id)
    checks=Path((model.AREA/'latest-checks').read_text().strip())
    model.require(checks.resolve().is_relative_to(model.AREA),'Known C117 checks')
    cr=json.loads((checks/'analysis.json').read_text());model.require(cr['passed'] is True,'C117 checks passed')
    for n,h in cr['source_sha256'].items():model.require(model.sha(model.REPO/n)==h,'Checked source unchanged')
    stage=Path(tempfile.mkdtemp(prefix='profile.',dir=model.AREA))
    (model.AREA/'latest-attempt').write_text(str(stage)+'\n')
    ssh=['ssh','-p','2222','-i',str(model.WORK/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes',
         '-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(model.WORK/'private/c07-known_hosts'),
         '-oBatchMode=yes','-oConnectTimeout=6','root@'+str(a.host)]
    def remote(label,code):
        write_new(stage/(label+'.sh'),code.encode())
        r=subprocess.run(ssh+['sh -s'],input=code,text=True,capture_output=True,timeout=150)
        for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:write_new(stage/(label+'.'+n),v.encode())
        model.require(r.returncode==0,'C117 failed '+label+'; retain current capsule and inspect '+str(stage))
        print('C117 step:',label,flush=True);return r.stdout
    before=remote('before',guard+INFRA)
    baseline=remote('mounts-before',guard+'cat /proc/1/mountinfo\n')
    d=model.session.previous.resident.capsule(remote('allocate',guard+'mktemp -d /run/muos-prefs-data.XXXXXX\n').strip())
    write_new(stage/'intent.json',(json.dumps({'schema':117,'directory':d,'boot_sequence':a.boot,'kernel_boot_id':a.boot_id,
        'C116_analysis_sha256':model.sha(prior/'analysis.json'),'checks_analysis_sha256':model.sha(checks/'analysis.json'),
        'source_sha256':cr['source_sha256']},indent=2)+'\n').encode());sync_dir(stage)
    model.require(remote('prepare',guard+f'sh /usr/libexec/muos-resident/load.sh prepare {d}\n')=='C112_RESIDENT_PREPARED_ZERO_UPLOADS\n','Resident preparation')
    validation=model.validation_commands(d,guard,a.boot,a.boot_id)
    model.require(remote('validate',validation)=='C117_CURRENT_CAPSULE_VALID_NO_UI\n','Current capsule validation')
    measured=model.metrics(remote('profile',guard+model.profile_commands(d)))
    model.require(remote('validate-after',validation)=='C117_CURRENT_CAPSULE_VALID_NO_UI\n','Original scripts/assets/metadata unchanged')
    model.require(remote('after',guard+INFRA)==before,'Infrastructure unchanged')
    model.require(remote('mounts-after',guard+'cat /proc/1/mountinfo\n')==baseline,'Global mounts unchanged')
    remote('cleanup',guard+f'''[ -d {d} ];[ ! -L {d} ];[ "$(stat -c %u:%g:%a {d})" = 0:0:700 ]
[ ! -e {d}/data ];[ ! -L {d}/data ]
rm -rf {d}
echo C117_RAM_REMOVED_ROOT_RO_NO_UI
''')
    model.require(remote('post-cleanup-health',guard+INFRA)==before,'Final native health preserved')
    report={'passed':True,'schema':117,'boot_sequence':a.boot,'kernel_boot_id':a.boot_id,'metrics':measured,
        'C116_analysis_sha256':model.sha(prior/'analysis.json'),'checks_analysis_sha256':model.sha(checks/'analysis.json'),
        'source_sha256':cr['source_sha256'],'unmodified_check_scripts_used':True,'inputs_uploaded':0,
        'local_ROM_reads_prohibited':True,'GUI_core_input_audio_reboot_or_persistent_write_executed':False,
        'physical_audio_or_graphics_validation_claimed':False,'actual_launch_path_timing_measured':False,
        'clock':'proc uptime; kernel tick resolution; includes measurement overhead; warm repeated checks',
        'RAM_removed':True,'root_RO_data_unmounted_infrastructure_and_global_mounts_preserved':True}
    write_new(stage/'analysis.json',(json.dumps(report,indent=2)+'\n').encode());sync_dir(stage)
    (model.AREA/'latest-complete').write_text(str(stage)+'\n');sync_dir(model.AREA)
    print('C117 check-only profile complete:',stage);print(json.dumps(measured,indent=2))
if __name__=='__main__':main()
