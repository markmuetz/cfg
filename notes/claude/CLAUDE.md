# Global instructions

## Dotfiles: `cfg` (bare git repo, work tree = `$HOME`)

My dotfiles (`.bashrc`, `.zshrc`, `.shrc.common`, `.shrc.<site>`, `.vimrc`, `bin/`, `notes/`, ...) are tracked in a
bare repo at `~/.cfg` whose work tree is `$HOME`. Remote: https://github.com/markmuetz/cfg (**public** — never
commit secrets, keys, tokens or anything under `.ssh/`).

- `cfg` is an interactive-shell alias (`git --git-dir=$HOME/.cfg/ --work-tree=$HOME`), so it does not exist in
  non-interactive shells. Use a function instead, and **always run from `$HOME`** (from a subdirectory,
  `status`/`ls-files` are silently limited to that prefix):
  ```sh
  cd "$HOME"; G() { git --git-dir="$HOME/.cfg" --work-tree="$HOME" "$@"; }
  ```
  Don't put the command in a plain variable (`G="git ..."; $G ...` breaks under zsh).
- Before committing: `G fetch -q origin` and check `G rev-list --count HEAD..origin/main` (behind). If behind,
  `G merge --ff-only origin/main` (fine with a dirty tree as long as the incoming commits don't touch the dirty
  files), then commit, then `G push`. Branch is `main`.
- `~/.gitignore` ignores `*` (deny-all). Already-tracked files show up normally in `G status`; **new** files need
  `G add -f <file>`, deliberately and one at a time. Never `G add -A`/`G add .`. To stage edits to tracked files
  under an ignored dir (e.g. `notes/`), plain `G add` refuses — use `G add -u -- <file>`.
- Where things go: `.shrc.common` is the portable bash+zsh core (PATH, exports, aliases) — keep it POSIX-ish (no
  `shopt`, no `type -P`, no bash prompt escapes). `.bashrc`/`.zshrc` hold only shell-specific bits. Site-specific
  config lives in `.shrc.jasmin.sh`, `.shrc.racc.sh`, `.shrc.monsoon.sh`, `.shrc.darwin`. So a request to "add X
  to my bashrc" usually means `.shrc.common` (or the site file) — check the layout first.
- Commit message style: short imperative summary line ending in a period, optional body.
- Updating another machine: `cfg-install` (or `curl -fsSL
  https://raw.githubusercontent.com/markmuetz/cfg/main/bin/cfg-install | sh`). Full details:
  `~/notes/new_computer_setup.md`, `~/notes/check_cfg_up_to_date.md`.

## Global software: the `computer_setup` repo

What is installed *globally* on each machine (JASMIN, lapsedpacifist), and why, is recorded in
https://github.com/markmuetz/computer_setup (**private**; on JASMIN at `~/projects/local/computer_setup`).
Project envs are out of scope. Dotfiles stay in cfg.

- Order of preference: **uv > pixi > conda > pip**. Python CLI tools: `uv tool install`. Non-Python CLI tools:
  `pixi global install` (JASMIN) / `brew` (Mac). New project envs: uv, or pixi if they need conda-forge
  binaries. No new conda envs. Never `pip install --user`.
- When installing or removing something global: update that machine's manifest (`<machine>/pixi-global.toml`,
  `uv-tools.txt`, `Brewfile`), `TOOLS.md`, and `<machine>/changes.md`, then commit. Removals are proposed in
  `<machine>/cleanup.md` and need an explicit OK. Retired things on JASMIN go to `~/legacy/`.
- Tell installers not to edit shell rc files (`--no-modify-path`, decline the prompt). PATH lives in cfg's
  `.shrc.common`.

## Tools installed per machine

- `pixi` lives in `~/.pixi/bin` (on PATH via `.shrc.common`); global tools such as `gh` are installed with
  `pixi global install <tool>` and also land there. If `pixi`/`gh` are "not found" in a non-interactive shell, call
  them as `~/.pixi/bin/pixi` / `~/.pixi/bin/gh`.
- git's GitHub credential helper is `gh auth git-credential`, so `git push` over https needs `gh` on PATH
  (e.g. `PATH=$HOME/.pixi/bin:$PATH git push`). There is no GitHub ssh key on JASMIN.

## JASMIN (`~/.i_am_on_jasmin` exists)

- **Always use `du --apparent-size`** (e.g. `du -sh --apparent-size`, `du -s --apparent-size --block-size=1M`).
  Plain `du` on the JASMIN filesystems does not report the space that counts. It is also slow on the NFS
  home, so run it per directory with a `timeout`, or in the background.
- `$HOME` has a hard quota, and it has filled up before (Sept 2026). When it is exceeded every write fails,
  including editors and shells in other sessions. Before anything that downloads or unpacks a lot into
  `$HOME` (a conda/pixi env, a big `pip`/`uv` install), check there is room. Put caches on scratch
  (`/work/scratch-nopw2/mmuetz`), as pixi's already is.
