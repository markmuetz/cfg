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

if [ -t 1 ] && [ "$TERM" != "dumb" ]; then
    if [ "${EUID}" = 0 ]; then
        PS1='${debian_chroot:+($debian_chroot)}\[\033[01;31m\]\h\[\033[01;34m\] \W \$\[\033[00m\] '
    else
        PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[01;34m\] \w \$\[\033[00m\] '
    fi
else
    # Show root@ when we don't have colours.
    PS1='\u@\h \w \$ '
fi

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
