# SPDX-License-Identifier: MIT
"""C93 guarded regular-file eligibility callback for a future initial writer.

No block target, unlock or write operation. A finite physical entrypoint must
pin C79, obtain fresh current p2 bytes, and call this before Controller.apply
unlocks. Context or a caller's success flag cannot substitute for the scans.
"""
from pathlib import Path
import fcntl,os,stat
from phase4_root_migration import require,digest
import phase4_recovery_image as image
import phase4_initial_image as initial
import phase4_initial_migration as migration

def validate_fd(source,candidate_sha256,factory,factory_sha256,current,current_sha256,
                image_bytes,stage,backup_rows,backup_counter,prefix_sha256,attempt,context):
    image.private_stage(stage);digest(candidate_sha256)
    before=os.fstat(source)
    require(stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and before.st_nlink==1
        and stat.S_IMODE(before.st_mode) in (0o400,0o600) and before.st_size==image_bytes,
        'Initial candidate descriptor must be a private regular image')
    fcntl.flock(source,fcntl.LOCK_EX|fcntl.LOCK_NB)
    require(image.fd_sha(source)==candidate_sha256,'Initial candidate descriptor hash changed')
    with image.source_image(Path(factory),factory_sha256,image_bytes) as fd:baseline=initial.factory_scan(fd,stage)
    with image.source_image(Path(current),current_sha256,image_bytes) as fd:observed=image.scan(fd,stage)
    candidate=image.scan(source,stage)
    plan=migration.eligibility(baseline,observed,candidate,backup_rows,backup_counter,prefix_sha256,
        attempt,context,current_sha256,image_bytes)
    require(image.signature(os.fstat(source))==image.signature(before) and
        image.fd_sha(source)==candidate_sha256,'Initial candidate changed during descriptor validation')
    return plan
