#!/usr/bin/env python
import sys
import subprocess as sp
import re

# e.g. https://code.metoffice.gov.uk/svn/roses-u/a/t/1/0/1/trunk
URL_TPL = 'https://code.metoffice.gov.uk/svn/roses-{}/trunk'

def main(suite_name):
    assert re.match('u-[a-z][a-z]\d\d\d', suite_name)

    suite_name_for_url = '/'.join(suite_name.replace('-', ''))
    suite_url = URL_TPL.format(suite_name_for_url)
    # e.g. fcm co https://code.metoffice.gov.uk/svn/roses-u/a/t/1/0/1/trunk u-at101
    cmd = 'fcm co {} {}'.format(suite_url, suite_name)
    print(cmd)
    sp.call(cmd.split())

if __name__ == '__main__':
    main(sys.argv[1])
