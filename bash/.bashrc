# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

[ -f "$HOME/.config/bash/aliases.bash" ] && . "$HOME/.config/bash/aliases.bash"
[ -f "$HOME/.config/bash/custom.bash" ] && . "$HOME/.config/bash/custom.bash"

# The prompt (yabpc) and the cross-session history sync are configured in
# custom.bash via PROMPT_COMMAND. Do not set PROMPT_COMMAND here: doing so after
# sourcing custom.bash would overwrite the "__history_sync; yabpc" chain it builds.
