#!/usr/bin/env bash
#
# Set up this machine from the repo, in order:
#   1. system packages with apt (laptop only, asks for the sudo password)
#   2. user toolchain in $HOME            (scripts/prerequisites.sh)
#   3. config symlinks                     (scripts/symlinks.sh)
#   4. the steps left to do by hand
# Safe to re-run: anything already in place is skipped.
#
# Usage: ./install.sh [--profile laptop|juno] [--check] [--backup]
#   --profile  machine profile; default: juno when HPC_SYSTEM=juno or the
#              hostname contains "juno", laptop otherwise
#   --check    only report what is missing, change nothing
#   --backup   a regular file where a link goes (e.g. the system's ~/.bashrc)
#              is moved to <file>.orig.<date> and linked; without it it is
#              left alone and reported

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source-path=SCRIPTDIR source=scripts/utils.sh
. "$SCRIPT_DIR/scripts/utils.sh"

# Debian/Ubuntu packages for the laptop. Juno has no sudo: there they come from
# the cluster (prerequisites.sh checks the ones it needs).
APT_PACKAGES=(
    build-essential              # cc: cargo needs a linker
    ca-certificates curl wget git
    tar gzip xz-utils unzip zstd # unpacking the downloaded tools
    bash-completion
    gnupg pass oathtool          # credentials read by kerb.exp/juno.exp/vpn.exp, t2a.sh
    expect krb5-user openssh-client
    xclip                        # t2a.sh copies the OTP to the clipboard
)

# apt_missing <package>... -> prints the packages that are not installed
apt_missing() {
    local pkg
    for pkg in "$@"; do
        # shellcheck disable=SC2016 # ${Status} is a dpkg-query field, not a shell variable
        dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q "ok installed" || echo "$pkg"
    done
}

# system_packages <check_only>
system_packages() {
    local check_only="$1" missing
    if ! command -v apt-get &>/dev/null; then
        warning "No apt-get here: install the equivalent of: ${APT_PACKAGES[*]}"
        return 1
    fi
    mapfile -t missing < <(apt_missing "${APT_PACKAGES[@]}")
    if ((${#missing[@]} == 0)); then
        info "System packages: all installed"
        return 0
    fi
    if [ "$check_only" == true ]; then
        warning "System packages missing: ${missing[*]}"
        return 1
    fi
    info "Installing system packages: ${missing[*]}"
    sudo apt-get update && sudo apt-get install -y "${missing[@]}"
}

# manual_steps <profile> -> what this script cannot do
manual_steps() {
    info "Left to do by hand (skip what is already done):"
    if [ "$1" == "laptop" ]; then
        cat <<'EOF'
  - GPG: import your private key (backup), then restore the pass store in
    ~/.password-store; kerb.exp/juno.exp/vpn.exp/t2a.sh read
    cmcc/juno/{user,password,authenticator}
  - SSH: keys and ~/.ssh/config (Juno login hosts, juno-ro for claude-ssh)
  - Kerberos: /etc/krb5.conf for the CMCC realm, if krb5-user didn't ask
  - Not in apt: WezTerm (https://wezterm.org), forcepoint-client (the VPN client vpn.exp runs)
  - Vault snapshot: clone the vault to ~/Obsidian/CMCC, then
      systemctl --user daemon-reload && systemctl --user enable --now vault-snapshot.timer
EOF
    else
        cat <<'EOF'
  - Conda environments used by the aliases: rofs_testenv_v0.1 (ca-pitest),
    cylc_ocflow-2.1 (ca-exp)
EOF
    fi
    cat <<'EOF'
  - Host-only settings and secrets: ~/.config/bash/local.bash (untracked)
  - Open a new shell (or `exec bash`) to load the new config
EOF
}

usage() {
    echo "Usage: $(basename "$0") [--profile laptop|juno] [--check] [--backup]"
}

main() {
    local profile="" check_only=false backup=() rc=0
    while (($#)); do
        case "$1" in
            --profile)
                profile="${2:-}"
                shift
                ;;
            --check) check_only=true ;;
            --backup) backup=(--backup) ;;
            -h | --help) usage; return 0 ;;
            *) error "Unknown argument '$1'"; usage; return 1 ;;
        esac
        shift
    done

    profile="${profile:-$(detect_profile)}"
    if [[ "$profile" != "laptop" && "$profile" != "juno" ]]; then
        error "Unknown profile '$profile' (laptop or juno)"
        return 1
    fi
    info "Profile: $profile"

    if [ "$profile" == "laptop" ]; then
        system_packages "$check_only" || rc=1
    fi

    if [ "$check_only" == true ]; then
        "$SCRIPT_DIR/scripts/prerequisites.sh" --check || rc=1
        info "Symlinks: not checked (--check changes nothing)"
    else
        "$SCRIPT_DIR/scripts/prerequisites.sh" || rc=1
        "$SCRIPT_DIR/scripts/symlinks.sh" --create --profile "$profile" "${backup[@]}" || rc=1
    fi

    manual_steps "$profile"

    if ((rc)); then
        error "Some steps failed or are incomplete: see the messages above"
    else
        success "Done"
    fi
    return $rc
}

if [ "$(basename "$0")" = "$(basename "${BASH_SOURCE[0]}")" ]; then
    main "$@"
fi
