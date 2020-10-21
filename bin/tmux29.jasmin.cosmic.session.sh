#!/bin/bash

tmux=/apps/contrib/jaspy/miniconda_envs/jaspy3.7/m3-4.6.14/envs/jaspy3.7-m3-4.6.14-r20190612/bin/tmux

function has-session {
  $tmux has-session -t Jasmin_cosmic 2>/dev/null
}

project=${1:-wp2}

if [[ $project == wp2 ]]; then
    echo "${project}"
elif [[ $project == ChEx2020 ]]; then
    echo "ch"
else
    echo "Unrecognized: ${project}"
    exit 1
fi

if has-session ; then
    echo "Session Jasmin_cosmic already exists, attaching"
    sleep 1
    $tmux attach -t Jasmin_cosmic
else
    echo "Creating new Jasmin_cosmic session"
    $tmux -V
    $tmux new-session -d -s 'Jasmin_cosmic' -n jobs
    $tmux split-window -h
    $tmux select-pane -t 0
    $tmux split-window 

    $tmux new-window -n dev
    $tmux split-window -h

    $tmux new-window -n ctrl
    $tmux split-window -h

    $tmux new-window -n data
    $tmux split-window -h

    $tmux select-window -t 2

    # Allow shells enough time to initialize.
    sleep 10
    $tmux send-keys -t Jasmin_cosmic:0.0 'watch -n60 "squeue -u mmuetz 2>&1"' C-m
    # Not working yet.
    # $tmux send-keys -t Jasmin_cosmic:0.1 'watch -n60 "squeue -u mmuetz --states=R 2>&1|wc && squeue -u mmuetz --states=PD 2>&1"' C-m

    if [[ $project == wp2 ]]; then
        $tmux send-keys -t Jasmin_cosmic:1.0 'cd $HOME/projects/cosmic' C-m
        $tmux send-keys -t Jasmin_cosmic:1.1 'cd $HOME/projects/cosmic/ctrl' C-m

        $tmux send-keys -t Jasmin_cosmic:2.0 'cd $HOME/projects/cosmic/ctrl/WP2_analysis && conda activate cosmic_env && export MPLBACKEND=agg' C-m
        $tmux send-keys -t Jasmin_cosmic:2.1 'cd $HOME/projects/cosmic/ctrl/WP2_analysis' C-m
    elif [[ $project == ChEx2020 ]]; then
        $tmux send-keys -t Jasmin_cosmic:1.0 'cd $HOME/projects/china_extreme_precip' C-m
        $tmux send-keys -t Jasmin_cosmic:1.1 'cd $HOME/projects/china_extreme_precip' C-m

        $tmux send-keys -t Jasmin_cosmic:2.0 'cd $HOME/projects/china_extreme_precip && conda activate cosmic_env && export MPLBACKEND=agg' C-m
        $tmux send-keys -t Jasmin_cosmic:2.1 'cd $HOME/projects/china_extreme_precip' C-m
    fi

    $tmux send-keys -t Jasmin_cosmic:3.0 'cd $WCOSMIC/mmuetz/data' C-m
    $tmux send-keys -t Jasmin_cosmic:3.1 'cd $WCOSMIC/mmuetz/data' C-m

    $tmux -f .tmux.jasmin.conf -2 attach-session -d
fi
