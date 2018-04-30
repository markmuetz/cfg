ARCHER appears to be running a pretty old version of glibc:

    mmuetz@eslogin007 ~ $ ldd --version
    ldd (GNU libc) 2.11.3
    Copyright (C) 2009 Free Software Foundation, Inc.
    This is free software; see the source for copying conditions.  There is NO
    warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    Written by Roland McGrath and Ulrich Drepper.

This is from 2010: https://sourceware.org/glibc/wiki/Glibc%20Timeline.

This means that e.g. Qt will not run, and has I think been causing me problems installing
iris from source. It means I may have to build iris if I want to use it.
