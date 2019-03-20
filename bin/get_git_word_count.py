#!/usr/bin/env python
# coding: utf-8
import os
import sys
import subprocess as sp
import re
import datetime as dt

import matplotlib
matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt

def get_word_count():
    return int(re.search('Words in text: (?P<word_count>\d*)', sp.check_output('texcount main.tex'.split()).decode())['word_count'])

def parse_git_datetime(s):
    return dt.datetime.strptime(s, '%Y-%m-%d %H:%M:%S %z')


if __name__ == '__main__':
    orig_dir = os.getcwd()
    os.chdir(sys.argv[1])

    assert sp.check_output('git branch'.split()).decode().strip() == '* master'

    rev_list = sp.check_output('git rev-list master'.split()).decode().split('\n')

    dates = []
    word_count = []
    for rev in rev_list:
        sp.call('git checkout {}'.format(rev).split())
        word_count.append(get_word_count())
        dates.append(parse_git_datetime(sp.check_output('git show -s --format=%ci'.split()).decode().strip()))

    plt.plot(dates[::-1], word_count[::-1])
    plt.show()
    sp.call('git checkout master'.split())

    os.chdir(orig_dir)

