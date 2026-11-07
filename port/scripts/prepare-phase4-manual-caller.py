#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C105 finite caller package, no ROM/ELF/private identity or device action."""
from pathlib import Path
import json,os,re,subprocess,tempfile
from phase4_backup_core import write_new,sync_dir
from phase4_manual_caller import *

def main():
    os.umask(0o077);AREA.mkdir(mode=0o700,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='package.',dir=AREA));root=stage/'target'/PREFIX
    root.mkdir(mode=0o755,parents=True)
    for d in [stage/'target',stage/'target/usr',stage/'target/usr/libexec',root]:d.chmod(0o755)
    originals,intent=original_scripts()
    for n,p in originals.items():write_new(root/n,p.read_bytes())
    write_new(root/'functions.sh',(NATIVE/'functions.sh').read_bytes())
    write_new(root/'dependencies.tsv',public_dependencies().encode())
    assets=['runner','state-metadata',*[d+'/'+n for d in ['lib','provider-lib'] for n in parent.NAMES]]
    require(len(assets)==10 and len(set(assets))==10,'Fixed public runtime asset inventory')
    write_new(root/'assets.tsv',''.join(intent['binary_sha256'][n]+' '+n+'\n' for n in assets).encode())
    contract={'schema':105,'activation':'manual only','commands':['check','stage <capsule>','run <capsule> observe'],
        'prefix':'/'+PREFIX,'root_mode':'read-only','persistent_store_mode':'read-only','role':'load',
        'game_maximum_seconds':45,'outer_supervisor_seconds':240,'original_worker_seconds':210,
        'public_dependencies':142,'runtime_assets_pinned':10,'runtime_scripts':10,
        'ROM_core_host_store_or_provider_ELF_included':False,'private_identity_or_boot_UUID_included':False,
        'whole_etc_or_mnt_views_used':False,'autostart_or_power_enabled':False,
        'capsule_inputs':'root0700 tmpfs, pinned runtime assets, private GB ROM, existing load snapshot identity',
        'general_ROM_browser_or_standalone_session_preparation':False,'combined_license_review_pending':True}
    write_new(root/'contract.json',(json.dumps(contract,indent=2)+'\n').encode())
    write_new(root/'LICENSE',b'MIT License\n\nCopyright (c) 2026 muOS R35S port contributors\n\nPermission is hereby granted, free of charge, to any person obtaining a copy\nof this software and associated documentation files (the "Software"), to deal\nin the Software without restriction, including without limitation the rights\nto use, copy, modify, merge, publish, distribute, sublicense, and/or sell\ncopies of the Software, and to permit persons to whom the Software is\nfurnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice shall be included in all\ncopies or substantial portions of the Software.\n\nTHE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\nIMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\nFITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\nAUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\nLIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\nOUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\nSOFTWARE.\n')
    contents=SCRIPTS+['functions.sh','dependencies.tsv','assets.tsv','contract.json','LICENSE']
    write_new(root/'payload.sha256',''.join(sha(root/n)+' '+n+'\n' for n in contents).encode())
    text=(NATIVE/'caller.in.sh').read_text()
    for key,value in [('@MANIFEST_SHA@',sha(root/'payload.sha256')),('@FUNCTIONS_SHA@',sha(root/'functions.sh'))]:
        require(text.count(key)==1,'Finite caller entry substitution');text=text.replace(key,value)
    write_new(root/'caller.sh',text.encode())
    require(set(p.name for p in root.iterdir())==set(NAMES),'Finite installed scope')
    for p in root.iterdir():
        p.chmod(0o644)
        if p.suffix=='.sh':subprocess.run(['sh','-n',str(p)],check=True)
    # Own transactional scope derived from the frozen C76 adapter, never edit it.
    old=REPO/'port/device/rk-r35s-p0/gambatte-install'
    frozen=parent.proof('gambatte-installed')/'source'/old.relative_to(REPO)
    for n in ['transaction.sh','native.sh']:require((old/n).read_bytes()==(frozen/n).read_bytes(),'Frozen C76 adapter')
    transaction=(old/'transaction.sh').read_text().replace('c76','c105').replace('C76','C105')
    transaction=re.sub(r'c105_dirs\(\) \{.*?\n\}',lambda _:"c105_dirs() {\n    printf '%s\\n' "+PREFIX+'\n}',transaction,count=1,flags=re.S)
    transaction=re.sub(r'c105_names\(\) \{.*?\n\}',lambda _:"c105_names() {\n    printf '%s\\n' "+' '.join(PREFIX+'/'+n for n in NAMES)+'\n}',transaction,count=1,flags=re.S)
    transaction=transaction.replace('"$install_payload/FILES")" = 9','"$install_payload/FILES")" = 17')
    oldroots='opt/muos/share/core usr/share/muos-gambatte usr/share/licenses/muos-gambatte'
    require(transaction.count(oldroots)==2,'Exact absence and rollback owned roots')
    transaction=transaction.replace(oldroots,PREFIX)
    write_new(stage/'transaction.sh',transaction.encode())
    native=(old/'native.sh').read_text().replace('c76','c105').replace('C76','C105')
    # Reuse the qualified C102 fingerprint, including diagnostic/preferences.
    c102=(REPO/'port/device/rk-r35s-p0/c79-layout-install/native.sh').read_text()
    fp=c102.split('private_fingerprint() {\n',1)[1].split('\nlayout_exec()',1)[0]
    native=re.sub(r'private_fingerprint\(\) \{.*?\n\}\ninstall_exec',lambda _:'private_fingerprint() {\n'+fp+'\ninstall_exec',native,count=1,flags=re.S)
    native=native.replace('c25_ready || return 64','c25_ready && sh "$deployment/guard.sh" || return 64')
    write_new(stage/'native.sh',native.encode())
    for n in ['transaction.sh','native.sh']:subprocess.run(['sh','-n',str(stage/n)],check=True)
    report={'passed':True,'schema':105,'experiment':'C105_MANUAL_CALLER_PACKAGE','files':17,'directories':1,
        'bytes':sum(p.stat().st_size for p in root.iterdir()),'activation':'manual only',
        'original_scripts_byte_identical':True,'ROM_ELF_or_private_identity_included':False,
        'device_accessed_or_installed':False,'package_files':{n:sha(root/n) for n in NAMES},
        'adapter_sha256':{n:sha(stage/n) for n in ['transaction.sh','native.sh']},
        'parent_proofs_sha256':{n:sha(parent.proof(n)/'SHA256SUMS') for n in ['reboot-layout-session','gambatte-installed','c79-layout-installed']},
        'source_sha256':{str(p.relative_to(REPO)):sha(p) for p in source_files()}}
    write_new(stage/'analysis.json',(json.dumps(report,indent=2)+'\n').encode());sync_dir(root);sync_dir(stage)
    (AREA/'latest-package').write_text(str(stage)+'\n');sync_dir(AREA)
    print('C105 caller-only package prepared:',report['bytes'],'bytes,',stage)

if __name__=='__main__':main()
