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

# Custom Prompt
PROMPT_COMMAND=yabpc
