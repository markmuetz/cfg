rosie
=====

Run rosie (locally on puma):

    rosie go --prefix=puma

Run rose (needs MOSRS access):

    rosie go

rose useful commands
====================

Start from scratch:

    rose suite-run --new

Run with a given name (e.g. goes to archer:~/work/cylc-run/<name>):

    rose suite-run -n <name>

No cylc:

    rose suite-run -n u-af095_64x64km2_1km_base --no-gcontrol

Shutdown:

    rose suite-shutdown -n u-af095_64x64km2_1km_no_graupel -y
