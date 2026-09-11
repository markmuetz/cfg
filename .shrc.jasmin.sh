# JASMIN setup. Sourced from .shrc.common when ~/.i_am_on_jasmin exists.
echo "#####################"
echo "# Setting up JASMIN #"
echo "#####################"

export WCOSMIC=/gws/nopw/j04/cosmic
export WMCSPRIME=/gws/nopw/j04/mcs_prime

# tmux (and rg, fzf, fd, gh, ...) come from `pixi global` in ~/.pixi/bin, which
# .shrc.common puts ahead of the system's older copies. No alias needed.

# uv's cache stays in $HOME: uv hardlinks from it into venvs, and scratch purges
# delete files one by one, which could leave half-empty cache entries behind.
# To keep it off the home quota, prune unused entries in the background at
# most once every 30 days. The stamp lives outside the cache so that
# `uv cache clean` doesn't remove it.
_uv_stamp="$HOME/.cache/uv-last-prune"
if _shrc_have uv && [ -z "$(find "$_uv_stamp" -mtime -30 2>/dev/null)" ]; then
    mkdir -p "$HOME/.cache" && touch "$_uv_stamp"
    (uv cache prune >/dev/null 2>&1 &)
fi
unset _uv_stamp

# Conda managed by miniforge, so no dependency on the (removed) Anaconda:
# https://help.jasmin.ac.uk/docs/software-on-jasmin/conda-removal/
_shrc_conda_init "$HOME/miniforge3"
