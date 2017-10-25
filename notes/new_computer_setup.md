New Computer Setup
==================

has git
-------

    git clone --bare https://github.com/markmuetz/cfg .cfg
    alias cfg='/usr/bin/git --git-dir=$HOME/.cfg/ --work-tree=$HOME'
    cfg config --local status.showUntrackedFiles no

    # Wont work - need to back up existing cfg:
    cfg checkout
    # Lists files to backup - mv to .cfg-backup
    mkdir .cfg-backup
    cfg checkout 2>&1 | egrep "+\." | awk {'print $1'}
    # mv .bashrc .cfg-backup
    # ...
    cfg checkout

no git
------

    wget https://github.com/markmuetz/cfg/archive/master.zip -O cfg-master.zip
    unzip cfg-master.zip
    cd cfg-master
    cp -r .
