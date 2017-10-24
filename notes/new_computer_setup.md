New Computer Setup
==================

has git
-------

    git clone --bare https://github.com/markmuetz/dotfiles .dotfiles
    alias dotfiles='/usr/bin/git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME'
    dotfiles config --local status.showUntrackedFiles no

    # Wont work - need to back up existing dotfiles:
    dotfiles checkout
    # Lists files to backup - mv to .dotfiles-backup
    mkdir .dotfiles-backup
    dotfiles checkout 2>&1 | egrep "+\." | awk {'print $1'}
    # mv .bashrc .dotfiles-backup
    # ...
    dotfiles checkout

no git
------

    wget https://github.com/markmuetz/dotfiles/archive/master.zip -O dotfiles-master.zip
    unzip dotfiles-master.zip
    cd dotfiles-master
    cp -r .
