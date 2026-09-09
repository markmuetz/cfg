# Monsoon / Met Office Rose setup. Sourced from .shrc.common.

# Don't re-run the gpg-agent setup inside tmux -- it inherits the outer one.
if ! { [ "$TERM" = "screen" ] && [ -n "$TMUX" ]; }; then
    [ -f ~fcm/bin/mosrs-setup-gpg-agent ] && . ~fcm/bin/mosrs-setup-gpg-agent
fi

_shrc_have module && module load hpctools-tmux
