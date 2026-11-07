# SPDX-License-Identifier: MIT
"""C88 first-boot private image provisioning. Regular ext4 files only.

The exact factory SHA is bound by the host to C79; private state comes from
the independently verified offline reference. No physical entrypoint/fence.
"""
from pathlib import Path
from copy import deepcopy
import os,re,stat
from phase4_root_migration import require
from phase4_backup_core import parse_stat,sync_dir,write_new
import phase4_root_recovery as recovery
import phase4_recovery_image as image

NEW_DIRS={'var/lib/muos-network','var/lib/muos-seedrng'}

def factory_scan(fd,stage):
    """Read the public factory tree without inventing private identity/counter.

    C79 has no xattrs or special inodes. Refuse a future factory with either
    until qualified; provisioned readback uses the existing full C85 scanner.
    """
    image.private_stage(stage);image.command(['e2fsck','-fn','/proc/self/fd/'+str(fd)],fd,180)
    records={};seen=set();cache={};budget=0
    def walk(number,path,depth):
        nonlocal budget
        require(depth<=32 and len(records)<8192,'Factory traversal bounds')
        if number in cache:row=cache[number]
        else:
            text=image.debug(fd,'stat <'+str(number)+'>');info=parse_stat(text)
            require(info['type'] in ('regular','directory','symlink'),'Unqualified factory inode type')
            require('Extended attributes:' not in text and re.search(r'^File ACL: 0$',text,re.M),'Unqualified factory xattrs')
            flags=re.search(r'Flags: (0x[0-9a-f]+)',text);require(flags is not None,'Factory inode flags')
            row={k:v for k,v in info.items() if k!='bytes'}
            row.update({'flags':flags[1],'external_xattrs':False,'xattrs':{}})
            if info['type']=='regular':
                budget+=info['bytes'];require(info['bytes']<=64*1024*1024 and budget<=768*1024*1024,'Factory payload bounds')
                data=image.dumped(fd,'dump <'+str(number)+'> @OUTPUT@',stage,info['bytes'])
                row.update({'bytes':len(data),'sha256':recovery.hashed(data)})
            elif info['type']=='symlink':
                match=re.search(r'^Fast link dest: "(.*)"$',text,re.M)
                data=match[1].encode() if match else image.dumped(fd,'dump <'+str(number)+'> @OUTPUT@',stage,info['bytes'])
                require(len(data)==info['bytes'] and len(data)<=4096,'Factory symlink bound');row['target_hex']=data.hex()
            cache[number]=row
        records[path]=row
        if row['type']=='directory':
            require(number not in seen,'Factory directory alias');seen.add(number)
            for name,child in image.entries(image.debug(fd,'ls -p <'+str(number)+'>')):
                require(not name.endswith('.once') and not re.fullmatch(r'c(?:12|25)\.used(?:[.].*)?',name),'Runtime marker in factory')
                walk(child,(path+'/' if path else '')+name,depth+1)
    walk(2,'',0)
    for name,mode in image.PARENTS.items():
        if name in NEW_DIRS:require(name not in records,'Factory already provisioned');continue
        row=records.get(name,{})
        require(row.get('type')=='directory' and row['uid']==row['gid']==0 and row['mode']==mode,'Factory private ancestor')
    private=set(records)&(recovery.PRIVATE_FILES|recovery.OPTIONAL_PRIVATE)
    require(private=={'etc/muos-network-authorized_key',recovery.COUNTER},'Factory private inventory')
    counter=records[recovery.COUNTER]
    require(counter['type']=='regular' and counter['links']==1 and counter['uid']==counter['gid']==0
        and counter['mode']==0o600 and counter['sha256']==recovery.hashed(b'0\n'),'Factory fresh counter')
    auth=records['etc/muos-network-authorized_key']
    require(auth['type']=='regular' and auth['links']==1 and auth['uid']==auth['gid']==0 and auth['mode']==0o644,'Factory public key placeholder')
    return records

def public_expected(factory,history):
    tree=deepcopy(factory)
    for n in recovery.PRIVATE_FILES|recovery.OPTIONAL_PRIVATE:tree.pop(n,None)
    # Only these two newly created subdirectories change the parent's nlink.
    tree['var/lib']['links']+=2
    return tree

