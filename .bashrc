# To enable the settings / commands in this file for login shells as well,
# this file has to be sourced in /etc/profile.

# If not running interactively, don't do anything
[ -z "$PS1" ] && return

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "$debian_chroot" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

use_color=true

# Set colorful PS1 only on colorful terminals.
# dircolors --print-database uses its own built-in database
# instead of using /etc/DIR_COLORS.  Try to use the external file
# first to take advantage of user additions.  Use internal bash
# globbing instead of external grep binary.
safe_term=${TERM//[^[:alnum:]]/?}   # sanitize TERM
match_lhs=""
[[ -f ~/.dir_colors   ]] && match_lhs="${match_lhs}$(<~/.dir_colors)"
[[ -f /etc/DIR_COLORS ]] && match_lhs="${match_lhs}$(</etc/DIR_COLORS)"
[[ -z ${match_lhs}    ]] \
        && type -P dircolors >/dev/null \
        && match_lhs=$(dircolors --print-database)
[[ $'\n'${match_lhs} == *$'\n'"TERM "${safe_term}* ]] && use_color=true

if ${use_color} ; then
    # Enable colors for ls, etc.  Prefer ~/.dir_colors #64489
    if type -P dircolors >/dev/null ; then
        if [[ -f ~/.dir_colors ]] ; then
            eval $(dircolors -b ~/.dir_colors)
        elif [[ -f /etc/DIR_COLORS ]] ; then
            eval $(dircolors -b /etc/DIR_COLORS)
        else
            eval $(dircolors)
        fi
    fi

    if [[ ${EUID} == 0 ]] ; then
        PS1='${debian_chroot:+($debian_chroot)}\[\033[01;31m\]\h\[\033[01;34m\] \W \$\[\033[00m\] '
    else
        PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[01;34m\] \w \$\[\033[00m\] '
    fi

    alias ls='ls --color=auto'
    alias grep='grep --colour=auto'
    alias rgrep='rgrep --colour=auto'
else
    if [[ ${EUID} == 0 ]] ; then
        # show root@ when we don't have colors
        PS1='\u@\h \W \$ '
    else
        PS1='\u@\h \w \$ '
    fi
fi

# Try to keep environment pollution down, EPA loves us.
unset use_color safe_term match_lhs

# enable bash completion in interactive shells
if [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
fi

export HISTFILESIZE=1000000000
export FIGNORE=.pyc
export PATH=$PATH:$HOME/bin:$HOME/.local/bin

if [[ -d $HOME/Dropbox/Academic/Projects ]]; then
    for projdir in $HOME/Dropbox/Academic/Projects/*;
    do
        proj=$(basename $projdir)
        export $proj=$projdir
    done
fi

if ! hash rgrep 2>/dev/null; then
    alias rgrep='grep -r'
fi

if hash fcm 2>/dev/null; then
    alias svn='echo "WARNING, using svn not fcm"; svn'
fi

function monsoon () {
    echo -ne "\033]0;MONSOON\007"
    # N.B. set up in .ssh/config
    ssh Monsoon
}

function jasmin-sci () {
    SERVER=$1
    if [ -z "$2" ]
    then
        echo -ne "\033]0;jasmin-sci-${SERVER}\007"
        # echo "No tmux requested"
        # N.B. automatically uses proxy due to .ssh/config setup for *.jasmin.ac.uk
        ssh sci-${SERVER}.jasmin.ac.uk
    else
        TMUX_SESS=$2
        echo -ne "\033]0;jasmin-sci-${SERVER} ${TMUX_SESS}\007"
        ssh sci-${SERVER}.jasmin.ac.uk -t "/home/users/mmuetz/miniconda3/envs/tmux_env/bin/tmux new-session -As ${TMUX_SESS}"
    fi
}

function jasmin-mass () {
    echo -ne "\033]0;JASMIN-MASS\007"
    # N.B. automatically uses proxy due to .ssh/config setup for *.jasmin.ac.uk
    ssh mass-cli.jasmin.ac.uk
}

function racc-cluster () {
    SERVER=$1
    echo -ne "\033]0;RACC-CLUSTER${SERVER}\007"
    # N.B. automatically uses proxy due to .ssh/config setup for *.rdg.ac.uk
    ssh racc-login.rdg.ac.uk
}

function cfg-check () {
    DOTFILES_REPO=https://github.com/markmuetz/cfg/
    LOCAL_HASH=$(cfg rev-parse HEAD)
    REMOTE_HASH=$(git ls-remote $DOTFILES_REPO|grep HEAD|awk '{print $1}')
    if [ $LOCAL_HASH != $REMOTE_HASH ]; then
        echo "Dotfiles out-of-date with $DOTFILES_REPO"
    else
        echo "Dotfiles up-to-date with $DOTFILES_REPO"
    fi
    if [[ `cfg status --porcelain` ]]; then
        echo "There are uncommitted changes"
    fi
}
# Check git exists:
if hash git 2>/dev/null; then
    alias cfg='git --git-dir=$HOME/.cfg/ --work-tree=$HOME'
else
    alias cfg='echo "cfg not available: no git"'
fi

alias lsf='readlink -f'
alias du-sort-dirs="du -h --max-depth=1|sort -hr"

# Thanks ChatGPT!
function cdup() {
  local count=$1
  if [[ -z "$count" ]]; then
    count=1
  fi
  local ups=""
  for ((i=1; i<=count; i++)); do
    ups+="../"
  done
  cd "$ups" || return
}

# if [[ $(echo $HOSTNAME|cut -c1-10) = "jasmin-sci" ]] || [[ $(echo $HOSTNAME) = "mass-cli1.ceda.ac.uk" ]] || [[ $(echo $HOSTNAME|cut -c11-16) = "jasmin" ]] || [[ $(echo $HOSTNAME|cut -c6-11) = "jasmin" ]]; then
# This is altogether more straightforward, and works for e.g. sci 8 which has a hostXXX hostname.
if [ -e ~/.i_am_on_jasmin ]; then
    source ~/.bashrc.jasmin.sh
fi

if [ $HOSTNAME = "mistakenot" ] || [ $HOSTNAME = "zerogravitas" ] || [ $HOSTNAME = "breakeven" ]; then
    source ~/.bashrc.conda.sh
fi

if [[ $(echo $HOSTNAME|cut -c1-10) = "racc-login" ]]; then
    source ~/.bashrc.racc.sh
fi

[[ $- != *i* ]] && return # Stop here if not running interactively

if [ $HOSTNAME = "exvmsrose.monsoon-metoffice.co.uk" ] || [ $(echo $HOSTNAME|cut -c1-5) = "xcslc" ]; then
    if ! { [ "$TERM" = "screen" ] && [ -n "$TMUX" ]; } then
        . ~fcm/bin/mosrs-setup-gpg-agent
    fi
    module load hpctools-tmux
fi

