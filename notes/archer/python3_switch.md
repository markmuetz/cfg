12/12/17
========

In preparation for switching to Python 3, I have been trying to create a new env based on python3.6
with iris. 

Steps
-----

First, edit `~/.condarc`. This should move pkgs into work dir but I'm not sure it's working.

    pkgs_dirs:
        - /work/n02/n02/mmuetz/conda/pkgs

Then:

    conda create --prefix ~/work/conda/envs/iris3 python=3.6
    source activate /home/n02/n02/mmuetz/work/conda/envs/iris36
    conda install -c conda-forge iris
    conda install ipython

    pip install pyshp
    ipython

>>>

    import iris

Problems
--------

* pyshp not installed correctly: `import shapefile` does not work on `import iris`
* `readline` not found, to fix (downgrades to python 3.6.2, destroyed when something else upgrades python):


    * `conda remove --force python`
    * `conda install -c anaconda python`

Solutions
---------

Tried: https://github.com/ContinuumIO/anaconda-issues/issues/152#issuecomment-225214743
to fix readline problem. Didn't work.

Upgrading my repos
==================

for all of my Python repos (omnium, scaffold_analysis, cosar_analysis, cloud_tracking), I have made
a new branch called python3_upgrade. omnium tests are almost all passing, and I've switched to that
branch for each repo on ARCHER. e.g. omnium ls-analysers is working and finding all the analysers.

I am hitting a problem with interactive plotting in ipython:

    ImportError: /lib64/libpthread.so.0: version `GLIBC_2.12' not found (required by
    /home/n02/n02/mmuetz/work/conda/envs/iris36/lib/python3.6/site-packages/PyQt5/../../.././libglib-2.0.so.0)

on `import pylab as plt`.
A workaround is to:

    import matplotlib
    matplotlib.use('agg')

First thing, then output pngs.
