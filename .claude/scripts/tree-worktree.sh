#!/usr/bin/env bash

# This file is sourced by the wtree/tree shell functions so a successful run
# can change the caller's working directory.

_tree_worktree_error() {
    printf 'Error: %s\n' "$*" >&2
    return 1
}

_tree_worktree_info() {
    printf 'Info: %s\n' "$*"
}

_tree_worktree_provision_beads_redirect() {
    local primary_path="$1"
    local target_path="$2"
    local primary_beads="${primary_path}/.beads"
    local target_beads="${target_path}/.beads"
    local redirect_target

    [[ -d "$primary_beads" ]] || return 0
    [[ ! -f "${target_beads}/beads.db" && ! -f "${target_beads}/redirect" ]] || return 0

    redirect_target="$(python3 -c 'import os,sys; print(os.path.relpath(sys.argv[1], sys.argv[2]))' "$primary_beads" "$target_beads" 2>/dev/null)" || {
        _tree_worktree_info "Skipped .beads/redirect provisioning because the relative path could not be resolved."
        return 0
    }

    mkdir -p "$target_beads" || return 1
    printf '%s\n' "$redirect_target" >"${target_beads}/redirect" || return 1
    _tree_worktree_info "Provisioned .beads/redirect -> ${redirect_target}."
}

_tree_worktree_main() {
    local raw_name="${1-}"
    local common_dir primary_path primary_parent target_name target_path target_sha
    local worktree_list current_path="" current_branch=""
    local target_registered=0 branch_conflict=""
    local line add_mode

    if [[ $# -ne 1 || -z "$raw_name" ]]; then
        _tree_worktree_error "Usage: tree <name>"
        return 1
    fi
    if [[ "$raw_name" == "." || "$raw_name" == ".." || "$raw_name" == *".."* ]]; then
        _tree_worktree_error "Invalid worktree name '$raw_name': dot and dotdot names are not allowed."
        return 1
    fi
    if [[ "$raw_name" == *"/"* || "$raw_name" == *"\\"* || ! "$raw_name" =~ ^[A-Za-z0-9._-]+$ ]]; then
        _tree_worktree_error "Invalid worktree name '$raw_name': use one component containing only A-Z, a-z, 0-9, '.', '_' or '-'."
        return 1
    fi

    git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
        _tree_worktree_error "Not inside a git worktree."
        return 1
    }

    common_dir="$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || {
        _tree_worktree_error "Cannot resolve the repository common directory."
        return 1
    }
    common_dir="$(cd "$common_dir" 2>/dev/null && pwd -P)" || {
        _tree_worktree_error "Cannot canonicalize the repository common directory."
        return 1
    }
    [[ "$common_dir" == */.git ]] || {
        _tree_worktree_error "Unsupported git common-directory layout: $common_dir"
        return 1
    }
    primary_path="${common_dir%/.git}"
    primary_path="$(cd "$primary_path" 2>/dev/null && pwd -P)" || {
        _tree_worktree_error "Cannot resolve the primary worktree."
        return 1
    }
    primary_parent="$(dirname "$primary_path")"
    target_name="worktree_${raw_name}"
    target_path="${primary_parent}/${target_name}"

    [[ "$target_path" != "$primary_path" ]] || {
        _tree_worktree_error "Refusing to operate on the primary worktree."
        return 1
    }

    GIT_TERMINAL_PROMPT=0 git -C "$primary_path" fetch origin main >/dev/null 2>&1 || {
        _tree_worktree_error "Failed to fetch origin/main from '$primary_path'."
        return 1
    }
    target_sha="$(git -C "$primary_path" rev-parse --verify 'refs/remotes/origin/main^{commit}' 2>/dev/null)" || {
        _tree_worktree_error "Fetched origin/main is unavailable in '$primary_path'."
        return 1
    }

    worktree_list="$(git -C "$primary_path" worktree list --porcelain)" || {
        _tree_worktree_error "Cannot read the repository worktree registry."
        return 1
    }
    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ -z "$line" ]]; then
            if [[ "$current_path" == "$target_path" ]]; then
                target_registered=1
            fi
            if [[ "$current_branch" == "refs/heads/$target_name" && "$current_path" != "$target_path" ]]; then
                branch_conflict="$current_path"
            fi
            current_path=""
            current_branch=""
            continue
        fi
        case "$line" in
            worktree\ *) current_path="${line#worktree }" ;;
            branch\ *) current_branch="${line#branch }" ;;
        esac
    done <<<"$worktree_list"
    if [[ "$current_path" == "$target_path" ]]; then
        target_registered=1
    fi
    if [[ "$current_branch" == "refs/heads/$target_name" && "$current_path" != "$target_path" ]]; then
        branch_conflict="$current_path"
    fi

    if [[ -n "$branch_conflict" ]]; then
        _tree_worktree_error "Branch '$target_name' is checked out at '$branch_conflict'."
        return 1
    fi

    if [[ -e "$target_path" ]]; then
        [[ -d "$target_path" && "$target_registered" -eq 1 ]] || {
            _tree_worktree_error "Existing target '$target_path' is not a registered worktree of this repository."
            return 1
        }
        local target_common_dir
        target_common_dir="$(git -C "$target_path" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || {
            _tree_worktree_error "Cannot resolve the target repository identity."
            return 1
        }
        target_common_dir="$(cd "$target_common_dir" 2>/dev/null && pwd -P)" || {
            _tree_worktree_error "Cannot canonicalize the target repository identity."
            return 1
        }
        [[ "$target_common_dir" == "$common_dir" ]] || {
            _tree_worktree_error "Target '$target_path' belongs to a different repository."
            return 1
        }

        git -C "$target_path" reset --hard "$target_sha" >/dev/null || {
            _tree_worktree_error "Unable to reset '$target_path' to origin/main $target_sha."
            return 1
        }
        git -C "$target_path" checkout -B "$target_name" "$target_sha" >/dev/null 2>&1 || {
            _tree_worktree_error "Unable to attach '$target_name' at origin/main $target_sha."
            return 1
        }
        git -C "$target_path" clean -fd >/dev/null || {
            _tree_worktree_error "Unable to remove non-ignored untracked files from '$target_path'."
            return 1
        }
    else
        if git -C "$primary_path" show-ref --verify --quiet "refs/heads/$target_name"; then
            add_mode="-B"
        else
            add_mode="-b"
        fi
        git -C "$primary_path" worktree add "$add_mode" "$target_name" "$target_path" "$target_sha" >/dev/null 2>&1 || {
            _tree_worktree_error "Failed to create '$target_path' at origin/main $target_sha."
            return 1
        }
    fi

    [[ "$(git -C "$target_path" rev-parse HEAD 2>/dev/null)" == "$target_sha" ]] || {
        _tree_worktree_error "Postcondition failed: '$target_path' is not at origin/main $target_sha."
        return 1
    }
    _tree_worktree_provision_beads_redirect "$primary_path" "$target_path" || {
        _tree_worktree_error "Failed to provision .beads/redirect in '$target_path'."
        return 1
    }
    cd "$target_path" || {
        _tree_worktree_error "Failed to enter '$target_path'."
        return 1
    }
    printf '%s\n' "$target_path"
}

_tree_worktree_main "$@"
_tree_worktree_status=$?
unset -f _tree_worktree_main _tree_worktree_provision_beads_redirect _tree_worktree_info _tree_worktree_error
return "$_tree_worktree_status" 2>/dev/null || exit "$_tree_worktree_status"
