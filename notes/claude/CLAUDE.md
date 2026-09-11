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

## Tools installed per machine

- `pixi` lives in `~/.pixi/bin` (on PATH via `.shrc.common`); global tools such as `gh` are installed with
  `pixi global install <tool>` and also land there. If `pixi`/`gh` are "not found" in a non-interactive shell, call
  them as `~/.pixi/bin/pixi` / `~/.pixi/bin/gh`.
- git's GitHub credential helper is `gh auth git-credential`, so `git push` over https needs `gh` on PATH
  (e.g. `PATH=$HOME/.pixi/bin:$PATH git push`). There is no GitHub ssh key on JASMIN.
