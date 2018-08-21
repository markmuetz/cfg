#!/usr/bin/env python
import sys
from configparser import RawConfigParser


def read_rose_cp(fn):
    cp = RawConfigParser()
    with open(fn, 'r') as f:
        metaline = f.readline()
        metaval = metaline.split('=')[1].strip()

        while f.readline() != '\n':
            pass
        cp.read_file(f)
    return metaval, cp


def compare_sections(sec1, sec2, cpdiff):
    sec1 = cp1[sec]
    sec2 = cp2[sec]
    cpdiff.add_section(sec)
    items1 = sec1.items()
    try:
        for name1, val1 in items1:
            if name1[:2] == '!!':
                basename = name1[2:]
            else:
                basename = name1
            if basename in sec2:
                name2 = basename
                val2 = sec2[basename]
            elif '!!' + basename in sec2:
                name2 = '!!' + basename
                val2 = sec2['!!' + basename]
            else:
                print('Cant find {} in cp2'.format(basename))
            diff = item_diff((name1, val1), (name2, val2))
            if diff:
                cpdiff.set(sec, basename, diff)
    except Exception as e:
        print(sec)
        print(e)


def item_diff(i1, i2):
    n1, v1 = i1
    n2, v2 = i2
    if n1[:2] == '!!' or n2[:2] == '!!':
        return None
    if v1 == v2:
        return None
    return '{}:{}'.format(v1, v2)


if __name__ == '__main__':
    suite1 = sys.argv[1]
    suite2 = sys.argv[2]

    metaval1, cp1 = read_rose_cp('{}/app/um/rose-app.conf'.format(suite1))
    metaval2, cp2 = read_rose_cp('{}/app/um/rose-app.conf'.format(suite2))
    if metaval1 != metaval2:
        print('WARNING: comparing different metavals')
        print(metaval1)
        print(metaval2)
        print()
    cpdiff = RawConfigParser()

    secs1 = set(cp1.sections())
    secs2 = set(cp2.sections())
    # Common sections.
    sboth = secs1 & secs2

    for sec in sboth:
        if sec[:2] == '!!':
            continue
        compare_sections(cp1[sec], cp2[sec], cpdiff)

    for sec in cpdiff.sections():
        if len(cpdiff[sec]) == 0:
            cpdiff.remove_section(sec)

    output_fn = 'rose-app.um.{}_{}.diff.conf'.format(suite1, suite2) 
    print('Writing to {}'.format(output_fn))
    with open(output_fn, 'w') as f:
        cpdiff.write(f)
