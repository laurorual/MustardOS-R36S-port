#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Pinned SSH controller for the finite C20 helper; raw backups stay private."""
from pathlib import Path
import argparse,hashlib,ipaddress,json,os,subprocess,tempfile

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'preferences'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('action',choices=['deploy','inspect','backup','resume','partition','format','repair-root-mode','verify','restore','stop'])
p.add_argument('--host',required=True,type=ipaddress.IPv4Address);a=p.parse_args()
stage=Path((area/'latest-offline-package').read_text().strip());assert stage.is_relative_to(area)
checks=json.loads((stage/'checks.json').read_text());assert checks['passed']
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(stage/'deployment.tar')==checks['deployment_sha256']
ssh=['ssh','-p','22','-i',str(work/'private/deck-client'),'-oIdentitiesOnly=yes',
 '-oStrictHostKeyChecking=yes','-oHostKeyAlias=192.168.15.16',
 '-oUserKnownHostsFile='+str(work/'private/deck-known-hosts'),'-oBatchMode=yes',
 '-oConnectTimeout=8','-oServerAliveInterval=10','-oServerAliveCountMax=3','deck@'+str(a.host)]
base='/home/deck/muos-r35s-c20'
def remote(label,command,data=None,timeout=30):
    label_path=Path(tempfile.mkdtemp(prefix=label+'.',dir=stage))
    (label_path/'command').write_text(command+'\n')
    result=subprocess.run(ssh+[command],input=data,capture_output=True,timeout=timeout)
    (label_path/'stdout').write_bytes(result.stdout);(label_path/'stderr').write_bytes(result.stderr)
    (label_path/'exit').write_text(str(result.returncode)+'\n')
    assert result.returncode==0,(label,result.stdout.decode(errors='replace'),result.stderr.decode(errors='replace'))
    return result.stdout
def request(action,extra=''):
    command='/usr/bin/python3 '+base+'/phase4-userdata-offline-client.py '+action+extra
    raw=remote('deck-'+action,command,timeout=1250)
    response=json.loads(raw);assert response['ok'],response
    return response['result']
if a.action=='deploy':
    remote('deck-deploy','umask 077; test ! -e '+base+' && mkdir -m 700 '+base+' && tar -xf - -C '+base,
           (stage/'deployment.tar').read_bytes())
    manifest=json.loads((stage/'payload/package.json').read_text())
    files={**manifest['files'],'phase4-userdata-offline-client.py':sha(stage/'payload/phase4-userdata-offline-client.py'),
           'package.json':sha(stage/'payload/package.json')}
    command='set -eu\n'+''.join(f"printf '%s  %s\\n' {digest} {base}/{name} | sha256sum -c -\n" for name,digest in files.items())
    remote('deck-deploy-verify',command)
    print('Deck user-only package transferred and hash-verified. Root helper NOT started; no card writes by this deployment.')
elif a.action=='backup':
    assert not (stage/'independent-backup.json').exists(),'Never overwrite independent recovery evidence'
    result=request('backup');assert result['backup_bytes']==671088640
    destination=Path(tempfile.mkdtemp(prefix='c20-backup.',dir=work/'private'));destination.chmod(0o700)
    path=destination/'prefix.backup'
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as output:
        # SSH compression reduces network traffic without exposing raw bytes to logs.
        done=subprocess.run(ssh[:-1]+['-C',ssh[-1],'cat /home/deck/muos-r35s-c20-private/prefix.backup'],
                            stdout=output,stderr=subprocess.PIPE,timeout=600)
        output.flush();os.fsync(output.fileno())
    assert done.returncode==0,done.stderr
    assert path.stat().st_size==671088640 and sha(path)==result['sha256'],'Independent backup differs'
    record={**result,'host_private_copy':str(path),'host_copy_sha256_verified':True,
            'deployment_sha256':checks['deployment_sha256']}
    (destination/'backup.json').write_text(json.dumps(record,indent=2)+'\n');(destination/'backup.json').chmod(0o600)
    (stage/'independent-backup.json').write_text(json.dumps(record,indent=2)+'\n')
    ack=request('ack-backup',' --sha256 '+result['sha256']);assert ack['independent_backup_acknowledged']
    print('Private640MiB backup verified on Deck and this host; digest acknowledged. No card writes yet.')
else:
    if a.action in ('resume','partition','format','repair-root-mode','verify','restore'):
        record=json.loads((stage/'independent-backup.json').read_text());path=Path(record['host_private_copy'])
        assert path.is_relative_to(work/'private') and not path.is_symlink()
        assert record['deployment_sha256']==checks['deployment_sha256'] and sha(path)==record['sha256']
    result=request(a.action)
    if a.action=='resume':
        assert result['resumed_readonly'] and result['sha256']==record['sha256']
        ack=request('ack-backup',' --sha256 '+record['sha256']);assert ack['independent_backup_acknowledged']
    if a.action=='inspect':
        print(json.dumps({n:result.get(n) for n in ['euid','architecture','dmi_product','cards','helper_state',
                                                 'mbr_phase','data_probe','raw_inspection_error']},indent=2))
    else:print(json.dumps(result,indent=2))
