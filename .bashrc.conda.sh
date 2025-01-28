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
