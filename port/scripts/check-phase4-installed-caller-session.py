#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C106 routing/binding checks, reusing the qualified C105 runtime fixtures."""
from pathlib import Path
from unittest.mock import patch
import ast,json,os,subprocess,tempfile
import phase4_installed_caller_session as session
from phase4_backup_core import write_new,sync_dir

def main():
    os.umask(0o077);session.AREA.mkdir(mode=0o700,exist_ok=True);cases=[]
    def reject(name,fn):
        try:fn()
        except (ValueError,KeyError,TypeError,AssertionError):cases.append(name)
        else:raise AssertionError(name)
    q=session.qualified();stage,r,meta,plan=q;boot=r['boot_sequence']
    cases.append('qualified-native-C105-and-frozen-public-payload')
    with patch.object(session,'qualified',return_value=q):
        for name,value in [('old-boot',boot-1),('next-boot',boot+1),('boolean',True),('string',str(boot))]:
            reject('reject-'+name,lambda value=value:session.current_common('',0,value))
        guard=session.current_common('',0,boot)
        require=session.require
        require(guard.splitlines().count('c25_ready')==1 and '/usr/libexec/muos-caller/caller.sh' in guard,
            'Installed package and unchanged readiness gate')
        hashes=__import__('re').findall(r"printf '[^']+' ([0-9a-f]{64}) /([A-Za-z0-9_./+-]+) \| sha256sum -c - >/dev/null",guard)
        assert len(hashes)==160 and len(set(n for _,n in hashes))==160
        subprocess.run(['sh','-n'],input=guard,text=True,check=True)
        cases.append('full-143-foundation-plus-17-installed-caller-hashes-and-metadata')
        ctx,prior_stage,prior,provider_stage,provider,online=session.historical()
        observation={'passed':True,'experiment':'C77_OBSERVED_BOOT','boot_sequence':boot,
            'kernel_boot_id':meta['kernel_boot_id'],'prior_analysis_sha256':session.sha(prior_stage/'analysis.json'),
            'provider_analysis_sha256':session.sha(provider_stage/'analysis.json'),
            'C66_analysis_sha256':session.sha(session.WORK/'frontend-libs-session/load.o2agwm0q/analysis.json'),
            'C67_analysis_sha256':session.sha(ctx['C67_stage']/'analysis.json'),
            'C72_analysis_sha256':session.sha(session.WORK/'provider-upgrade-native/install.otw0lflu/install-analysis.json'),
            'C76_analysis_sha256':session.sha(session.WORK/'gambatte-install/install.ucdyhb4b/install-analysis.json'),
            'C105_analysis_sha256':session.sha(stage/'analysis.json'),
            'C105_proof_sha256':session.sha(session.proof('manual-caller-installed')/'SHA256SUMS'),
            'root_RO_installed_payload_and_foundation_verified':True,'infrastructure':'offline fixture',
            'agent_requested_reboot':False}
        assert session.bind(prior,provider,observation,boot,meta['kernel_boot_id'])==ctx['C66_report']['libraries']
        cases.append('current-C105-boot-and-unchanged-GB-assets-bound')
        for key in ['C105_analysis_sha256','C105_proof_sha256']:
            bad={**observation,key:'0'*64};reject('reject-'+key,lambda bad=bad:session.bind(prior,provider,bad,boot,meta['kernel_boot_id']))
        reject('reject-wrong-UUID',lambda:session.bind(prior,provider,observation,boot,'00000000-0000-4000-8000-000000000106'))
        reject('reject-missing-observation',lambda:session.bind(prior,provider,{},boot,meta['kernel_boot_id']))
    text=session.render_online(online);ast.parse(text)
    assert 'if n in caller_scripts:continue' in text and 'C47_WORKER' not in text
    assert '/bin/sh /usr/libexec/muos-caller/caller.sh run {directory} {native_mode}' in text
    assert '{directory}/runner 240' not in text and 'stage {directory}' in text
    assert 'caller-stage/run.once' in text and 'timeout=300' in text
    assert 'timeout=120' in text and "'Quick Save (hotkey)'" not in text
    cases.append('installed-stage-and-run-routing-no-script-upload-or-direct-worker-entry')
    reject('reject-changed-online-anchor',lambda:session.render_online(online.replace("remote('prepare',code)",'missing_prepare_anchor()')))
    runner=session.rendered_runner();ast.parse(runner)
    assert 'caller_scripts_transferred_by_host' in runner and "'Quick Save (hotkey)' not in game" in runner
    assert 'C106_INSTALLED_WORKER_CMDLINE_CONFIRMED' in runner and 'C106_INSTALLED_CALLER_RUN_ONCE_CONFIRMED' in runner
    cases.append('new-proof-requires-installed-worker-and-one-shot-marker-plus-map-and-snapshot-checks')
    code=session.watch_script('/run/muos-prefs-data.ABC123')
    subprocess.run(['sh','-n'],input=code,text=True,check=True)
    assert 'seq 1 310' in code and '/usr/libexec/muos-caller/worker.sh' in code
    assert 'manager_start' in code and '/environ' not in code
    cases.append('bounded-readonly-worker-PID-starttime-cmdline-witness')
    reject('reject-watcher-path-injection',lambda:session.watch_script('/run/bad;exit'))
    for filename in ['phase4_installed_caller_session.py','run-phase4-installed-caller-session.py',
                     'finish-phase4-installed-caller-session.py','check-phase4-installed-caller-session.py']:
        ast.parse((session.REPO/'port/scripts'/filename).read_text())
    reused=json.loads((session.proof('manual-caller-installed')/'checks.json').read_text())
    assert reused['passed'] and reused['case_count']==43 and reused['binding_test_groups']==4
    cases.append('C105-43-plus-four-binding-groups-reused-without-rerunning-runtime-fixtures')
    target=Path(tempfile.mkdtemp(prefix='checks.',dir=session.AREA))
    sources=[Path(__file__),Path(session.__file__),session.REPO/'port/scripts/run-phase4-installed-caller-session.py',
        session.REPO/'port/scripts/finish-phase4-installed-caller-session.py']
    report={'passed':True,'schema':106,'case_count':len(cases),'cases':cases,
        'source_sha256':{str(p.relative_to(session.REPO)):session.sha(p) for p in sources},
        'C105_runtime_cases_reused':43,'C105_binding_groups_reused':4,
        'device_or_network_accessed':False,'core_ROM_reboot_or_image_build_executed':False}
    write_new(target/'analysis.json',(json.dumps(report,indent=2)+'\n').encode());sync_dir(target)
    (session.AREA/'latest-checks').write_text(str(target)+'\n');sync_dir(session.AREA)
    print('C106',len(cases),'installed caller routing/binding checks passed:',target)

if __name__=='__main__':main()
