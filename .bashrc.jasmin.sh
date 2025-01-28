echo "#####################"
echo "# Setting up JASMIN #"
echo "# in .bashrc        #"
echo "#####################"
export WCOSMIC=/gws/nopw/j04/cosmic
export WMCSPRIME=/gws/nopw/j04/mcs_prime

# if [ $(echo $HOSTNAME|cut -c1-10) = "jasmin-sci" ] ; then
#     module load jaspy/3.7/r20190612
# fi
# Standard version of git seems to work for me now.
# alias git=/apps/contrib/jaspy/miniconda_envs/jaspy3.7/m3-4.6.14/envs/jaspy3.7-m3-4.6.14-r20190612/bin/git
# Switch to a locally managed version of tmux. 
if [ $(echo $HOSTNAME) = "mass-cli1.jasmin.ac.uk" ] ; then
    # Works on both mass-cli1.jasmin.ac.uk and sci4.jasmin.ac.uk
    alias tmux=/home/users/mmuetz/miniconda3/envs/tmux_env/bin/tmux
else
    # BUT has weird bahviour. Revert to this for now.
    # alias tmux=/apps/contrib/jaspy/miniconda_envs/jaspy3.7/m3-4.6.14/envs/jaspy3.7-m3-4.6.14-r20190612/bin/tmux
    alias tmux=/home/users/mmuetz/miniconda3/envs/tmux_env/bin/tmux
fi
# Using conda managed by miniforge so no dep on Anaconda:
# https://help.jasmin.ac.uk/docs/software-on-jasmin/conda-removal/
# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/home/users/mmuetz/miniforge3/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/home/users/mmuetz/miniforge3/etc/profile.d/conda.sh" ]; then
        . "/home/users/mmuetz/miniforge3/etc/profile.d/conda.sh"
    else
        export PATH="/home/users/mmuetz/miniforge3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

# alias xfc=/home/users/mmuetz/xfc_venv/bin/xfc
# !! Contents within this block are managed by 'conda init' !!
# NO LONGER. Managed by me!
# __conda_setup="$('/home/users/mmuetz/miniconda3/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
# if [ $? -eq 0 ]; then
#     eval "$__conda_setup"
# else
#     if [ -f "/home/users/mmuetz/miniconda3/etc/profile.d/conda.sh" ]; then
#         . "/home/users/mmuetz/miniconda3/etc/profile.d/conda.sh"
#     else
#         export PATH="/home/users/mmuetz/miniconda3/bin:$PATH"
#     fi
# fi
unset __conda_setup
# Using jaspy conda.
# __conda_setup="$('/apps/contrib/jaspy/miniconda_envs/jaspy3.7/m3-4.6.14/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
# if [ $? -eq 0 ]; then
#     eval "$__conda_setup"
# else
#     if [ -f "/apps/contrib/jaspy/miniconda_envs/jaspy3.7/m3-4.6.14/etc/profile.d/conda.sh" ]; then
#         . "/apps/contrib/jaspy/miniconda_envs/jaspy3.7/m3-4.6.14/etc/profile.d/conda.sh"
#     else
#         export PATH="/apps/contrib/jaspy/miniconda_envs/jaspy3.7/m3-4.6.14/bin:$PATH"
#     fi
# fi
# unset __conda_setup

