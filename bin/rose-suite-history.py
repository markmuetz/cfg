#!/usr/bin/env python
import os
import sys
import re
from glob import glob


def suite_history(suite_dir):
    # rose_suite_dirs = sorted([d for d in glob('u-?????') if os.path.isdir(d)])
    # print(rose_suite_dirs)
    with open(os.path.join(suite_dir, 'rose-suite.info')) as f:
        lines = f.readlines()
        # print(lines)
    if lines[0].split('=')[0] != 'description':
        return
    desc = lines[0].split('=')[1].strip()
    m = re.search('copy of (?P<suite_name>u-\w\w\d\d\d)/trunk@(?P<rev>\d*)', 
                  desc, re.IGNORECASE)

    if not m:
        return
    # print(desc)
    split_desc = desc.split(' ')
    from_desc = split_desc[2]
    from_suite = m.groups()[0]
    print(from_suite)
    if os.path.exists(from_suite):
        suite_history(from_suite)


if __name__ == '__main__':
    suite_history(sys.argv[1])
