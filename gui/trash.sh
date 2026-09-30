#!/bin/bash
# The GUI passes exact, reviewed paths and identities; Mole owns the Trash sink.
set -euo pipefail

if [[ "$EUID" -eq 0 ]]; then
    echo "Run the GUI as your regular user, without sudo." >&2
    exit 1
fi

if [[ $# -ne 4 || ! "$3" =~ ^[0-9]+:[0-9]+:-?[0-9]+$ || ! "$4" =~ ^[0-9]+:[0-9]+$ ]]; then
    echo "The selection is invalid. Refresh the folder and review it again." >&2
    exit 1
fi
readonly GUI_TARGET="$2"
case "$1" in
    preview)
        export MOLE_DRY_RUN=1
        export DRY_RUN=true
        ;;
    trash)
        export MOLE_DRY_RUN=0
        export DRY_RUN=false
        ;;
    *) exit 1 ;;
esac
export MOLE_DELETE_MODE=trash
export MOLE_CURRENT_COMMAND=analyze
export MOLE_UNINSTALL_MODE=0

# Personal folder roots stay put. No arbitrary API-supplied path may reach the
# shared helper, even if this bridge is called independently of the server.
if [[ "$2" == */ ]]; then
    echo "A trailing-slash selection is invalid. Refresh the folder and review it again." >&2
    exit 1
fi
case "$2" in
    "$HOME/Downloads/"* | "$HOME/Desktop/"* | "$HOME/Documents/"* | \
        "$HOME/Pictures/"* | "$HOME/Movies/"* | "$HOME/Music/"*) ;;
    *)
        echo "Only reviewed items inside personal folders can be moved to Trash here." >&2
        exit 1
        ;;
esac
case "/${2#"$HOME/"}/" in
    */.* | *.[Aa][Pp][Pp]/* | */[Ll][Ii][Bb][Rr][Aa][Rr][Yy]/*)
        echo "Hidden state, applications, and Library paths are kept. Use Mole in Terminal for these paths." >&2
        exit 1
        ;;
esac

GUI_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=lib/core/common.sh
source "$GUI_ROOT/lib/core/common.sh"
# shellcheck source=lib/manage/whitelist.sh
source "$GUI_ROOT/lib/manage/whitelist.sh"
load_whitelist clean

if should_protect_path "$2" || is_path_whitelisted "$2"; then
    echo "Mole protects this path. Keep it, or review its protection in mo clean --whitelist." >&2
    exit 1
fi

# Rebind the approved physical parent before the shared helper captures its
# own snapshot and checks it again immediately before moving to Trash.
if [[ -L "$2" || (! -f "$2" && ! -d "$2") ]] ||
    ! _mole_path_matches_identity "$2" "${2%/*}" "$4" "${3%:*}" ||
    [[ "$("$STAT_BSD" -f '%u' "$2" 2> /dev/null)" != "$EUID" ]]; then
    echo "The item or its folder changed. Refresh the folder and review the selection again." >&2
    exit 1
fi

# Preserve the shared helper's identity rebind, live-state guards and logging.
# Trash failures never fall back to permanent deletion or elevated privileges.
if [[ "$1" == preview ]]; then
    mole_delete "$2" false "$3"
    exit $?
fi

GUI_PYTHON="${MOLE_GUI_PYTHON:-python3}"
GUI_DELETE_LOG="${MOLE_DELETE_LOG:-$HOME/Library/Logs/mole/deletions.log}"
GUI_LOG_HELPER="$GUI_ROOT/gui/attempt_log.py"
GUI_BEFORE=$("$GUI_PYTHON" "$GUI_LOG_HELPER" capture "$GUI_DELETE_LOG") || {
    echo "Mole's deletion log cannot be verified. Review its permissions or move the item in Finder." >&2
    exit 1
}
GUI_ATTEMPT_TOKEN="gui-$$-$RANDOM"
if [[ "${MO_NO_OPLOG:-}" != 1 ]]; then
    log_operation analyze TRASH_ATTEMPT "$GUI_TARGET" "GUI $GUI_ATTEMPT_TOKEN; outcome pending"
    "$GUI_PYTHON" "$GUI_LOG_HELPER" pending "$OPERATIONS_LOG_FILE" "$GUI_TARGET" "$GUI_ATTEMPT_TOKEN" || {
        echo "The pending Trash attempt could not be recorded. Review Mole's log permissions or use Finder." >&2
        exit 1
    }
fi

# A killed helper leaves the durable pending row behind. Normal refusals add
# an unconfirmed outcome; neither record guesses a restore destination.
gui_attempt_unconfirmed() {
    if [[ "${MO_NO_OPLOG:-}" != 1 ]]; then
        log_operation analyze TRASH_UNCONFIRMED "$GUI_TARGET" "GUI $GUI_ATTEMPT_TOKEN; check the folder and Trash"
        "$GUI_PYTHON" "$GUI_LOG_HELPER" sync "$OPERATIONS_LOG_FILE" || true
    fi
}
trap gui_attempt_unconfirmed EXIT

if ! mole_delete "$2" false "$3"; then
    echo "Mole did not confirm the move. Check the folder and Trash before another review." >&2
    exit 1
fi
if [[ -e "$2" || -L "$2" ]] ||
    ! "$GUI_PYTHON" "$GUI_LOG_HELPER" confirmed "$GUI_DELETE_LOG" "$GUI_BEFORE" "$GUI_TARGET"; then
    echo "The move outcome is unconfirmed. Check the folder and Trash; absence alone is not a move receipt." >&2
    exit 1
fi
if [[ "${MO_NO_OPLOG:-}" != 1 ]]; then
    "$GUI_PYTHON" "$GUI_LOG_HELPER" sync "$OPERATIONS_LOG_FILE" || {
        echo "The move's operation log could not be persisted. Check the folder and Trash." >&2
        exit 1
    }
fi
trap - EXIT
printf '%s\n' GUI_TRASH_CONFIRMED
