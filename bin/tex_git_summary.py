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
            # Hack to make ch01_introduction appear the same as ch01 (deals with renames).
            filename = split_line[2].strip()[:4]
        elif len(split_line) == 2:
            word_count = int(split_line[0])
            filename = 'totl'
        filenames[filename] = word_count

    return filenames


def parse_git_datetime(s):
    return dt.datetime.strptime(s, '%Y-%m-%d %H:%M:%S %z')


def main(tex_dir, fn_globs, use_tags, use_date):
    orig_dir = Path.cwd()
    os.chdir(tex_dir)

    try:
        assert re.search('\* master', sp.check_output('git branch'.split()).decode().strip())
        if use_tags:
            rev_list = sp.check_output('git tag --sort=committerdate'.split()).decode().split('\n')[::-1]
        else:
            rev_list = sp.check_output('git rev-list master'.split()).decode().split('\n')

        dates_for_fn = defaultdict(list)
        counts_for_fn = defaultdict(list)
        all_dates = {}
        counter = 0

        for rev in rev_list:
            sp.run('git checkout {} 1>/dev/null'.format(rev), stdout=sp.DEVNULL, stderr=sp.DEVNULL, shell=True)
            date = parse_git_datetime(sp.check_output('git show -s --format=%ci'.split()).decode().strip())
            print(f'{rev}: {date}')

            fn_counts = get_summary_info(*fn_globs)
            for fn, count in fn_counts.items():
                counts_for_fn[fn].append(count)
                dates_for_fn[fn].append(date)
                if date not in all_dates:
                    all_dates[date] = counter
                    counter += 1

        plt.figure('counts')
        plt.title('counts')
        for fn, counts in counts_for_fn.items():
            dates = dates_for_fn[fn]
            if use_date:
                plt.plot(dates[::-1], counts[::-1], label=fn)
            else:
                commits = [all_dates[date] for date in dates]
                plt.plot(commits, counts[::-1], label=fn)
        plt.legend()
        if use_date:
            plt.xticks(rotation=90)
        plt.tight_layout()

        plt.show()
    finally:
        sp.call('git checkout master'.split())

    os.chdir(orig_dir)
