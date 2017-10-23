New Computer Setup
==================

    git clone --bare https://github.com/markmuetz/dotfiles .dotfiles
    alias dotfiles='/usr/bin/git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME'
    # Wont work - need to back up existing dotfiles:
    dotfiles checkout
    # Lists files to backup - mv to .dotfiles-backup
    dotfiles checkout 2>&1 | egrep "+\." | awk {'print $1'}
    # ...
    dotfiles checkout
    dotfiles config --local status.showUntrackedFiles no
