import sys
from itertools import product
from signal import signal, SIGPIPE, SIG_DFL


# Allow piping: https://stackoverflow.com/a/30091579/54557
signal(SIGPIPE, SIG_DFL)

def usage():
    print('Usage:')
    print(sys.argv[0] + ' --var1=a,b,c --var2=1,2,3 "{var1}.{var2}"')
    sys.exit()

def main():
    if len(sys.argv) == 1:
        usage()
    args = sys.argv[1:-1]
    fmt = sys.argv[-1]
    prod_args = {}
    try:
        for arg in args:
            varname, varargs = arg.split('=')
            assert varname[:2] == '--'
            varname = varname[2:]
            varargs = varargs.split(',')
            prod_args[varname] = varargs
    except:
        usage()

    for prod in product(*prod_args.values()):
        kwargs = dict(zip(prod_args.keys(), prod))
        print(fmt.format(**kwargs))

