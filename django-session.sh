#!/bin/bash
tmux new-session -d -s django
tmux split-window -h
tmux send-keys -t django:0.1 "source venv/bin/activate && python manage.py runserver" C-m
tmux select-pane -t django:0.0
tmux send-keys "nvim ." C-m
tmux attach-session -t django

