#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C103 new installed-layout binding checks; no replay of approved C77 tests."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import ast,json,os,subprocess,tempfile
import phase4_native_layout_session as session
from phase4_backup_core import write_new,sync_dir

def main():
    os.umask(0o077);session.AREA.mkdir(mode=0o700,exist_ok=True);cases=[]
    def reject(name,fn):
        try:fn()
        except (ValueError,KeyError,TypeError,AssertionError):cases.append(name)
        else:raise AssertionError(name)
    qualified=session.qualified();stage,report,guard,manifest=qualified
    public=json.loads((session.proof('c79-layout-installed')/'analysis.json').read_text())
    session.valid_install(report,public);cases.append('actual-native-C102-install-and-C97-lineage')
    for key,value in [('passed',False),('schema',True),('boot_sequence',True),('boot_sequence',report['boot_sequence']+1),
        ('root_read_only',False),('RAM_capsule_removed',False),('private_state_fingerprint_matched',False),
        ('infrastructure_and_global_mounts_preserved',False),('public_template_unchanged',False),
        ('p1_or_p3_mounted',True),('seed_counter_or_user_data_updated',True),('reboot_or_UI_started',True),
        ('public_file_added_bytes',445),('empty_directory_added',2),('existing_files_replaced',1),
        ('foundation_files_reverified',140)]:
        bad=deepcopy(report);bad[key]=value
        reject('reject-'+key+'-'+str(value),lambda bad=bad:session.valid_install(bad,public))
    with patch.object(session,'qualified',return_value=qualified):
        reject('later-boot-needs-new-observation',lambda:session.current_common('',0,report['boot_sequence']+1))
        reject('boolean-requested-boot',lambda:session.current_common('',0,True))
        reject('wrong-kernel-boot-id',lambda:session.bind({}, {}, {},report['boot_sequence'],'00000000-0000-0000-0000-000000000000'))
        reject('missing-C102-observation',lambda:session.bind({}, {}, {},report['boot_sequence'],manifest['kernel_boot_id']))
        observation={'C102_analysis_sha256':'0'*64,'C102_proof_sha256':'0'*64}
        reject('wrong-C102-observation',lambda:session.bind({}, {},observation,report['boot_sequence'],manifest['kernel_boot_id']))
    subprocess.run(['sh','-n'],input=guard,text=True,check=True)
    text=session.rendered_runner();ast.parse(text)
    assert 'from phase4_native_layout_session import ' in text and "'C103_native_layout_runtime_validation': True" in text
    assert "'Quick Save (hotkey)' not in game" in text and "'Quick Load (hotkey)' in game" in text
    assert 'etc-view.sh' not in text and 'c79-session/worker.sh' not in text
    cases.append('runner-keeps-installed-assets-no-save-and-cleanup-without-C99-worker')
    assert '0:0:644:1:444' in guard and '0:0:755:2' in guard and '[ -d /mnt/mmc ]' in guard
    assert '[ ! -e /etc/asound.conf ];' not in guard and '[ ! -e /mnt/mmc ];' not in guard
    cases.append('guard-requires-installed-layout-and-exact-boot')
    original=session.REPO/'port/device/rk-r35s-p0/app-selection/worker.sh'
    worker=original.read_text()
    assert '    sha256sum "$path" >> "$state/writer-original.sha256"' in worker
    assert 'session_c79_etc_prepare' not in worker and 'etc-view.sh' not in worker
    subprocess.run(['sh','-n',str(original)],check=True)
    context,*_=session.historical();assert context['worker']==original and 'etc-view.sh' not in context['files']
    cases.append('original-worker-preserves-original-audio-hash-and-no-directory-copy')
    previous=json.loads((session.WORK/'installed-core-session/checks.sqbqeova/analysis.json').read_text())
    assert previous==json.loads((session.proof('installed-core-session')/'checks/analysis.json').read_text())
    assert previous['passed'] and previous['case_count']==47
    for n,h in previous['source_sha256'].items():assert session.sha(session.REPO/n)==h
    cases.append('47-approved-C77-cases-reused-by-source-and-report-not-rerun')
    sources={session.REPO/n for n in previous['source_sha256']}
    sources.update([Path(__file__),Path(session.__file__),original,
        session.REPO/'port/scripts/run-phase4-native-layout-session.py',
        session.REPO/'port/scripts/finish-phase4-native-layout-session.py'])
    target=Path(tempfile.mkdtemp(prefix='checks.',dir=session.AREA))
    record={'passed':True,'schema':103,'experiment':'C103_INSTALLED_LAYOUT_BINDING_CHECKS',
        'case_count':len(cases),'cases':cases,'unchanged_C77_cases_reused':47,
        'C77_checks_sha256':session.sha(session.WORK/'installed-core-session/checks.sqbqeova/analysis.json'),
        'C102_analysis_sha256':session.sha(stage/'analysis.json'),
        'source_sha256':{str(p.relative_to(session.REPO)):session.sha(p) for p in sources},
        'device_or_network_accessed':False,'core_or_ROM_executed':False}
    write_new(target/'analysis.json',(json.dumps(record,indent=2)+'\n').encode());sync_dir(target)
    (session.AREA/'latest-checks').write_text(str(target)+'\n');sync_dir(session.AREA)
    print('C103',len(cases),'installed-layout binding checks passed:',target)

if __name__=='__main__':main()
