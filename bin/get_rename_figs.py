import sys
sys.dont_write_bytecode = True
from collections import Counter
from pathlib import Path
import shutil
import subprocess as sp

def sysrun(cmd):
    return sp.run(cmd, check=True, shell=True, stdout=sp.PIPE, stderr=sp.PIPE, encoding='utf8')


def main():
    sys.path.append('.')
    try:
        from fig_data import REMOTE, FIG_DATA
    except ImportError:
        print('You must make a file called fig_data.py including REMOTE and FIG_DATA')
        raise

    assert isinstance(REMOTE, str), 'REMOTE must be a string of form <user>@<server>'
    assert isinstance(FIG_DATA, dict), 'FIG_DATA must be a dict'
    for k, v in FIG_DATA.items():
        assert isinstance(k, str) or isinstance(k, Path), f'{k} must be a string or a Path'
        assert isinstance(v, str) or isinstance(v, Path), f'{k} must be a string or a Path'

    filenames = [p.name for p in FIG_DATA.keys()]
    dups = [k for k, v in Counter(filenames).items() if v > 1]
    if dups:
        raise Exception(f'There are duplicate filenames: {dups}')

    remote_paths = ' '.join(':' + str(p) for p in FIG_DATA.keys()).strip()
    cmd = f'rsync -av {REMOTE}{remote_paths} raw'
    print(sysrun(cmd).stdout)

    rawpaths = [Path('raw') / fn for fn in filenames]
    problems = [p for p in rawpaths if not p.exists()]
    if problems:
        raise Exception(f'Some files were not copied: {problems}')

    for rawpath, dst in zip(rawpaths, FIG_DATA.values()):
        print(f'{rawpath} -> {dst}')
        shutil.copyfile(rawpath, dst)


if __name__ == '__main__':
    main()
