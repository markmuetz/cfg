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

# if the command-not-found package is installed, use it
if [ -x /usr/lib/command-not-found ]; then
    function command_not_found_handle {
        # check because c-n-f could've been removed in the meantime
        if [ -x /usr/lib/command-not-found ]; then
            /usr/bin/python /usr/lib/command-not-found -- $1
            return $?
        else
            return 127
        fi
    }
fi

if [ $(echo $HOSTNAME|cut -c1-7) != "eslogin" ]; then
    # Make these very large so that history-search-backwards has a lot of cmds.
    export HISTSIZE=1000000
fi
export HISTFILESIZE=1000000000
export FIGNORE=.pyc
export PATH=$PATH:$HOME/bin:$HOME/.local/bin

# alias vim='vim -p'
alias nvim='nvim -p'
if ! hash rgrep 2>/dev/null; then
    alias rgrep='grep -r'
fi

if hash fcm 2>/dev/null; then
    alias svn='echo "WARNING, using svn not fcm"; svn'
fi

alias jasmin='echo -ne "\033]0;JASMIN\007"; ssh -AY mmuetz@jasmin-login1.ceda.ac.uk'
alias jasmin2='echo -ne "\033]0;JASMIN2\007"; ssh -AY mmuetz@jasmin-login2.ceda.ac.uk'
alias jasminhop='echo -ne "\033]0;JASMINHOP\007"; ssh -o "ProxyCommand ssh -AY markmuetz@puma.nerc.ac.uk -W %h:%p" -AY mmuetz@jasmin-login1.ceda.ac.uk'
alias jasminsci='echo -ne "\033]0;JASMINSCI\007"; ssh -AY JasminSci4'
alias jasminscirdg='echo -ne "\033]0;JASMINSCI\007"; ssh -AY JasminSci4Rdg'

alias archer='echo -ne "\033]0;ARCHER\007"; ssh -Y mmuetz@login.archer.ac.uk'
alias rdf='echo -ne "\033]0;RDF\007"; ssh -Y mmuetz@login.rdf.ac.uk'
alias puma='echo -ne "\033]0;PUMA\007"; ssh -Y markmuetz@puma.nerc.ac.uk'
alias oak='echo -ne "\033]0;OAK\007"; ssh -Y hb865130@oak.reading.ac.uk'
alias monsoon='echo -ne "\033]0;MONSOON\007"; ssh -Y mamue@lander.monsoon-metoffice.co.uk'

alias jsync='rsync -e "ssh -o \"ProxyCommand ssh -A markmuetz@puma.nerc.ac.uk -W %h:%p\""'

export JASMIN="mmuetz@jasmin-xfer1.ceda.ac.uk"
export ARCHER="mmuetz@login.archer.ac.uk"

alias lsf='readlink -f'

# Computer specific settings at end so can overwrite.
if [ $(echo $HOSTNAME|cut -c1-7) = "eslogin" ] || [ $(echo $HOSTNAME|cut -c1-6) = "esPP00" ] ; then
    # Interactive shells on ARCHER. 
    alias qserial='qsub -IVl select=serial=true:ncpus=1,walltime=10:0:0 -A n02-REVCON'
    # N.B.
    alias qshort='echo "REM aprun"; qsub -q short -IVl select=1,walltime=0:20:0 -A n02-REVCON'
    # export OMNIUM_ANALYSIS_PKGS=scaffold:cosar
    export WORK=/work/n02/n02/mmuetz
    export COSAR_SUITE_UAU197_DIR=/home/n02/n02/mmuetz/work/omnium_test_suites/cosar_test_suite/u-au197
    export SCAFFOLD_SUITE_UAN388_DIR=/home/n02/n02/mmuetz/work/omnium_test_suites/scaffold_test_suite/u-an388
    export ube530=/home/n02/n02/mmuetz/nerc/um11.0_runs/archive/u-be530
fi

if [ $HOSTNAME = "puma" ]; then
    . mosrs-setup-gpg-agent
    # N.B. different git location.
    # alias dotfiles='/usr/local/bin/git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME'
