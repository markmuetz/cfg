# zsh login shells. The zsh counterpart of ~/.profile.
#
# Kept deliberately small: Homebrew needs to be on PATH before anything else
# runs, and .shrc.darwin (sourced from .shrc.common) repeats this guarded, for
# non-login shells which never read this file.

for _brew in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    if [ -x "$_brew" ]; then
        eval "$("$_brew" shellenv)"
        break
    fi
done
unset _brew
