#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C104 fresh-boot identity/binding checks; no hardware, reboot or ROM."""
from pathlib import Path
from unittest.mock import patch
import ast,importlib,json,os,subprocess,tempfile
import phase4_reboot_layout_session as session
from phase4_backup_core import write_new,sync_dir

def main():
    os.umask(0o077);session.AREA.mkdir(mode=0o700,exist_ok=True);cases=[]
    def reject(name,fn):
        try:fn()
        except (ValueError,KeyError,TypeError,AssertionError):cases.append(name)
        else:raise AssertionError(name)
    q=session.qualified();stage,previous=q
    cases.append('qualified-C103-physical-native-layout-history')
    boot=previous['boot_sequence']+1
    new_uuid='00000000-0000-4000-8000-000000000104'
    assert new_uuid!=previous['kernel_boot_id']
    session.transition(previous,boot,new_uuid);cases.append('next-counter-and-fresh-UUID')
    for name,b,u in [
        ('same-boot',boot-1,new_uuid),('older-boot',boot-2,new_uuid),('skipped-boot',boot+1,new_uuid),
        ('boolean-boot',True,new_uuid),('string-boot',str(boot),new_uuid),('counter-overflow',9999,new_uuid),
        ('old-UUID',boot,previous['kernel_boot_id']),('malformed-UUID',boot,'invalid'),('boolean-UUID',boot,True)]:
        reject('reject-'+name,lambda b=b,u=u:session.transition(previous,b,u))
    with patch.object(session,'qualified',return_value=q):
        reject('same-boot-guard',lambda:session.current_common('',0,boot-1))
        reject('skipped-boot-guard',lambda:session.current_common('',0,boot+1))
        reject('boolean-boot-guard',lambda:session.current_common('',0,True))
        guard=session.current_common('',0,boot)
        context,prior_stage,prior,provider_stage,provider,_=session.legacy.historical()
        observation={'passed':True,'experiment':'C77_OBSERVED_BOOT','boot_sequence':boot,'kernel_boot_id':new_uuid,
            'prior_analysis_sha256':session.sha(prior_stage/'analysis.json'),
            'provider_analysis_sha256':session.sha(provider_stage/'analysis.json'),
            'C66_analysis_sha256':session.sha(session.WORK/'frontend-libs-session/load.o2agwm0q/analysis.json'),
            'C67_analysis_sha256':session.sha(context['C67_stage']/'analysis.json'),
            'C72_analysis_sha256':session.sha(session.WORK/'provider-upgrade-native/install.otw0lflu/install-analysis.json'),
            'C76_analysis_sha256':session.sha(session.WORK/'gambatte-install/install.ucdyhb4b/install-analysis.json'),
            'root_RO_installed_payload_and_foundation_verified':True,'infrastructure':'offline fixture',
            'agent_requested_reboot':False,'C103_analysis_sha256':session.sha(stage/'analysis.json'),
            'C103_proof_sha256':session.sha(session.proof('native-layout-session')/'SHA256SUMS')}
        assert session.bind(prior,provider,observation,boot,new_uuid)==context['C66_report']['libraries']
        cases.append('fresh-observation-retains-qualified-C77-assets-and-new-C103-binding')
        for key in ['C103_analysis_sha256','C103_proof_sha256']:
            bad={**observation,key:'0'*64}
            reject('wrong-'+key,lambda bad=bad:session.bind(prior,provider,bad,boot,new_uuid))
        reject('missing-C103-observation',lambda:session.bind(prior,provider,{},boot,new_uuid))
    assert previous['kernel_boot_id'] not in guard
    assert guard.count("stat -c '%u:%g:%a:%h:%s' /var/lib/muos-network/")==3
    assert 'seed.credit' not in guard and 'seed.no-credit' not in guard
    assert '0:0:644:1:444' in guard and '0:0:755:2' in guard
    subprocess.run(['sh','-n'],input=guard,text=True,check=True)
    cases.append('guard-regenerated-for-new-counter-layout-and-four-stable-identities-without-seed-read')
    text=session.rendered_runner();ast.parse(text)
    assert 'from phase4_reboot_layout_session import ' in text and "'C104_post_reboot_layout_runtime_validation': True" in text
    assert "'Quick Save (hotkey)' not in game" in text and 'etc-view.sh' not in text
    cases.append('finite-runner-retains-no-save-map-and-cleanup-contracts')
    reboot=importlib.import_module('reboot-phase4-native-layout')
    request=reboot.request_code(guard)
    subprocess.run(['sh','-n'],input=request,text=True,check=True)
    assert request.endswith('sync\nprintf "C104_REQUEST_NORMAL_C07_REBOOT\\n"\n/sbin/reboot\n')
    assert 'reboot -f' not in request and 'sysrq' not in request
    cases.append('normal-PID1-request-with-sync-and-no-force')
    reused=json.loads((session.WORK/'native-layout-session/checks.d564ang1/analysis.json').read_text())
    assert reused['passed'] and reused['case_count']==26 and reused['unchanged_C77_cases_reused']==47
    for n,h in reused['source_sha256'].items():assert session.sha(session.REPO/n)==h
    cases.append('26-C103-and-47-C77-approved-cases-not-rerun')
    sources=[Path(__file__),Path(session.__file__),Path(reboot.__file__),
        session.REPO/'port/scripts/run-phase4-reboot-layout-session.py',
        session.REPO/'port/scripts/finish-phase4-reboot-layout-session.py']
    target=Path(tempfile.mkdtemp(prefix='checks.',dir=session.AREA))
    record={'passed':True,'schema':104,'case_count':len(cases),'cases':cases,
        'C103_checks_reused':26,'C77_checks_reused':47,
        'source_sha256':{str(p.relative_to(session.REPO)):session.sha(p) for p in sources},
        'device_or_network_accessed':False,'reboot_executed':False,'core_or_ROM_executed':False}
    write_new(target/'analysis.json',(json.dumps(record,indent=2)+'\n').encode());sync_dir(target)
    (session.AREA/'latest-checks').write_text(str(target)+'\n');sync_dir(session.AREA)
    print('C104',len(cases),'fresh boot checks passed:',target)

if __name__=='__main__':main()
