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

macOS
-----

The checkout above is all that's needed -- zsh picks up `.zshrc`/`.zprofile`,
which source the same `.shrc.common` as `.bashrc` does on the Linux boxes.
`.shrc.darwin` handles the macOS-specific bits and is sourced automatically.

Optional, but makes the config behave exactly as it does on Linux (GNU `ls
--color`, `dircolors`, `du --max-depth`) rather than falling back to the BSD
equivalents:

    brew install coreutils

Other things worth having:

    brew install tmux vim git

Note macOS ships bash 3.2 (2007) as `/bin/bash`. Nothing here needs bash 4+,
but `brew install bash` if a script does.


Shell config layout
-------------------

    .shrc.common      portable core: PATH, exports, aliases, ssh helpers
     |- .bashrc       bash entry:  shopt, PS1, HISTFILESIZE, bash_completion
     |- .zshrc        zsh entry:   PROMPT, SAVEHIST, compinit, bindkey
     |- .shrc.darwin  macOS:       homebrew, GNU-vs-BSD fixups
     |- .shrc.jasmin.sh / .shrc.racc.sh / .shrc.conda.sh / .shrc.monsoon.sh

`.shrc.common` must stay portable between bash and zsh -- no `shopt`, no `type
-P`, no bash prompt escapes, and use `$_shrc_host` rather than `$HOSTNAME`
(unset in zsh) or `$HOST` (unset in bash).

Site files are picked by `~/.i_am_on_jasmin` (sentinel file) or by a `case` on
`$_shrc_host` at the bottom of `.shrc.common`.