def compose(factory,factory_sha256,reference,reference_sha256,image_bytes,stage,private_rows,counter):
    image.private_stage(stage);recovery.manifest(private_rows,counter,True)
    with image.source_image(factory,factory_sha256,image_bytes) as source:
        baseline=factory_scan(source,stage)
        with image.source_image(reference,reference_sha256,image_bytes) as backup:
            captured=image.scan(backup,stage)
        require(captured['private_files']==private_rows and captured['boot_sequence']==counter,'Fresh offline reference binding')
        history={n:row for n,row in captured['tree'].items() if image.historical_marker(n)}
        require(all(not r['xattrs'] and not r['external_xattrs'] for r in history.values()),'Unqualified historical marker xattrs')
        payload=dict(captured['payloads'])
        for n,row in history.items():
            data=b'MUOS-C12-ONCE\n' if n.endswith('/c12.used') else f'MUOS-C25-ONCE\nBOOT={int(n[-4:])}\n'.encode()
            require(recovery.hashed(data)==row['sha256'],'Historical marker readback binding');payload[n]=data
        output=stage/'candidate.ext4';fd=os.open(output,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        try:
            image.sparse_clone(source,fd,image_bytes);require(image.fd_sha(fd)==factory_sha256,'Factory clone differs')
            for n in ['etc/muos-network-authorized_key',recovery.COUNTER]:image.debug(fd,'rm /'+n,True)
            for n in sorted(NEW_DIRS):
                image.debug(fd,'mkdir /'+n,True)
                for field,value in [('mode','040700'),('uid','0'),('gid','0')]:image.debug(fd,'set_inode_field /'+n+' '+field+' '+value,True)
            for index,(name,data) in enumerate(sorted(payload.items())):
                require(name in recovery.PRIVATE_FILES|recovery.OPTIONAL_PRIVATE or image.historical_marker(name),'Fixed provision allowlist')
                asset=stage/('payload-%02d.dat'%index);write_new(asset,data)
                image.debug(fd,'write '+str(asset)+' /'+name,True);asset.unlink()
                mode=private_rows[name]['mode'] if name in private_rows else 0o600
                for field,value in [('mode','0'+format(stat.S_IFREG|mode,'o')),('uid','0'),('gid','0')]:
                    image.debug(fd,'set_inode_field /'+name+' '+field+' '+value,True)
                for attr,value in captured['attrs'].get(name,{}).items():
                    asset=stage/'attribute.dat';write_new(asset,value)
                    image.debug(fd,'ea_set -f '+str(asset)+' /'+name+' '+attr,True);asset.unlink()
            os.fsync(fd);after=image.scan(fd,stage)
            excluded=(recovery.PRIVATE_FILES|recovery.OPTIONAL_PRIVATE|NEW_DIRS|set(history))
            actual={n:r for n,r in after['tree'].items() if n not in excluded}
            require(actual==public_expected(baseline,history),'Factory public tree/metadata changed')
            require(after['private_files']==private_rows and after['boot_sequence']==counter,'Private state/counter changed')
            require(all(after['payloads'][n]==data for n,data in captured['payloads'].items()),'Private payload readback')
            require(after['attrs']==captured['attrs'],'Private xattrs changed')
            require({n:r for n,r in after['tree'].items() if image.historical_marker(n)}==history,'Consumed markers changed')
            for n in NEW_DIRS:
                row=after['tree'][n];require(row['links']==2 and not row['xattrs'] and not row['external_xattrs'],'New private directory metadata')
            digest=image.fd_sha(fd);require(digest!=factory_sha256,'Unprovisioned clone')
        finally:os.close(fd)
    sync_dir(stage)
    result={'passed':True,'schema':88,'candidate_provisioned':True,'candidate_sha256':digest,'root_bytes':image_bytes,
        'counter_preserved':counter,'private_file_count':len(private_rows),'historical_marker_count':len(history),
        'factory_public_tree_and_metadata_preserved':True,'private_payloads_and_xattrs_readback_verified':True,
        'source_images_unchanged':True,'root_fsck_exit':0,'seed_generated_or_loaded':False,'host_keys_generated':False,
        'physical_card_writer_available':False,'boot_handoff_authorized':False,'handoff_fence_created':False}
    write_new(stage/'tree.json',recovery.encoded(after['tree']))
    write_new(stage/'private-files.json',recovery.encoded(after['private_files']))
    write_new(stage/'analysis.json',recovery.encoded(result));return result