fi
if [ $HOSTNAME = "zerogravitas" ]; then
    export PATH="/home/markmuetz/opt/MO/fcm-2016.12.0/bin:/home/markmuetz/opt/MO/cylc/bin:/home/markmuetz/opt/MO/rose-2017.01.0/bin:/home/markmuetz/opt/intel/bin:$PATH"
    # export OMNIUM_ANALYSIS_PKGS=scaffold:cosar
    export COSAR_SUITE_UAU197_DIR=/home/markmuetz/omnium_test_suites/cosar_test_suite/u-au197
    export SCAFFOLD_SUITE_UAN388_DIR=/home/markmuetz/omnium_test_suites/scaffold_test_suite/u-an388
    export ube530=/home/markmuetz/mirrors/archer/nerc/um11.0_runs/archive/u-be530/
    source $HOME/.anaconda3_setup.sh
fi

if [ $HOSTNAME = "breakeven" ]; then
    . $HOME/.argcomplete.rc
    export PATH="/home/markmuetz/opt/fcm-2016.05.1/bin:/home/markmuetz/opt/cylc-6.10.2/bin:/home/markmuetz/opt/rose-master/bin:$PATH"
    # export OMNIUM_ANALYSIS_PKGS=scaffold:cosar
    export OMNIUM_ANALYSIS_PKGS=cosar
    export ube530=/home/markmuetz/mirrors/archer/nerc/um11.0_runs/archive/u-be530/
fi 
if [ $HOSTNAME = "exppostproc01.monsoon-metoffice.co.uk" ]; then
    export OMNIUM_ANALYSIS_PKGS=scaffold:cosar
fi
if [ $HOSTNAME = "exvmsrose.monsoon-metoffice.co.uk" ]; then
    . mosrs-setup-gpg-agent
fi

if [ $(echo $HOSTNAME|cut -c1-10) = "jasmin-sci" ] || [ $(echo $HOSTNAME) = "mass-cli1.ceda.ac.uk" ] ; then
    export WCOSMIC=/gws/nopw/j04/cosmic
    if [ $(echo $HOSTNAME|cut -c1-10) = "jasmin-sci" ] ; then
        module load jaspy/3.7/r20190612
    fi
    alias git=/apps/contrib/jaspy/miniconda_envs/jaspy3.7/m3-4.6.14/envs/jaspy3.7-m3-4.6.14-r20190612/bin/git
    # !! Contents within this block are managed by 'conda init' !!
    # NO LONGER. Managed by me!
    __conda_setup="$('/apps/contrib/jaspy/miniconda_envs/jaspy3.7/m3-4.6.14/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
    if [ $? -eq 0 ]; then
        eval "$__conda_setup"
    else
        if [ -f "/apps/contrib/jaspy/miniconda_envs/jaspy3.7/m3-4.6.14/etc/profile.d/conda.sh" ]; then
            . "/apps/contrib/jaspy/miniconda_envs/jaspy3.7/m3-4.6.14/etc/profile.d/conda.sh"
        else
            export PATH="/apps/contrib/jaspy/miniconda_envs/jaspy3.7/m3-4.6.14/bin:$PATH"
        fi
    fi
    unset __conda_setup
fi

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

if [ $HOSTNAME = "mistakenot" ] || [ $HOSTNAME = "zerogravitas" ] || [ $HOSTNAME = "breakeven" ]; then
    # Activate conda envs.
    # >>> conda initialize >>>
    # !! Contents within this block are managed by 'conda init' !!
    __conda_setup="$('/home/markmuetz/anaconda3/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
    if [ $? -eq 0 ]; then
        eval "$__conda_setup"
    else
        if [ -f "/home/markmuetz/anaconda3/etc/profile.d/conda.sh" ]; then
            . "/home/markmuetz/anaconda3/etc/profile.d/conda.sh"
        else
            export PATH="/home/markmuetz/anaconda3/bin:$PATH"
        fi
    fi
    unset __conda_setup
    # <<< conda initialize <<<
fi

# Remove (base) from PS1.
# Gets added by conda.
# Doing it like this means that new envs will still be prepended to PS1.
# https://stackoverflow.com/a/55172508/54557
PS1="$(echo $PS1 | sed 's/(base) //') "
