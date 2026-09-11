Claude Code: global CLAUDE.md, pixi and gh
==========================================

What was done on JASMIN (Sept 2026), to repeat on each other machine.


1. pixi on PATH (arrives with cfg)
----------------------------------

`.shrc.common` prepends `~/.pixi/bin` to PATH if the directory exists, so
nothing to do beyond updating cfg (`cfg-install`) and starting a new shell.

If pixi itself is missing:

    curl -fsSL https://pixi.sh/install.sh | sh

(The installer offers to edit `.bashrc` -- decline; `.shrc.common` already
handles PATH. On JASMIN, point the cache at scratch in
`~/.config/pixi/config.toml`: `[cache] root = "/work/scratch-nopw2/mmuetz/pixi-cache"`.)


2. gh (GitHub CLI) via pixi global
----------------------------------

    pixi global install gh
    gh auth status            # already logged in? (token in ~/.config/gh/hosts.yml)
    gh auth login             # if not

`~/.gitconfig` uses `gh auth git-credential` as the credential helper for
https://github.com, so `git push` fails with "could not read Username" if
`gh` is not on PATH -- that was the symptom on JASMIN.


3. Global CLAUDE.md (not tracked in place -- copy it)
-----------------------------------------------------

The canonical copy is `notes/claude/CLAUDE.md` (this directory). It tells
Claude how to drive `cfg` (bare repo, run from `$HOME`, `add -f`, public
repo), where shell config goes, and about pixi/gh.

    mkdir -p ~/.claude
    cp ~/notes/claude/CLAUDE.md ~/.claude/CLAUDE.md

If you edit `~/.claude/CLAUDE.md` on a machine, copy it back here and commit
it with cfg (`cfg add -f notes/claude/CLAUDE.md` the first time only; it is
tracked after that). Or symlink instead of copying so there is only one file:

    ln -sf ~/notes/claude/CLAUDE.md ~/.claude/CLAUDE.md
