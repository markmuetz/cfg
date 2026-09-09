# zsh entry point. Everything portable lives in ~/.shrc.common, which is shared
# with ~/.bashrc; this file holds only the zsh-specific bits.
#
# Much of this is a port of settings that are bash/readline-only:
#   - PS1 (bash escapes)      -> PROMPT (zsh % escapes)
#   - HISTFILESIZE            -> SAVEHIST
#   - /etc/bash_completion    -> compinit
#   - ~/.inputrc              -> bindkey/zstyle, see "Key bindings" below

# If not running interactively, don't do anything.
[[ -o interactive ]] || return

# --- Prompt ---------------------------------------------------------------
# Mirrors the PS1 set in ~/.bashrc: green user@host, blue cwd.
#
# Neither half uses the machine's own names by default:
#   ~/.compname overrides the hostname with a short friendly name (else %m).
#   ~/.username overrides the account name (else markmuetz). The local account
#   is markmuetz, mmuetz or ln914101@reading.ac.uk depending on the machine,
#   and %n would show whichever it happens to be -- the Reading one in
#   particular renders as ln914101@reading.ac.uk@host, which is unreadable.

_compname=$(cat "$HOME/.compname" 2>/dev/null || echo '%m')
_username=$(cat "$HOME/.username" 2>/dev/null || echo 'markmuetz')
if [[ $EUID == 0 ]]; then
    PROMPT="%B%F{red}${_username}@${_compname}%f %F{blue}%~%f %#%b "
else
    PROMPT="%B%F{green}${_username}@${_compname}%f %F{blue}%~%f %#%b "
fi
unset _compname _username

# --- History --------------------------------------------------------------
# HISTSIZE (in-memory) is set in .shrc.common. SAVEHIST is the on-disk limit,
# i.e. the zsh counterpart of bash's HISTFILESIZE.

export HISTFILE="$HOME/.zsh_history"
export SAVEHIST=1000000000

setopt APPEND_HISTORY         # don't clobber the file when several shells exit
setopt INC_APPEND_HISTORY     # write as we go, not just at exit
setopt EXTENDED_HISTORY       # record timestamps
setopt HIST_IGNORE_DUPS       # don't store an immediately repeated command
setopt HIST_IGNORE_SPACE      # leading space keeps a command out of history
setopt HIST_REDUCE_BLANKS
setopt HIST_VERIFY            # expand !! etc. onto the line instead of running

# --- Completion -----------------------------------------------------------

fignore=(.pyc)                # zsh counterpart of bash's FIGNORE

autoload -Uz compinit
compinit

zstyle ':completion:*' menu select
# `set colored-stats on` in .inputrc.
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
# `set show-all-if-ambiguous on` in .inputrc: list straight away on an ambiguous
# completion rather than waiting for a second TAB.
unsetopt LIST_AMBIGUOUS

# --- Key bindings ---------------------------------------------------------
# Port of ~/.inputrc, which zsh does not read (readline is bash-only).

bindkey -e                    # emacs keymap, as per readline's default

# Up/down search history for lines starting with what's already typed
# (.inputrc: "\e[A": history-search-backward / "\e[B": history-search-forward).
autoload -Uz up-line-or-beginning-search down-line-or-beginning-search
zle -N up-line-or-beginning-search
zle -N down-line-or-beginning-search
bindkey '^[[A' up-line-or-beginning-search
bindkey '^[[B' down-line-or-beginning-search
bindkey '^[OA' up-line-or-beginning-search    # application cursor mode
bindkey '^[OB' down-line-or-beginning-search

# .inputrc: Control-j: menu-complete / Control-k: menu-complete-backward.
# N.B. this takes ^J away from accept-line, same as it did under bash.
bindkey '^J' menu-complete
bindkey '^K' reverse-menu-complete

# --- Shared config --------------------------------------------------------
# Last, so per-OS and per-site overrides win.

[ -f "$HOME/.shrc.common" ] && . "$HOME/.shrc.common"
