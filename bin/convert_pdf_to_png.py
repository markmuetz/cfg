"""Convert single file PDFs to PNGs"""
import sys
from pathlib import Path
import shutil
import subprocess as sp


def sysrun(cmd):
    return sp.run(cmd, check=True, shell=True, stdout=sp.PIPE, stderr=sp.PIPE, encoding='utf8')


def main():
    exepath = shutil.which('pdftoppm')
    if not exepath:
        print('pdftoppm not installed')
        print('sudo apt install poppler-utils')
        sys.exit(1)

    paths = [Path(p) for p in sys.argv[1:]]
    for path in paths:
        assert path.exists(), f'{path} does not exist'
        assert path.suffix == '.pdf', f'{path} is not a .pdf'

    for path in paths:
        cmd = f'pdftoppm {path} {path.stem} -png -f 1 -singlefile'
        print(cmd)
        sysrun(cmd).stdout

    sys.exit(0)
