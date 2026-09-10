Checking a machine's cfg deployment is up to date
=================================================

For an agent (or me) landing on JASMIN, RACC, Monsoon or one of the Linux
boxes and needing to know whether the dotfiles there are current.

The dotfiles live in a bare repo at `~/.cfg` whose work tree is `$HOME`.
There is no ordinary checkout to `cd` into, which is what makes the checks
below less obvious than they look.


The check
---------

Paste this whole block. It works under bash and zsh, and from any directory:

    cd "$HOME" || exit 1
    G() { git --git-dir="$HOME/.cfg" --work-tree="$HOME" "$@"; }
    G fetch -q origin
    echo "HEAD          $(G rev-parse --short HEAD)"
    echo "origin/master $(G rev-parse --short origin/master)"
    echo "behind        $(G rev-list --count HEAD..origin/master)"
    echo "ahead         $(G rev-list --count origin/master..HEAD)"
    echo "dirty         $(G status --porcelain | wc -l | tr -d ' ')"

Up to date means: `behind 0`, `ahead 0`, `dirty 0`.

If the machine has a shell started since the last deployment, `cfg-check`
does a cut-down version of the same thing.


Two traps, both of which have already caused wrong answers
----------------------------------------------------------

**1. Run it from `$HOME`.** Git limits `ls-files`, `ls-tree` and `status`
to the current directory's prefix when the cwd is inside the work tree.
The work tree here is `$HOME`, so running a check from, say,
`~/projects/cfg/bin` reports 0 tracked files and an empty status on a
perfectly healthy install. Hence the `cd "$HOME"` on the first line. This
is not hypothetical: it produced a confident "nothing is deployed" reading
on a machine where all 238 files were in fact deployed.

**2. Don't put the git invocation in a plain variable.** In zsh an
unquoted parameter is not word-split, so

    G="git --git-dir=$HOME/.cfg --work-tree=$HOME"    # BROKEN under zsh
    $G rev-parse HEAD

fails with "no such file or directory: git --git-dir=...". Use a shell
function, as above. (Works in bash, fails in zsh -- and JASMIN is bash
while the Mac is zsh, so test the shell you are actually in.)


If it is behind
---------------

    curl -fsSL https://raw.githubusercontent.com/markmuetz/cfg/master/bin/cfg-install | sh

`cfg-install` is idempotent and fast-forward-only, and is the update path
as well as the installer. It also repairs older deployments in passing: it
sets the `remote.origin.fetch` refspec that `git clone --bare` omits
(without which there are no remote-tracking refs, so `behind`/`ahead`
above cannot be computed at all), and installs `~/.gitignore`.

If the box has no outbound HTTPS, use the checked-out copy instead:

    cd "$HOME" && sh ~/bin/cfg-install

Note the raw.githubusercontent.com URL is CDN-cached for a few minutes
after a push. If a fix was just committed, confirm it is in the copy you
are about to run before trusting it.


If it is dirty
--------------

`cfg-install` will refuse to merge and leave the tree alone -- that is
correct, not a failure. Inspect and decide:

    cd "$HOME"
    G status
    G diff
    # then either
    G commit -am "..." && G push
    # or
    G checkout -- <file>

Then re-run `cfg-install`.

Untracked files that an incoming commit wants to create are handled
automatically: `cfg-install` moves them to `~/.cfg-backup/<timestamp>/`
and carries on. Nothing is ever deleted.


JASMIN specifics
----------------

- Site config is `~/.shrc.jasmin.sh` (it was `~/.bashrc.jasmin.sh` before
  Sept 2026 -- a machine still showing the old name is behind).
- It is sourced only when `~/.i_am_on_jasmin` exists. That sentinel file
  is untracked and per-machine, so it does not arrive with an update. If
  the "Setting up JASMIN" banner stops appearing, `touch
  ~/.i_am_on_jasmin`.
- `~/.compname` and `~/.username` are also untracked and per-machine.
  Without them the prompt falls back to the real hostname and to
  `markmuetz`. On JASMIN: `echo mmuetz > ~/.username` if you want the
  local account shown.
- JASMIN is bash. `.zshrc`/`.zprofile` will be checked out there and sit
  inert; that is expected, not a sign of a bad deployment.
