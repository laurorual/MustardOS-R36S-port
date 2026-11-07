# SPDX-License-Identifier: MIT
"""C100 additive public factory layout. Only private regular ext4 files."""
from copy import deepcopy
import os,re,stat
import phase4_initial_image as factory
import phase4_recovery_image as image
import phase4_root_recovery as recovery
from phase4_backup_core import write_new,sync_dir
from phase4_root_migration import require

C79_SHA='a09edf63ac5397b0adc5bdf7d9eb7413f6e02e7963e569b915df0ffe674d08fc'
TEMPLATE='opt/muos/share/conf/rootfs/asound.conf'
TEMPLATE_SHA='58aa042723b6935ddf81d44b47e6e960279f257e2543e0ed2626c461f585e8cb'
ADDED={'etc/asound.conf','mnt/mmc'}


def expected_tree(before):
    require(not (ADDED & set(before)) and not any(n.startswith('mnt/') for n in before),
        'Layout must be absent and original /mnt empty')
    for name in ['etc','mnt']:
        row=before[name]
        require(row['type']=='directory' and row['uid']==row['gid']==0 and row['mode']==0o755 and
            not row['xattrs'] and not row['external_xattrs'],'Unqualified layout parent')
    require(before['mnt']['links']==2,'Empty /mnt link count')
    template=before[TEMPLATE]
    require(template['type']=='regular' and template['uid']==template['gid']==0 and template['links']==1 and
        template['mode']==0o755 and template['bytes']==444 and template['sha256']==TEMPLATE_SHA and
        template['flags']=='0x80000' and not template['xattrs'] and not template['external_xattrs'],
        'Pinned public audio template metadata')
    after=deepcopy(before)
    after['etc/asound.conf']={**template,'mode':0o644}
    after['mnt/mmc']=deepcopy(before['mnt'])
    after['mnt']['links']+=1
    return after


def filesystem_identity(fd):
    text=image.debug(fd,'stats');result={}
    for name in ['Filesystem UUID','Filesystem features','Inode count','Block count','Block size','Inode size']:
        match=re.search(r'^'+name+r':\s*(.+)$',text,re.M)
        require(match is not None,'Filesystem identity fields');result[name]=match[1]
    return result


def compose(source,source_sha,size,stage):
    image.private_stage(stage)
    with image.source_image(source,source_sha,size) as original:
        before=factory.factory_scan(original,stage);expected=expected_tree(before)
        identity=filesystem_identity(original)
        payload=image.dumped(original,'dump /'+TEMPLATE+' @OUTPUT@',stage,444)
        require(recovery.hashed(payload)==TEMPLATE_SHA,'Audio template readback')
        output=stage/'factory.ext4'
        fd=os.open(output,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        try:
            image.sparse_clone(original,fd,size)
            require(image.fd_sha(fd)==source_sha,'Regular clone differs')
            asset=stage/'asound-template.dat';write_new(asset,payload)
            image.debug(fd,'write '+str(asset)+' /etc/asound.conf',True);asset.unlink()
            image.debug(fd,'mkdir /mnt/mmc',True)
            for path,kind,mode in [('etc/asound.conf',stat.S_IFREG,0o644),('mnt/mmc',stat.S_IFDIR,0o755)]:
                for field,value in [('mode','0'+format(kind|mode,'o')),('uid','0'),('gid','0')]:
                    image.debug(fd,'set_inode_field /'+path+' '+field+' '+value,True)
            os.fsync(fd)
            after=factory.factory_scan(fd,stage)
            require(after==expected,'Only two layout additions and /mnt link count may change')
            require(filesystem_identity(fd)==identity,'Filesystem UUID/features/geometry changed')
            digest=image.fd_sha(fd);require(digest!=source_sha,'Unmodified layout clone')
        finally:os.close(fd)
    # The source FD signature/hash are rechecked by the context manager before
    # any completion record is written. No seed/counter/identity provisioning.
    report={'passed':True,'schema':100,'experiment':'C100_PUBLIC_C79_LAYOUT_FACTORY','root_bytes':size,
        'source_factory_sha256':source_sha,'factory_sha256':digest,'added_paths':sorted(ADDED),
        'audio_template_sha256':TEMPLATE_SHA,'full_tree_and_metadata_readback_matched':True,
        'source_unchanged':True,'fsck_exit':0,'filesystem_identity_features_and_geometry_preserved':True,
        'factory_counter_preserved':0,'private_identity_seed_ROM_or_state_added':False,
        'seed_generated_or_loaded':False,'autostart_enabled':False,'physical_device_writer_available':False,
        'hardware_boot_or_installed_layout_qualified':False}
    for name,value in [('before-tree.json',before),('tree.json',after),('analysis.json',report)]:
        write_new(stage/name,recovery.encoded(value))
    sync_dir(stage);return report
