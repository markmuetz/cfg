import sys
sys.dont_write_bytecode = True
from collections import Counter, defaultdict
from pathlib import Path
import re
import shutil
import subprocess as sp


def sysrun(cmd):
    return sp.run(cmd, check=True, shell=True, stdout=sp.PIPE, stderr=sp.PIPE, encoding='utf8')


def parse_rsync_stderr(stderr):
    # rsync: link_stat "/gws/nopw/j04/mcs_prime/mmuetz/data/mcs_prime_figs/mcs_local_envs/combined_filtered_radius_mcs_local_env_precursor_mean_2001-2002,2006-2020.pdf" failed: No such file or directory (2)
    pattern = """rsync: link_stat "(?P<filename>.*?)" failed: (?P<error>.*?)\n"""
    matches = re.findall(pattern, stderr)
    reasons = defaultdict(list)
    for m in matches:
        reasons[m[1]].append(m[0])
    for key, vs in reasons.items():
        print(f'{key}:')
        for v in vs:
            print('  ', v)


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
    fig_data = {Path(k): Path(v) for k, v in FIG_DATA.items()}

    infilenames = [p.name for p in fig_data.keys()]
    indups = [k for k, v in Counter(infilenames).items() if v > 1]
    if indups:
        raise Exception(f'There are duplicate input filenames: {indups}')

    outdups = [k for k, v in Counter(fig_data.values()).items() if v > 1]
    if outdups:
        raise Exception(f'There are duplicate output filenames: {outdups}')

    if REMOTE:
        remote_paths = ' '.join(':' + str(p) for p in fig_data.keys()).strip()
    else:
        remote_paths = ' '.join(str(p) for p in fig_data.keys()).strip()
    cmd = f'rsync -av {REMOTE}{remote_paths} raw'
    try:
        print(cmd)
        ret = sysrun(cmd)
        print(ret.stdout)
    except sp.CalledProcessError as cpe:
        parse_rsync_stderr(cpe.stderr)
        print('\nRSYNC ERROR:')
        print(cpe.stderr)
        return

    rawpaths = [Path('raw') / fn for fn in infilenames]
    problems = [p for p in rawpaths if not p.exists()]
    if problems:
        raise Exception(f'Some files were not copied: {problems}')

    for rawpath, dst in zip(rawpaths, fig_data.values()):
        print(f'{rawpath} -> {dst}')
        shutil.copyfile(rawpath, dst)


if __name__ == '__main__':
    main()
