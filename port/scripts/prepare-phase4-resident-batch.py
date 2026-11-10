#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C122 nine small resident scripts/manifests; no ROM/ELF/full image build."""
import os,json,re,subprocess,tempfile
from phase4_resident_batch import *
from phase4_backup_core import write_new,sync_dir

def main():
    os.umask(0o077);AREA.mkdir(mode=0o700,exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='package.',dir=AREA))
    root=stage/'target'/PREFIX;root.mkdir(parents=True)
    for p in [stage/'target',stage/'target/usr',stage/'target/usr/libexec',root]:p.chmod(0o755)
    for n,b in payload().items():
        write_new(root/n,b);(root/n).chmod(0o644)
        if n.endswith('.sh'):subprocess.run(['sh','-n'],input=b,check=True)
    old=graphics.proof('manual-caller-installed')/'adapter'
    tx=(old/'transaction.sh').read_text().replace('c105','c122').replace('C105','C122')
    tx=tx.replace('usr/libexec/muos-caller',PREFIX).replace('= 17 ]','= 9 ]')
    tx=re.sub(r'c122_names\(\) \{.*?\n\}',lambda _:"c122_names() {\n    printf '%s\\n' "+' '.join(PREFIX+'/'+n for n in NAMES)+'\n}',tx,count=1,flags=re.S)
    native=(old/'native.sh').read_text().replace('c105','c122').replace('C105','C122')
    for n,text in [('transaction.sh',tx),('native.sh',native)]:write_new(stage/n,text.encode());subprocess.run(['sh','-n'],input=text,text=True,check=True)
    write_new(stage/'export.sha256',''.join(sha(root/n)+'  '+n+'\n' for n in NAMES).encode())
    r={'passed':True,'schema':122,'files':9,'directories':1,'bytes':sum((root/n).stat().st_size for n in NAMES),
      'package_files':{n:sha(root/n) for n in NAMES},'adapter_sha256':{n:sha(stage/n) for n in ['transaction.sh','native.sh']},
      'source_sha256':{str(p.relative_to(REPO)):sha(p) for p in sources()},
      'parent_proofs_sha256':{'batch-graphics':sha(graphics.proof('batch-graphics')/'SHA256SUMS')},
      'ROM_ELF_seed_or_private_identity_included':False,'full_image_built':False}
    write_new(stage/'analysis.json',(json.dumps(r,indent=2)+'\n').encode());sync_dir(stage)
    (AREA/'latest-package').write_text(str(stage)+'\n');sync_dir(AREA)
    print('C122 resident batch package:',r['bytes'],'bytes;',stage)
if __name__=='__main__':main()
