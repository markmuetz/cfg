#!/bin/bash

function has-session {
  tmux has-session -t Jasmin_cosmic 2>/dev/null
}

if has-session ; then
    echo "Session Jasmin_cosmic already exists, attaching"
    sleep 1
    tmux attach -t Jasmin_cosmic
else
    echo "Creating new Jasmin_cosmic session"
    tmux -V
    tmux -f .tmux.jasmin.conf new-session -d -s 'Jasmin_cosmic' -n jobs
    tmux split-window -h
    tmux select-pane -t 0
    tmux split-window 

    tmux new-window -n dev
    tmux split-window -h

    tmux new-window -n ctrl
    tmux split-window -h

    tmux new-window -n data
    tmux split-window -h

    tmux select-window -t 2

    # Allow shells enough time to initialize.
    sleep 10
    tmux send-keys -t Jasmin_cosmic:0.0 'watch -n60 "bjobs 2>&1"' C-m
    tmux send-keys -t Jasmin_cosmic:0.1 'watch -n60 "bjobs 2>&1|grep RUN|wc && bjobs 2>&1|grep PEND|wc"' C-m

    tmux send-keys -t Jasmin_cosmic:1.0 'cd $HOME/projects/cosmic' C-m
    tmux send-keys -t Jasmin_cosmic:1.1 'cd $HOME/projects/cosmic/ctrl' C-m

    tmux send-keys -t Jasmin_cosmic:2.0 'cd $HOME/projects/cosmic/ctrl/WP2_analysis && conda activate cosmic_env && export MPLBACKEND=agg' C-m
    tmux send-keys -t Jasmin_cosmic:2.1 'cd $HOME/projects/cosmic/ctrl/WP2_analysis' C-m

    tmux send-keys -t Jasmin_cosmic:3.0 'cd $WCOSMIC/mmuetz/data' C-m
    tmux send-keys -t Jasmin_cosmic:3.1 'cd $WCOSMIC/mmuetz/data' C-m

    tmux -f .tmux.jasmin.conf -2 attach-session -d
fi
