#!/usr/bin/env bash
#
# Create or delete the config symlinks listed in symlinks.conf.
#
# symlinks.conf holds one link per line:   source:target[:profile]
#   source   path in the repo; $(pwd) is the repo root. A source ending in /*
#            links each matching file into target, which is then a folder.
#   target   where the link goes; $HOME and other variables are expanded.
#   profile  optional, laptop or juno: the line only applies to that machine.
#
# Usage:
#   symlinks.sh --create [--profile laptop|juno] [--backup]
#   symlinks.sh --delete [--include-files]
#
#   --profile        machine profile (default: detected, see detect_profile)
#   --backup         move a regular file found at a target to <target>.orig.<date>
#                    and link; without it the target is left alone and reported
#   --include-files  --delete also removes regular files at the targets
# --delete goes over every line, whatever its profile.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$REPO_DIR/symlinks.conf"

# shellcheck source-path=SCRIPTDIR source=utils.sh
. "$SCRIPT_DIR/utils.sh"

# links <profile> -> one "source<TAB>target" line per link of the config that
# applies to <profile> ("all": every line). Runs in the repo root, so $(pwd)
# in the config is the repo whatever the caller's directory.
links() {
    local want="$1" raw_source raw_target profile target_base source target
    cd "$REPO_DIR" || return 1
    while IFS=: read -r raw_source raw_target profile || [ -n "$raw_source" ]; do
        if [[ -z "$raw_source" || -z "$raw_target" || "$raw_source" == \#* ]]; then
            continue
        fi
        if [[ -n "$profile" && "$want" != "all" && "$profile" != "$want" ]]; then
            continue
        fi
        target_base=$(eval echo "$raw_target")
        # Unquoted on purpose: eval expands the variables, the shell the glob
        for source in $(eval echo "$raw_source"); do
            if [[ "$raw_source" == *\** ]]; then
                target="$target_base/$(basename "$source")"
            else
                target="$target_base"
            fi
            printf '%s\t%s\n' "$source" "$target"
        done
    done <"$CONFIG_FILE"
}

create_symlinks() {
    local profile="$1" backup="$2" source target saved
    local blocked=0 broken=0
    info "Creating symbolic links (profile: $profile)..."
    while IFS=$'\t' read -r source target; do
        if [ ! -e "$source" ]; then
            error "Source not found (skipping): $source"
            broken=$((broken + 1))
            continue
        fi
        if [ -L "$target" ]; then
            if [ "$(readlink "$target")" == "$source" ]; then
                info "Already linked: $target"
            else
                ln -sfn "$source" "$target"
                success "Updated: $target -> $source"
            fi
            continue
        fi
        if [ -e "$target" ]; then
            if [ "$backup" != true ]; then
                warning "A file already exists (skipping): $target"
                blocked=$((blocked + 1))
                continue
            fi
            saved="$target.orig.$(date +%Y%m%d%H%M%S)"
            mv "$target" "$saved"
            warning "Moved the existing file to $saved"
        fi
        mkdir -p "$(dirname "$target")"
        ln -s "$source" "$target"
        success "Created: $target -> $source"
    done < <(links "$profile")

    if ((blocked)); then
        warning "$blocked target(s) are regular files and were left alone: re-run with --backup to move them aside and link"
    fi
    ((blocked == 0 && broken == 0))
}

delete_symlinks() {
    local include_files="$1" source target
    info "Deleting symbolic links..."
    while IFS=$'\t' read -r source target; do
        if [ -L "$target" ] || { [ "$include_files" == true ] && [ -f "$target" ]; }; then
            rm -f "$target"
            success "Deleted: $target"
        else
            info "Not found: $target"
        fi
    done < <(links all)
}

usage() {
    echo "Usage: $(basename "$0") --create [--profile laptop|juno] [--backup]"
    echo "       $(basename "$0") --delete [--include-files]"
}

main() {
    local action="" profile="" backup=false include_files=false
    while (($#)); do
        case "$1" in
            --create | --delete) action="$1" ;;
            --profile)
                profile="${2:-}"
                shift
                ;;
            --backup) backup=true ;;
            --include-files) include_files=true ;;
            -h | --help) usage; return 0 ;;
            *) error "Unknown argument '$1'"; usage; return 1 ;;
        esac
        shift
    done

    if [ ! -f "$CONFIG_FILE" ]; then
        error "Configuration file not found: $CONFIG_FILE"
        return 1
    fi

    profile="${profile:-$(detect_profile)}"
    if [[ "$profile" != "laptop" && "$profile" != "juno" ]]; then
        error "Unknown profile '$profile' (laptop or juno)"
        return 1
    fi

    case "$action" in
        --create) create_symlinks "$profile" "$backup" ;;
        --delete) delete_symlinks "$include_files" ;;
        *) usage; return 1 ;;
    esac
}

if [ "$(basename "$0")" = "$(basename "${BASH_SOURCE[0]}")" ]; then
    main "$@"
fi
