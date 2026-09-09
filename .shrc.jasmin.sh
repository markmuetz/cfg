# JASMIN setup. Sourced from .shrc.common when ~/.i_am_on_jasmin exists.
echo "#####################"
echo "# Setting up JASMIN #"
echo "#####################"

export WCOSMIC=/gws/nopw/j04/cosmic
export WMCSPRIME=/gws/nopw/j04/mcs_prime

# Locally managed tmux -- the system one is too old. Works on both
# mass-cli1.jasmin.ac.uk and the sci nodes.
if [ -x "$HOME/miniconda3/envs/tmux_env/bin/tmux" ]; then
    alias tmux="$HOME/miniconda3/envs/tmux_env/bin/tmux"
fi

# Conda managed by miniforge, so no dependency on the (removed) Anaconda:
# https://help.jasmin.ac.uk/docs/software-on-jasmin/conda-removal/
_shrc_conda_init "$HOME/miniforge3"
