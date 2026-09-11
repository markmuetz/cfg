# bash entry point. Everything portable lives in ~/.shrc.common, which is
# shared with ~/.zshrc; this file holds only the bash-specific bits.

# If not running interactively, don't do anything.
case $- in
    *i*) ;;
      *) return ;;
esac

# Check the window size after each command and, if necessary, update LINES and
# COLUMNS.
shopt -s checkwinsize

# Set variable identifying the chroot you work in (used in the prompt below).
if [ -z "$debian_chroot" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# --- Prompt ---------------------------------------------------------------
# The zsh equivalent is PROMPT in ~/.zshrc -- keep the two looking the same.
#
# ~/.compname overrides the hostname (else \h), ~/.username overrides the
# account name (else markmuetz). See the fuller note in ~/.zshrc: the local
# account differs per machine and \u would show whichever it happens to be.

if [ -f "$HOME/.compname" ]; then
    _compname=$(cat "$HOME/.compname")
else
    _compname='\h'
fi
if [ -f "$HOME/.username" ]; then
    _username=$(cat "$HOME/.username")
else
    _username='markmuetz'
fi

if [ -t 1 ] && [ "$TERM" != "dumb" ]; then
    if [ "${EUID}" = 0 ]; then
        PS1='${debian_chroot:+($debian_chroot)}\[\033[01;31m\]'"${_username}@${_compname}"'\[\033[01;34m\] \W \$\[\033[00m\] '
    else
        PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]'"${_username}@${_compname}"'\[\033[01;34m\] \w \$\[\033[00m\] '
    fi
else
    PS1="${_username}@${_compname}"' \w \$ '
fi

unset _compname _username

# --- History --------------------------------------------------------------
# HISTSIZE is set in .shrc.common; HISTFILESIZE is bash-only (zsh uses SAVEHIST).

export HISTFILESIZE=1000000000

# --- Completion -----------------------------------------------------------

export FIGNORE=.pyc

if [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
fi

# --- Shared config --------------------------------------------------------
# Last, so per-OS and per-site overrides win.

[ -f "$HOME/.shrc.common" ] && . "$HOME/.shrc.common"

# --- fzf ------------------------------------------------------------------
# Ctrl-R fuzzy history, Ctrl-T insert a path, Alt-C cd into a dir, and
# `**<Tab>` fuzzy completion. After .shrc.common, so PATH is final (pixi on
# JASMIN, brew on macOS). `fzf --bash` needs fzf >= 0.48; older ones print
# nothing here. Keep in step with the same block in ~/.zshrc.
if command -v fzf >/dev/null 2>&1; then
    # List with fd where there is one: fast, and skips .gitignored files.
    # FZF_DEFAULT_COMMAND is left alone: ~/.vimrc sets it when unset.
    if command -v fd >/dev/null 2>&1; then
        export FZF_CTRL_T_COMMAND='fd --type f'
        export FZF_ALT_C_COMMAND='fd --type d'
    fi
    eval "$(fzf --bash 2>/dev/null)"
fi
