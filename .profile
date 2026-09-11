# ~/.profile: executed by the command interpreter for login shells.
# Not read by bash if ~/.bash_profile or ~/.bash_login exists, and not read by
# zsh at all -- see ~/.zprofile for the zsh login-shell equivalent.

# The default umask is set in /etc/profile; for setting the umask for ssh
# logins, install and configure the libpam-umask package.
#umask 022

_profile_host="${HOSTNAME:-$(uname -n)}"

case "$_profile_host" in
    eslogin*|esPP00*)
        # ARCHER. Sets UMDIR and the Rose/UM environment.
        [ -f "$HOME/.profile_archer" ] && . "$HOME/.profile_archer"
        ;;
    puma)
        # --- Set ENV = the file holding KSH specific commands
        ENV=$HOME/.kshrc ; export ENV

        # ssh-agent setup
        . "$HOME/.ssh/ssh-setup"

        # Required for Rose UM suites.
        export UMDIR=/home/um
        ;;
esac

unset _profile_host

# Include .bashrc if we're bash. It in turn sources ~/.shrc.common.
if [ -n "$BASH_VERSION" ] && [ -f "$HOME/.bashrc" ]; then
    . "$HOME/.bashrc"
fi

# .bashrc returns early in non-interactive login shells (e.g. SLURM scripts
# with `#!/bin/bash -l`), so put the user bin dirs on PATH here as well.
# Appended, and skipped if .shrc.common already added them.
for _d in "$HOME/bin" "$HOME/.local/bin"; do
    if [ -d "$_d" ]; then
        case ":$PATH:" in
            *":$_d:"*) ;;
            *) PATH="$PATH:$_d" ;;
        esac
    fi
done
unset _d
export PATH
