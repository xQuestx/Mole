#!/bin/bash
# Open the local GUI in this Terminal session; Ctrl+C stops its server.
set -u

launcher_failure() {
    printf 'Mole GUI: %s\nNext: %s\n' "$1" "$2" >&2
    exit 1
}

# Reject root before resolving files or executing an interpreter from PATH.
if [[ "$EUID" -eq 0 ]]; then
    launcher_failure "Run as your regular Mac user." "Open this file without sudo."
fi

launcher_probe_pid=''
launcher_probe_cleanup() {
    [[ -n "$launcher_probe_pid" ]] || return 0
    if kill -TERM -- "-$launcher_probe_pid" 2> /dev/null; then
        /bin/sleep 0.1
        kill -KILL -- "-$launcher_probe_pid" 2> /dev/null || true
    fi
    wait "$launcher_probe_pid" 2> /dev/null || true
    launcher_probe_pid=''
}
trap launcher_probe_cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

launcher_source="${BASH_SOURCE[0]}"
case "$launcher_source" in
    /*) ;;
    *) launcher_source="$PWD/$launcher_source" ;;
esac

link_count=0
while [[ -L "$launcher_source" ]]; do
    link_count=$((link_count + 1))
    if [[ "$link_count" -gt 40 ]]; then
        launcher_failure "The launcher has a circular or overly long symlink chain." "Open gui/Mole GUI.command directly in the Mole checkout."
    fi
    launcher_dir=$(cd -P -- "${launcher_source%/*}" && pwd -P) ||
        launcher_failure "The launcher's folder is unavailable." "Open gui/Mole GUI.command from an intact Mole checkout."
    link_target=$(/usr/bin/readlink "$launcher_source") ||
        launcher_failure "The launcher symlink could not be read." "Open gui/Mole GUI.command directly in the Mole checkout."
    case "$link_target" in
        /*) launcher_source="$link_target" ;;
        *) launcher_source="$launcher_dir/$link_target" ;;
    esac
done

launcher_dir=$(cd -P -- "${launcher_source%/*}" && pwd -P) ||
    launcher_failure "The launcher's folder is unavailable." "Open gui/Mole GUI.command from an intact Mole checkout."
if [[ ! -f "$launcher_dir/server.py" ]]; then
    launcher_failure "server.py is missing beside this launcher." "Keep this file in the Mole checkout's gui folder and reopen it."
fi

python_supported() {
    [[ -x "$1" && ! -d "$1" ]] || return 1
    # A shadowed or broken interpreter must not strand the launcher. Job control
    # gives this probe its own process group so a timeout also stops its children.
    local probe_ticks=0 probe_status=0 monitor_was_set=0
    case "$-" in
        *m*) monitor_was_set=1 ;;
    esac
    set -m
    "$1" -I -c 'import sys; sys.exit(sys.version_info < (3, 10))' > /dev/null 2>&1 &
    launcher_probe_pid=$!
    while kill -0 "$launcher_probe_pid" 2> /dev/null; do
        if [[ "$probe_ticks" -ge 20 ]]; then
            launcher_probe_cleanup
            [[ "$monitor_was_set" -eq 1 ]] || set +m
            return 1
        fi
        /bin/sleep 0.1
        probe_ticks=$((probe_ticks + 1))
    done
    wait "$launcher_probe_pid" 2> /dev/null
    probe_status=$?
    # A wrapper may have exited while leaving a child behind.
    launcher_probe_cleanup
    [[ "$monitor_was_set" -eq 1 ]] || set +m
    return "$probe_status"
} 2> /dev/null

python_path=''
for python_command in python3 python3.14 python3.13 python3.12 python3.11 python3.10; do
    candidate=$(command -v "$python_command" 2> /dev/null) || continue
    if python_supported "$candidate"; then
        python_path="$candidate"
        break
    fi
done
if [[ -z "$python_path" ]]; then
    for candidate in "/opt/homebrew/bin/python3" "/usr/local/bin/python3" "/Library/Frameworks/Python.framework/Versions/Current/bin/python3" "/usr/bin/python3"; do
        if python_supported "$candidate"; then
            python_path="$candidate"
            break
        fi
    done
fi
if [[ -z "$python_path" ]]; then
    launcher_failure "Python 3.10 or newer was not found in PATH or common macOS locations." "Make a supported Python available as python3, verify python3 --version, then reopen this file."
fi

# Keep the foreground process and its exit status attached to Terminal.
exec "$python_path" "$launcher_dir/server.py" "$@"
