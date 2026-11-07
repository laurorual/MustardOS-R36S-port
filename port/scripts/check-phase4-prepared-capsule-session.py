#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C109 reduced-upload routing and strict C111 boot/proof binding checks."""
from pathlib import Path
from unittest.mock import patch
import ast,hashlib,importlib,json,os,re,subprocess,tempfile
import phase4_prepared_capsule_session as session
from phase4_backup_core import write_new,sync_dir

def main():
    os.umask(0o077);session.AREA.mkdir(mode=0o700,exist_ok=True);cases=[]
    def reject(name,fn):
        try:fn()
        except (ValueError,KeyError,AssertionError,TypeError):cases.append(name)
        else:raise AssertionError(name)
    q=session.qualified();stage,r,meta,_=q;boot=r['boot_sequence']
    cases.append('qualified-C111-package-and-closed-native-C111')
    with patch.object(session,'qualified',return_value=q):
        for n,b in [('old',boot-1),('new',boot+1),('boolean',True),('string',str(boot))]:
            reject('wrong-boot-'+n,lambda b=b:session.current_common('',0,b))
        guard=session.current_common('',0,boot)
        rows=re.findall(r"printf '[^']+' ([0-9a-f]{64}) /([A-Za-z0-9_./+-]+) \| sha256sum -c - >/dev/null",guard)
        assert len(rows)==178 and len({n for _,n in rows})==178 and guard.splitlines().count('c25_ready')==1
        subprocess.run(['sh','-n'],input=guard,text=True,check=True);cases.append('178-installed-hashes-and-readiness-preserved')
        ctx,prior_stage,prior,provider_stage,provider,online=session.historical()
        derived=hashlib.sha256(b'MUOS-R35S-GB-SNAPSHOT-V1\0'+bytes.fromhex(ctx['nr']['core_sha256'])+bytes.fromhex(prior['ROM_sha256'])).hexdigest()
        assert derived==prior['private_identity']==ctx['identity']
        cases.append('actual-private-ROM-core-pair-derives-existing-C63-snapshot-identity')
        observation={'passed':True,'experiment':'C77_OBSERVED_BOOT','boot_sequence':boot,'kernel_boot_id':meta['kernel_boot_id'],
            'prior_analysis_sha256':session.sha(prior_stage/'analysis.json'),
            'provider_analysis_sha256':session.sha(provider_stage/'analysis.json'),
            'C66_analysis_sha256':session.sha(session.WORK/'frontend-libs-session/load.o2agwm0q/analysis.json'),
            'C67_analysis_sha256':session.sha(ctx['C67_stage']/'analysis.json'),
            'C72_analysis_sha256':session.sha(session.WORK/'provider-upgrade-native/install.otw0lflu/install-analysis.json'),
            'C76_analysis_sha256':session.sha(session.WORK/'gambatte-install/install.ucdyhb4b/install-analysis.json'),
            'C111_analysis_sha256':session.sha(stage/'analysis.json'),
            'C111_proof_sha256':session.sha(session.proof('capsule-preparer-v3-installed')/'SHA256SUMS'),
            'root_RO_installed_payload_and_foundation_verified':True,'agent_requested_reboot':False,'infrastructure':'fixture'}
        assert session.bind(prior,provider,observation,boot,meta['kernel_boot_id'])==ctx['C66_report']['libraries']
        cases.append('current-boot-existing-GB-state-and-unchanged-provider-bound')
        for key in ['C111_analysis_sha256','C111_proof_sha256']:
            bad={**observation,key:'0'*64};reject('wrong-'+key,lambda bad=bad:session.bind(prior,provider,bad,boot,meta['kernel_boot_id']))
        reject('missing-binding',lambda:session.bind(prior,provider,{},boot,meta['kernel_boot_id']))
        reject('wrong-UUID',lambda:session.bind(prior,provider,observation,boot,'00000000-0000-4000-8000-000000000109'))
    text=session.render_online(online);ast.parse(text)
    assert 'if n not in prepared_inputs:continue' in text and 'directory+\'/inputs/\'+prepared_inputs[n]' in text
    assert 'mkdir -m 700 {directory}/inputs' in text and 'mkdir -m 700 {directory}/lib' not in text
    assert '/usr/libexec/muos-capsule-v3/prepare.sh prepare {directory}' in text
    assert 'launcher.sha256' not in text and 'gb-assets.sha256' not in text and 'printf' not in text.split("remote('prepare',code,timeout=120)")[0].split('code=common+f')[-1]
    assert 'C107_CAPSULE_PREPARED_RAM_ONLY' in text and 'preparation.once/ready' in text
    assert '/usr/libexec/muos-caller/caller.sh run' in text and '{directory}/runner 240' not in text
    cases.append('five-input-uploads-and-installed-preparation-no-host-metadata-or-direct-worker')
    assert len(session.prep.INPUTS)==5 and 'private.gb' in session.prep.INPUTS
    assert set(session.prep.INPUTS.values())=={'runner','state-metadata','menu-libmuxmod.so','provider-probe','private.gb'}
    cases.append('four-public-inputs-one-private-ROM-no-identity-input')
    reject('changed-subdirs-anchor',lambda:session.render_online(online.replace("f'mkdir -m 700 {directory}/lib\\n'",'changed-subdirs')))
    runner=session.rendered_runner();ast.parse(runner)
    assert 'public_assets_copied_locally' in runner and "'Quick Save (hotkey)' not in game" in runner
    assert "'C111_analysis_sha256'" in runner and 'C109_local_preparation_runtime_validation' in runner
    cases.append('new-local-preparation-proof-retains-maps-hotkeys-snapshot-and-cleanup-contracts')
    watcher=session.watch_script('/run/muos-prefs-data.ABC123')
    subprocess.run(['sh','-n'],input=watcher,text=True,check=True)
    assert 'selection_consumed' in watcher and 'first_game_present' in watcher and 'sleep 1' in watcher
    cases.append('read-only-timing-witness-with-existing-one-second-poll')
    metrics=importlib.import_module('analyze-phase4-prepared-capsule-session')
    example='C109_EVENT selection_consumed uptime=100.25\nC109_EVENT first_game_present uptime=105.50\n'
    assert metrics.timing_metrics(example,'Startup: ready in 1320.50 ms total')['observed_selection_to_present_seconds']==5.25
    cases.append('sampled-interval-independent-of-native-startup-interval')
    for label,w,g in [('missing','', 'Startup: ready in 1.00 ms total'),
        ('duplicate',example+example,'Startup: ready in 1.00 ms total'),
        ('reversed',example.replace('105.50','90.00'),'Startup: ready in 1.00 ms total'),
        ('missing-startup',example,'no startup measurement')]:
        reject('reject-timing-'+label,lambda w=w,g=g:metrics.timing_metrics(w,g))
    sources=[Path(__file__),Path(session.__file__),session.REPO/'port/scripts/run-phase4-prepared-capsule-session.py',
        session.REPO/'port/scripts/finish-phase4-prepared-capsule-session.py',
        session.REPO/'port/scripts/analyze-phase4-prepared-capsule-session.py']
    for p in sources:ast.parse(p.read_text())
    target=Path(tempfile.mkdtemp(prefix='checks.',dir=session.AREA))
    tested=json.loads((session.proof('capsule-preparer-v3-installed')/'checks.json').read_text())
    report={'passed':True,'schema':109,'case_count':len(cases),'cases':cases,
        'source_sha256':{str(p.relative_to(session.REPO)):session.sha(p) for p in sources},
        'C107_C111_cases_reused':tested['case_count'],'device_or_network_accessed':False,
        'core_ROM_reboot_or_image_build_executed':False}
    write_new(target/'analysis.json',(json.dumps(report,indent=2)+'\n').encode());sync_dir(target)
    (session.AREA/'latest-checks').write_text(str(target)+'\n');sync_dir(session.AREA)
    print('C109',len(cases),'local preparation routing/binding checks passed:',target)

if __name__=='__main__':main()
