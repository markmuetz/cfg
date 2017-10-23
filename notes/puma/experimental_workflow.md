Experimental workflow
=====================

Build/recon base model
----------------------

Turn on build, recon and turn off run. `fcm commit` with base name. Build base dir:

    rose suite-run -n u-af095_64x64km2_1km_base --no-gcontrol

This can take 1 hour, perhaps up to 6 hours if serial queue is being exceptionally slow.

Setup expt dirs on Archer
-------------------------

On Archer (login.archer.ac.uk), copy `~/work/cylc-run/u-af095_64x64km2_1km_base` to new dirs, e.g.:
`~/work/cylc-run/u-af095_64x64km2_1km_expt1`.

Run expts
---------

Turn off build, recon and turn on run. Make changes, fcm commit then run expts, e.g.:

    rose suite-run -n u-af095_64x64km2_1km_expt1 --no-gcontrol

N.B. certain changes (e.g. turning off graupel) will require recon.

Post process on RDF
===================

Archive runs to RDF
-------------------

Once expts have ended, copy to RDF:

    cd ~/nerc/um10.5_runs/<expt_group>
    rsync -av --progress ~/work/cylc-run/u-af095_64x64km2_1km_expt* .

(N.B. try to avoid copying base, and this can take a while (~30 mins)).

Delete from work (N.B. deleting takes a few minutes):

    cd ~/work/cylc-run/
    rm -rf u-af095_64x64km2_1km_expt*

Post process
------------

On RDF (login.rdf.ac.uk):

    cd omnis/u-af095_64x64km2_1km_expt_group
    omni gen-node-graph
    omni process

Post process on ARCHER
======================

Post process
------------

On ARCHER: TODO

* How to launch runs?
* Where should output go?
* How to archive to RDF?
* cylc integration?
