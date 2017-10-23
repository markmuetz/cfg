rose opts
=========

What is it
----------

rose has a way of providing options that will override a configuration: [optional
configuration](http://metomi.github.io/rose/doc/rose-configuration.html#opts).  If your base
configuration is in e.g. `app/um/rose-app.conf`, optional configuration should go in e.g.
`app/um/opt/rose-app-opt1_change_value.conf`. You can tell the main configuration to use the options
by putting an `opts=opt1_change_value` line in the configuration root, i.e. in a `[]` section:

    []
    opts=opt1_change_value

There are other other ways of loading it: using `--opt-conf-key=opt1_change_value` or `-O
opt1_change_value`, or settings env vars (see link above). The options files can be required (as in
above example) or optional, e.g. `opts=opt_req (opt_optional)`.

Have a look in the `conf` dir to see examples of opt usage:

    cd conf
    rose config --file=rose-app.conf
    # Uncomment opts=opt1_change_value
    rose config --file=rose-app.conf
    # Recomment above, uncomment opts=opt1_change_value opt2_extra_sec
    rose config --file=rose-app.conf

In practice, you will probably just want to look at one section:

    rose config --file=rose-app.conf section_name

Why it's useful
---------------

This can be used to run multiple experiments with minor changes between them. You could have one
base config with e.g. 3 optional configs in the `opt` dir, then change the base config to point at
each of them in turn (`fcm commit`ing in between). The commit diff log will be very easy to follow,
and combined with sensible `rose suite-run -n <expt_name`, should make it easy to tie UM output to
the rose configuration files in the commit log.
