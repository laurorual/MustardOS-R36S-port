#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C101 finite path guards and real deletion in disposable regular directories."""
from pathlib import Path
from copy import deepcopy
import importlib,json,os,tempfile
from unittest.mock import patch
from phase4_backup_core import write_new,sync_dir,sha


def main():
    c=importlib.import_module('phase4-deck-cleanup');cases=[]
    good=[{'path':'/home/deck/muos-r35s-c81','uid':1000,'kind':'directory','mode':0o700}]
    assert c.validate_paths(good,1000)=={good[0]['path']};cases.append('finite-valid-project-root')
    for name,key,value in [('foreign-home','path','/home/deck/Documents'),('nested-path','path','/home/deck/muos-r35s-c81/subdir'),
        ('outside-parent','path','/etc/muos-r35s-c81'),('traversal','path','/home/deck/../muos-r35s-c81'),
        ('wrong-name','path','/home/deck/muos-r35s-other'),('root-alias','kind','symlink'),('wrong-owner','uid',1001),
        ('unsafe-mode','mode',0o777)]:
        bad=deepcopy(good);bad[0][key]=value
        try:c.validate_paths(bad,1000)
        except ValueError:cases.append(name)
        else:raise AssertionError(name)
    for name,rows in [('empty-plan',[]),('duplicate-plan',good+good)]:
        try:c.validate_paths(rows,1000)
        except ValueError:cases.append(name)
        else:raise AssertionError(name)
    os.umask(0o077)
    repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/deck-cleanup-current'
    area.mkdir(mode=0o700,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='fixture.',dir=area) as tmp:
        p=Path(tmp);outside=p/'preserve';outside.mkdir();(outside/'data').write_text('untouched')
        target=p/'muos-r35s-c81';target.mkdir();(target/'data').write_text('remove')
        (target/'external-link').symlink_to(outside,target_is_directory=True)
        rows=[{'path':str(target),'uid':os.getuid(),'mode':0o700,'kind':'directory'}]
        ids,_=c.check_roots(rows);c.erase(rows,ids)
        assert not target.exists() and (outside/'data').read_text()=='untouched';cases.append('real-deletion-does-not-follow-external-symlink')
        target.mkdir();ids,_=c.check_roots(rows);target.rename(p/'old');target.symlink_to(outside,target_is_directory=True)
        try:c.erase(rows,ids)
        except ValueError:cases.append('root-swap-refused-before-deletion')
        else:raise AssertionError('root-swap')
        assert (outside/'data').read_text()=='untouched'
        with patch.object(c.shutil.rmtree,'avoids_symlink_attacks',False):
            try:c.erase([], {})
            except ValueError:cases.append('unsafe-platform-removal-refused')
            else:raise AssertionError('unsafe-platform')
    stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area))
    write_new(stage/'analysis.json',(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,
        'Deck_or_media_accessed':False,'source_sha256':{str(q.relative_to(repo)):sha(q) for q in [Path(__file__),Path(c.__file__)]}},indent=2)+'\n').encode())
    sync_dir(stage);(area/'latest-checks').write_text(str(stage)+'\n');sync_dir(area)
    print('C101',len(cases),'cleanup checks passed:',stage)


if __name__=='__main__':main()
