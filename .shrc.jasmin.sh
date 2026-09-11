# JASMIN setup. Sourced from .shrc.common when ~/.i_am_on_jasmin exists.
echo "#####################"
echo "# Setting up JASMIN #"
echo "#####################"

export WCOSMIC=/gws/nopw/j04/cosmic
export WMCSPRIME=/gws/nopw/j04/mcs_prime

# tmux (and rg, fzf, fd, gh, ...) come from `pixi global` in ~/.pixi/bin, which
# .shrc.common puts ahead of the system's older copies. No alias needed.

# Conda managed by miniforge, so no dependency on the (removed) Anaconda:
# https://help.jasmin.ac.uk/docs/software-on-jasmin/conda-removal/
_shrc_conda_init "$HOME/miniforge3"
