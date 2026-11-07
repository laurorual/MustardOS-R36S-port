#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check only the new C99 boot binding; reuse unchanged C77 dispatcher checks."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import ast,json,os,subprocess,tempfile
import phase4_c79_session as session
from phase4_backup_core import write_new,sync_dir


def main():
    os.umask(0o077);session.AREA.mkdir(exist_ok=True)
    cases=[]
    def reject(name,fn):
        try:fn()
        except (ValueError,KeyError,TypeError,AssertionError):cases.append(name)
        else:raise AssertionError(name)
    stage,report=session.qualified();public=json.loads((session.proof('initial-boot-native')/'analysis.json').read_text())
    session.valid_boot(report,public);cases.append('actual-native-migration-first-boot-lineage')
    for name,key,value in [('missing-qualification','passed',False),('wrong-schema','schema',True),
        ('wrong-boot','boot_sequence',report['boot_sequence']+1),('boolean-boot','boot_sequence',True),
        ('incomplete-guard','guard_match',{}),('missing-identity','stable_identity_files_verified',3),
        ('not-readonly','device_written_rebooted_or_tests_rearmed_by_collector',True),
        ('boot-not-qualified','physical_boot_after_initial_migration_qualified',False),
        ('wrong-seed-path','seedless_no_credit_2048bits_path_verified',False),
        ('old-seed-present','candidate_and_known_old_seed_hashes_absent',False)]:
        bad=deepcopy(report);bad[key]=value;reject(name,lambda bad=bad:session.valid_boot(bad,public))
    with patch.object(session,'qualified',return_value=(stage,report)):
        reject('later-boot-requires-separate-observation',lambda:session.current_common('',0,report['boot_sequence']+1))
        reject('boolean-requested-boot',lambda:session.current_common('',0,True))
        reject('wrong-kernel-boot-id',lambda:session.bind({}, {}, {}, report['boot_sequence'],'00000000-0000-0000-0000-000000000000'))
        reject('observation-without-C97-binding',lambda:session.bind({}, {}, {}, report['boot_sequence'],report['kernel_boot_id']))
    text=session.rendered_runner();ast.parse(text)
    require='from phase4_c79_session import '
    assert require in text and "'C99_C79_runtime_validation': True" in text
    assert 'Quick Save (hotkey)' in text and "'Quick Save (hotkey)' not in game" in text
    cases.append('finite-runner-adaptation-retains-no-save-and-cleanup-checks')
    common=session.current_common('',0,report['boot_sequence'])
    subprocess.run(['sh','-n'],input=common,text=True,check=True)
    assert report['kernel_boot_id'] in common and '%u:%g:%a:%h:%s' in common
    cases.append('141-C79-hashes-metadata-exact-boot-and-shell-syntax')
    frozen=session.proof('installed-core-session')
    old=session.WORK/'installed-core-session/checks.sqbqeova'
    previous=json.loads((old/'analysis.json').read_text())
    assert previous['passed'] and previous['case_count']==47
    assert previous==json.loads((frozen/'checks/analysis.json').read_text())
    for n,h in previous['source_sha256'].items():assert session.sha(session.REPO/n)==h
    cases.append('unchanged-47-approved-C77-dispatcher-content-and-binding-cases-reused')
    target=Path(tempfile.mkdtemp(prefix='checks.',dir=session.AREA))
    fixture=session.REPO/'port/diagnostics/phase4-c79-etc-fixture.py'
    argv=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
        '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=64m',
        '-v',str(session.WORK)+':/work:rw,z','-v',str(session.REPO/'port')+':/port:ro,z',
        (session.WORK/'rootfs-container.iid').read_text().strip(),'python3',
        '/port/diagnostics/phase4-c79-etc-fixture.py','/work/'+str((target/'etc-fixtures.json').relative_to(session.WORK))]
    result=subprocess.run(argv,capture_output=True,timeout=120)
    for n,data in [('stdout',result.stdout),('stderr',result.stderr),('exit',(str(result.returncode)+'\n').encode())]:
        write_new(target/('etc-fixtures.'+n),data)
    assert result.returncode==0,(target,result.stderr.decode()[-2000:])
    fixture_report=json.loads((target/'etc-fixtures.json').read_text());assert fixture_report['passed']
    cases+=fixture_report['cases']
    native=session.SESSION_NATIVE
    worker=(native/'worker.sh').read_text()
    assert '. "$dir/etc-view.sh"\nsession_c79_etc_prepare\nsession_prepare' in worker
    assert '[ "$path" = /etc/asound.conf ] || sha256sum "$path"' in worker
    assert '[ ! -e /etc/asound.conf ] && [ ! -L /etc/asound.conf ] || cleanup=1' in worker
    for p in native.glob('*.sh'):subprocess.run(['sh','-n',str(p)],check=True)
    cases.append('new-worker-isolates-etc-before-profile-and-verifies-original-absence-after-unmount')
    sources={session.REPO/n for n in previous['source_sha256']}
    sources.update([Path(__file__),session.REPO/'port/scripts/run-phase4-c79-session.py',Path(session.__file__),
        session.REPO/'port/scripts/prepare-phase4-c79-worker.py',fixture,*native.glob('*.sh')])
    record={'passed':True,'experiment':'C99_C79_SESSION_BINDING_CHECKS','case_count':len(cases),'cases':cases,
        'unchanged_C77_cases_reused':47,'C77_checks_sha256':session.sha(old/'analysis.json'),
        'C97_analysis_sha256':session.sha(stage/'analysis.json'),
        'source_sha256':{str(p.relative_to(session.REPO)):session.sha(p) for p in sources},
        'device_or_network_accessed':False,'core_or_ROM_executed':False}
    write_new(target/'analysis.json',(json.dumps(record,indent=2)+'\n').encode());sync_dir(target)
    (session.AREA/'latest-checks').write_text(str(target)+'\n');sync_dir(session.AREA)
    print('C99',len(cases),'binding checks passed; 47 unchanged C77 cases reused:',target)


if __name__=='__main__':main()
