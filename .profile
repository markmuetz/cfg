# ~/.profile: executed by the command interpreter for login shells.
# This file is not read by bash(1), if ~/.bash_profile or ~/.bash_login
# exists.
# see /usr/share/doc/bash/examples/startup-files for examples.
# the files are located in the bash-doc package.

# the default umask is set in /etc/profile; for setting the umask
# for ssh logins, install and configure the libpam-umask package.
#umask 022

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


