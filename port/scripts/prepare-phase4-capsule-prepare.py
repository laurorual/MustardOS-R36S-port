#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C107 script-only preparation package; C108 dedicated six-leaf transaction."""
import json,os,re,subprocess,tempfile
from phase4_capsule_prepare import *
from phase4_backup_core import write_new,sync_dir

def main():
    os.umask(0o077);AREA.mkdir(mode=0o700,exist_ok=True)
    table,core=asset_model();stage=Path(tempfile.mkdtemp(prefix='package.',dir=AREA));root=stage/'target'/PREFIX
    root.mkdir(parents=True)
    for p in [stage/'target',stage/'target/usr',stage/'target/usr/libexec',root]:p.chmod(0o755)
    write_new(root/'functions.sh',(NATIVE/'functions.sh').read_bytes())
    write_new(root/'assets.tsv',''.join(f'{h} {m:o} {d} {o}\n' for h,m,d,o in table).encode())
    contract={'schema':107,'activation':'manual only','local_public_assets':7,'input_public_assets':4,'input_ROM':'private RAM only',
        'persistent_ROM_or_data_mount':False,'host_metadata_required':False,'identity_derived_on_device':True,
        'role':'load','C105_modified':False,'ROM_ELF_seed_or_identity_included':False,'autostart':False}
    write_new(root/'contract.json',(json.dumps(contract,indent=2)+'\n').encode())
    write_new(root/'LICENSE',(base.proof('manual-caller-installed')/'payload/LICENSE').read_bytes())
    contents=['functions.sh','assets.tsv','contract.json','LICENSE']
    write_new(root/'payload.sha256',''.join(sha(root/n)+' '+n+'\n' for n in contents).encode())
    text=(NATIVE/'prepare.in.sh').read_text()
    for k,v in [('@MANIFEST_SHA@',sha(root/'payload.sha256')),('@FUNCTIONS_SHA@',sha(root/'functions.sh')),('@CORE_SHA@',core)]:
        require(text.count(k)==1,'Finite entry template');text=text.replace(k,v)
    write_new(root/'prepare.sh',text.encode())
    for p in root.iterdir():
        p.chmod(0o644)
        if p.suffix=='.sh':subprocess.run(['sh','-n',str(p)],check=True)
    old=base.proof('manual-caller-installed')/'adapter'
    tx=(old/'transaction.sh').read_text().replace('c105','c108').replace('C105','C108')
    tx=tx.replace('usr/libexec/muos-caller',PREFIX).replace('= 17 ]','= 6 ]')
    tx=re.sub(r'c108_names\(\) \{.*?\n\}',lambda _:"c108_names() {\n    printf '%s\\n' "+' '.join(PREFIX+'/'+n for n in NAMES)+'\n}',tx,count=1,flags=re.S)
    native=(old/'native.sh').read_text().replace('c105','c108').replace('C105','C108')
    for n,text in [('transaction.sh',tx),('native.sh',native)]:
        write_new(stage/n,text.encode());subprocess.run(['sh','-n',str(stage/n)],check=True)
    report={'passed':True,'schema':107,'files':6,'directories':1,'bytes':sum(p.stat().st_size for p in root.iterdir()),
        'package_files':{n:sha(root/n) for n in NAMES},'adapter_sha256':{n:sha(stage/n) for n in ['transaction.sh','native.sh']},
        'source_sha256':{str(p.relative_to(REPO)):sha(p) for p in sources()},
        'parent_proofs_sha256':{'installed-caller-session':sha(base.proof('installed-caller-session')/'SHA256SUMS')},
        'device_or_full_image_accessed':False,'local_public_assets':7,'input_public_assets':4}
    write_new(stage/'analysis.json',(json.dumps(report,indent=2)+'\n').encode());sync_dir(stage)
    (AREA/'latest-package').write_text(str(stage)+'\n');sync_dir(AREA)
    print('C107 preparer package:',report['bytes'],'bytes;',stage)

if __name__=='__main__':main()
