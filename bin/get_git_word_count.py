#!/usr/bin/env python
# coding: utf-8
import os
import sys
import subprocess as sp
import re
import datetime as dt
from collections import defaultdict

import matplotlib
import matplotlib.pyplot as plt

def get_summary_info():
    texcount_output = sp.check_output('texcount main.tex'.split()).decode()
    print(texcount_output)
    words = int(re.search('Words in text: (?P<words>\d*)', texcount_output)['words'])
    caption_words = int(re.search('Words outside text \(captions, etc.\): (?P<caption_words>\d*)', texcount_output)['caption_words'])
    floats = int(re.search('Number of floats/tables/figures: (?P<floats>\d*)', texcount_output)['floats'])
    return {'words': words, 'caption_words': caption_words, 'floats': floats}

def parse_git_datetime(s):
    return dt.datetime.strptime(s, '%Y-%m-%d %H:%M:%S %z')


if __name__ == '__main__':
    orig_dir = os.getcwd()
    os.chdir(sys.argv[1])

    assert sp.check_output('git branch'.split()).decode().strip() == '* master'
    rev_list = sp.check_output('git rev-list master'.split()).decode().split('\n')

    dates = []
    counts = defaultdict(list)
    for rev in rev_list:
        sp.call('git checkout {}'.format(rev).split())
        summary_info = get_summary_info()
        for k, v in summary_info.items():
            counts[k].append(v)

        dates.append(parse_git_datetime(sp.check_output('git show -s --format=%ci'.split()).decode().strip()))

    for k, v in counts.items():
        plt.figure(k)
        plt.title(k)
        # plt.plot(v[::-1])
        plt.plot(dates[::-1], v[::-1])
        plt.xticks(rotation=90)
        plt.tight_layout()

    plt.show()
    sp.call('git checkout master'.split())

    os.chdir(orig_dir)
