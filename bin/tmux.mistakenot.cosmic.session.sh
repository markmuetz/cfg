#!/bin/bash

function has-session {
  tmux has-session -t cosmic 2>/dev/null
}

if has-session ; then
    echo "Session cosmic already exists, attaching"
    sleep 1
    tmux attach -t cosmic
else
    echo "Creating new cosmic session"
    tmux new-session -d -s 'cosmic' -n sync

    tmux new-window -n dev
    tmux split-window -h

    tmux new-window -n ctrl
    tmux split-window -h

    tmux select-window -t 2

    # Allow shells enough time to initialize.
    sleep 4
    tmux send-keys -t cosmic:0.0 'cd $HOME/mirrors/jasmin/gw_cosmic/mmuetz/data' C-m

    tmux send-keys -t cosmic:1.0 'cd $HOME/projects/cosmic/cosmic' C-m
    tmux send-keys -t cosmic:1.1 'cd $HOME/cosmic_ctrl' C-m

    tmux send-keys -t cosmic:2.0 'cd $HOME/cosmic_ctrl && conda activate cosmic_env' C-m
    tmux send-keys -t cosmic:2.1 'cd $HOME/cosmic_ctrl' C-m

    tmux -2 attach-session -d
fi
