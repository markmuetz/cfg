import os
from pathlib import Path
import subprocess as sp
import re
import datetime as dt
from collections import defaultdict

import matplotlib
import matplotlib.pyplot as plt


def get_summary_info(*fn_globs):
    texcount_output = sp.check_output('texcount -sum -brief {}'.format(' '.join(fn_globs)).split()).decode()
    filenames = {}

    for line in texcount_output.split('\n'):
        split_line = line.split(':')
        if len(split_line) == 3:
            word_count = int(split_line[0])
            filename = split_line[2].strip()[:4]
        elif len(split_line) == 2:
            word_count = int(split_line[0])
            filename = 'totl'
        filenames[filename] = word_count

    return filenames


def parse_git_datetime(s):
    return dt.datetime.strptime(s, '%Y-%m-%d %H:%M:%S %z')


def main(args):
    orig_dir = Path.cwd()
    os.chdir(args.dir)

    try:
        assert re.search('\* master', sp.check_output('git branch'.split()).decode().strip())
        rev_list = sp.check_output('git rev-list master'.split()).decode().split('\n')

        dates = []
        counts = defaultdict(list)
        for rev in rev_list:
            sp.check_output('git checkout {}'.format(rev).split())
            filenames = get_summary_info(*args.fn_globs)
            for k, v in filenames.items():
                counts[k].append(v)
            date = parse_git_datetime(sp.check_output('git show -s --format=%ci'.split()).decode().strip())
            print(date)
            dates.append(date)

        plt.figure('counts')
        plt.title('counts')
        for k, v in counts.items():
            if args.use_date:
                plt.plot(dates[::-1], v[::-1])
            else:
                plt.plot(v[::-1])
            plt.xticks(rotation=90)
            plt.tight_layout()

        plt.show()
    finally:
        sp.call('git checkout master'.split())

    os.chdir(orig_dir)

