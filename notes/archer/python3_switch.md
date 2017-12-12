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
* `readline` not found, to fix (downgrades to python 3.6.2):

    conda remove --force python
    conda install -c anaconda python

Solutions
---------

Tried: https://github.com/ContinuumIO/anaconda-issues/issues/152#issuecomment-225214743
to fix readline problem. Didn't work.
