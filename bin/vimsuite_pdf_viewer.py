#!/usr/bin/python
import os, sys
from subprocess import call

def main():
    call(['evince', os.path.abspath(os.path.join(os.getcwd(), sys.argv[1], sys.argv[2]))])

if __name__ == '__main__':
    main()
