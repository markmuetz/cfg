#!/bin/bash

tmux=/apps/contrib/jaspy/miniconda_envs/jaspy3.7/m3-4.6.14/envs/jaspy3.7-m3-4.6.14-r20190612/bin/tmux

function has-session {
  $tmux has-session -t $1 2>/dev/null
}

project=${1:-wp2}

if [[ $project == wp2 ]]; then
    echo "${project}"
elif [[ $project == ChEx2020 ]]; then
    echo "ch"
elif [[ $project == mid_lat_EASM ]]; then
    echo "mid_lat_EASM"
else
    echo "Unrecognized: ${project}"
    exit 1
fi

session=JASMIN_COSMIC_${project}

if has-session ${session}; then
    echo "Session ${session} already exists, attaching"
    sleep 1
    $tmux attach -t ${session}
else
    echo "Creating new ${session} session"
    $tmux -V
    $tmux new-session -d -s "${session}" -n jobs
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
    $tmux send-keys -t ${session}:0.0 'watch -n60 "squeue -u mmuetz 2>&1"' C-m
    # Not working yet.
    # $tmux send-keys -t ${session}:0.1 'watch -n60 "squeue -u mmuetz --states=R 2>&1|wc && squeue -u mmuetz --states=PD 2>&1"' C-m

    if [[ $project == wp2 ]]; then
        $tmux send-keys -t ${session}:1.0 'cd $HOME/projects/cosmic' C-m
        $tmux send-keys -t ${session}:1.1 'cd $HOME/projects/cosmic/ctrl' C-m

        $tmux send-keys -t ${session}:2.0 'cd $HOME/projects/cosmic/ctrl/WP2_analysis && conda activate cosmic_env && export MPLBACKEND=agg' C-m
        $tmux send-keys -t ${session}:2.1 'cd $HOME/projects/cosmic/ctrl/WP2_analysis' C-m
    elif [[ $project == ChEx2020 ]]; then
        $tmux send-keys -t ${session}:1.0 'cd $HOME/projects/china_extreme_precip' C-m
        $tmux send-keys -t ${session}:1.1 'cd $HOME/projects/china_extreme_precip' C-m

        $tmux send-keys -t ${session}:2.0 'cd $HOME/projects/china_extreme_precip && conda activate cosmic_remake0.5_env && export MPLBACKEND=agg' C-m
        $tmux send-keys -t ${session}:2.1 'cd $HOME/projects/china_extreme_precip' C-m
    elif [[ $project == mid_lat_EASM ]]; then
        $tmux send-keys -t ${session}:1.0 'cd $HOME/projects/mid_lat_EASM' C-m
        $tmux send-keys -t ${session}:1.1 'cd $HOME/projects/mid_lat_EASM' C-m

        $tmux send-keys -t ${session}:2.0 'cd $HOME/projects/mid_lat_EASM && conda activate cosmic_remake0.5_env && export MPLBACKEND=agg' C-m
        $tmux send-keys -t ${session}:2.1 'cd $HOME/projects/mid_lat_EASM' C-m
    fi

    $tmux send-keys -t ${session}:3.0 'cd $WCOSMIC/mmuetz/data' C-m
    $tmux send-keys -t ${session}:3.1 'cd $WCOSMIC/mmuetz/data' C-m

    $tmux -f .tmux.jasmin.conf -2 attach-session -d
fi
