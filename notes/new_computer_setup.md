New Computer Setup
==================

has git
-------

    curl -fsSL https://raw.githubusercontent.com/markmuetz/cfg/master/bin/cfg-install | sh

That's it. `cfg-install` clones the bare repo to `~/.cfg`, sets the work tree to
`$HOME`, moves any colliding dotfiles into a timestamped `~/.cfg-backup/`, and
installs `~/.gitignore`. Start a new shell afterwards to pick up the `cfg`
alias.

To update an existing machine, re-run the same script -- it is idempotent and
fast-forward-only, and refuses to merge over local changes:

    cfg-install

(`cfg-check` reports whether you are behind; `cfg-install` is the remedy.)

### Day-to-day

    cfg status              # tracked files only
    cfg add -f <file>       # -f is REQUIRED, see "Why add -f" below
    cfg commit -m "..."
    cfg push

### Why `add -f`

`~/.gitignore` (installed from `gitignore.home`) ignores `*`. That is
deliberate: the work tree is your entire home directory, and this repo is
public on GitHub. Without it, one `cfg add -A` stages ~99 files including
`.ssh/` key material, `Documents/`, and `.cfg/` itself.

`status.showUntrackedFiles=no` does **not** protect you here -- it only hides
untracked files from `cfg status`, so the tree looks clean right up until you
stage a private key.

Ignoring `*` does not affect already-tracked files: they stay tracked and their
edits still show in `cfg status`. It only stops new files being swept up
automatically, so adding one is a deliberate act.

Note `cfg add -f` overrides every rule in `.gitignore`, including the explicit
`.ssh/id_*` and `*.pem` patterns. It stops the accidental mass-add, not a
determined one. Check what you are staging before you commit.

no git
------

    wget https://github.com/markmuetz/cfg/archive/master.zip -O cfg-master.zip
    unzip cfg-master.zip
    cp -a cfg-master/. "$HOME"/
    rm -rf "$HOME/.github" cfg-master cfg-master.zip

No version control this way, so no `cfg` alias and no updates -- prefer the git
route wherever possible.

macOS
-----

`cfg-install` above is all that's needed -- zsh picks up `.zshrc`/`.zprofile`,
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

    bin/cfg-install   installer/updater (POSIX sh, no bashisms)
    gitignore.home    deployed to ~/.gitignore by cfg-install

`gitignore.home` is tracked under that name rather than as `.gitignore` on
purpose: the work tree is `$HOME` in a deployment but an ordinary directory in
a development clone (e.g. `~/projects/cfg`), and a deny-all committed at the
repo root would make every `git add` in that clone need `-f` too.

`.shrc.common` must stay portable between bash and zsh -- no `shopt`, no `type
-P`, no bash prompt escapes, and use `$_shrc_host` rather than `$HOSTNAME`
(unset in zsh) or `$HOST` (unset in bash).

Site files are picked by `~/.i_am_on_jasmin` (sentinel file) or by a `case` on
`$_shrc_host` at the bottom of `.shrc.common`.
