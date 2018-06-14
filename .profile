# ~/.profile: executed by the command interpreter for login shells.
# This file is not read by bash(1), if ~/.bash_profile or ~/.bash_login
# exists.
# see /usr/share/doc/bash/examples/startup-files for examples.
# the files are located in the bash-doc package.

# the default umask is set in /etc/profile; for setting the umask
# for ssh logins, install and configure the libpam-umask package.
#umask 022

# Setup UM variables
. /etc/bash.bashrc > /dev/null 2>&1

if [ $(echo $HOSTNAME|cut -c1-7) = "eslogin" ] || [ $(echo $HOSTNAME|cut -c1-6) = "esPP00" ] ; then
    source ~/.profile_archer
fi

# if running bash
if [ -n "$BASH_VERSION" ]; then
    # include .bashrc if it exists
    if [ -f "$HOME/.bashrc" ]; then
	. "$HOME/.bashrc"
    fi
fi

# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/bin" ] ; then
    PATH="$HOME/bin:$PATH"
fi

if [ $(echo $HOSTNAME) = "puma" ]; then
    # --- Set ENV = the file holding KSH specific commands
    ENV=$HOME/.kshrc ; export ENV

    ### PLEASE ADD YOUR OWN CODE BELOW THIS LINE ###

    # ssh-agent setup
    . $HOME/.ssh/ssh-setup

    # required for Rose UM suites
    export UMDIR=/home/um
fi

# Apparently, according to Annette, I should be using the y07 one.
export UMDIR=/work/n02/n02/hum
#export UMDIR=/work/y07/y07/umshared

TARGET_MC=cce

VN=8.2
#VN=10.5
if test -f $HOME/.umsetvars_$VN; then
  . $HOME/.umsetvars_$VN
else
  . $UMDIR/vn$VN/$TARGET_MC/scripts/.umsetvars_$VN
fi 

# Rose 
export PATH=$PATH:$UMDIR/software/bin

