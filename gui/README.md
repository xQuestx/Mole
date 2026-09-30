# Mole local GUI

On macOS, double-click [Mole GUI.command](Mole%20GUI.command) in Finder. It opens Terminal, finds an existing Python 3.10 or newer, and opens the local browser interface. The launcher checks your PATH and common macOS Python locations; a failed or stalled runtime check tries the next candidate. It installs nothing. Keep its Terminal window open and press Ctrl+C to stop the server.

To start from this checkout in Terminal:

```bash
python3 gui/server.py
```

Use `python3 gui/server.py --no-open` to open the printed URL yourself. Keep the full URL, including its session token. Run as your regular Mac user, without sudo. There are no Python or JavaScript packages to install, external assets, background agents, launch-at-login tasks, or persistent GUI settings.

The interface provides Mole's command options and these on-demand views:

- **Disk explorer:** browse home folders, search names, sort rows, filter by type, minimum file size, or modification age, and page through results. Folder-only views disable the minimum file-size filter because an ordinary listing does not measure recursive folder sizes.
- **Folder measurements:** run Mole's `analyze --json` for the selected folder and view a proportional treemap. Its tiles represent positive, completely measured entries; partial or unavailable measurements appear separately. The largest twelve entries have individual tiles, with other measured entries grouped together. Folder tiles let you drill into another scan.
- **Cleanup and app previews:** inspect a forced, unprivileged dry-run and its full transcript. Standard cleanup can show rows from a fresh, complete shared Mole preview report. App previews resolve selected exact names against a fresh installed-app inventory and retain Mole's textual output.
- **System health, apps, and activity:** request a snapshot, search installed apps and sort by their reported size, or filter loaded activity by command, outcome, date, and text. Activity filters cover the latest available records, up to 200 per log.
- **Finder and Preview:** reveal discovered items in Finder and open supported regular image or PDF files in Preview. Symlinks are kept out of these actions.
- **Trash and recovery:** open your Mac's Trash and inspect confirmed moves from this GUI session or completed Trash outcomes in loaded activity. Restore items manually in Finder after checking their intended location. The GUI does not empty Trash or automatically restore paths.

The layout follows your system's light or dark appearance and supports smaller screens. Cmd+F or Ctrl+F focuses the current file, app, or activity search. Alt+Up goes to the parent folder when focus is outside an input. Escape clears a focused search or closes the mobile navigation; dialogs keep their own close controls.

Measurements, reports, and previews run as one cancellable task at a time. The task panel shows its stage, elapsed time, and completion or failure. Cancel stops the owned subprocess group and publishes cancellation only after the worker has stopped. Refreshing the browser recovers the current task while the server remains open. Tasks have bounded run times and completed results expire from the server's short session history. They do not run as background monitoring.

Cleanup and app previews also expose a bounded live tail of the output Mole actually emits, including a readable current partial line. Section headings and grouped discoveries can appear before the command finishes. This is not a complete record of every folder traversed: when Mole emits no new output, the last reported line stays visible beside the stage and elapsed time. Carriage-return progress replaces the current line, and terminal formatting is removed. The tail contains at most 120 lines with limits on individual lines and total text; it remains available after cancellation, failure, or active-task recovery. Reported output lines are not visited-file counts, progress percentages, deletion candidates, or authorization.

Disk totals and free space come from the filesystem hosting your home directory. Browser file sizes are current logical sizes; folder sizes stay unknown until explicitly measured. Each new measurement runs a fresh Mole scan. Completed tiles retain their sample time and coverage status, so remeasure after files change. The map's total covers its completely measured entries, not the whole volume. Moving items to Trash does not free their space, and the interface does not count Trash moves as reclaimed disk space.

Browser pages contain at most 200 rows. Discovery is limited to 20,000 entries or four seconds; a partial listing shows observed lower bounds rather than claiming complete counts or another page. Filtering and sorting scan current metadata again. Use Mole in Terminal when a complete listing exceeds these limits.

GUI cleanup and app previews are read-only inspections without administrator access. They can omit privileged or interactive checks, and their candidate rows never authorize a later removal. The standard cleanup report is shared with other Mole runs; a fresh, stable report is useful inspection evidence, not an exclusive per-run receipt. Ambiguous rows stay inspectable as raw text. Run actual maintenance and uninstall changes through the reviewed Terminal command.

Most commands open Mole in Terminal so its selection screens and existing authentication flows remain available. The launcher uses this checkout's `mole` executable. For `status` and `analyze`, it uses an installed `mo` if this checkout's Go helper is absent; run `make build` to use the checkout's Go helpers. The displayed checkout version can differ from an installed fallback's version. A successful Terminal handoff means the command was opened; read Terminal or Mole's activity logs for its actual outcome.

Cache cleanup, project purge, and installer removal normally remove their selected files permanently. Review their previews before execution. App uninstall defaults to Trash; its permanent option changes that behavior. The protected-path, protected-task, and project-directory managers edit configuration even when a preview option is also selected. Command help always opens help alone.

The browser permits navigation inside your home directory without following symbolic links. Its direct Trash action accepts only files or folders below Downloads, Desktop, Documents, Pictures, Movies, and Music. Those six roots, hidden paths, application bundles, Library paths, symlinks, and non-owned files are kept. Other home folders can be browsed, and Mole's Terminal analyzer remains available for other volumes and broader exploration.

Select up to five items and review their exact paths. Discovered selections expire after five minutes. A review runs Mole's actual deletion helper in dry-run mode; its confirmation receipt expires after two minutes and is usable once. Confirmation rechecks the selected target's device, inode, nanosecond modification time, size, and parent identity. The shell bridge rechecks the approved physical parent, applies Mole's protected-path and whitelist rules, and calls `mole_delete` with Trash mode forced and administrator access disabled. Mole rebinds the parent and target again at the Trash sink.

Each review helper gets a full 45-second budget, and each actual Trash attempt gets a full 120 seconds. Each operation has a 180-second overall budget; it stops before another helper when that helper's full budget would not fit. It never shortens a destructive attempt to the remaining few seconds. A started attempt writes and verifies a pending `TRASH_ATTEMPT` record in Mole's existing operation log before the move, unless `MO_NO_OPLOG=1` disables those records. Completed results require fresh native `trash`/`ok` deletion evidence for the exact reviewed path and the bridge's acknowledgement; source disappearance alone does not prove a move.

A selected directory is moved as a unit. Its identity checks do not freeze nested contents, and another process running as the same user can still race a pathname-based move. Failed or interrupted attempts stop later items. Results distinguish confirmed moves, attempted paths whose outcomes are unconfirmed, and paths whose helpers were never started. If a move times out or its evidence cannot be verified, check the folder and Trash before making another selection; it is never described as kept merely because confirmation failed. There is no permanent-delete fallback in the direct browser action.

The server binds only to `127.0.0.1` on an automatically chosen port. Each run generates a fresh access token. API calls require that token, the exact local Host, and a matching Origin when supplied. The token is carried in the URL fragment rather than query parameters; the server does not log request paths or tokens. Do not share the launcher URL.

Ctrl+C (SIGINT), Terminal hangup (SIGHUP), and SIGTERM all stop the server through graceful cleanup. The server rejects new work, cancels and joins read-only jobs, lets the current bounded Trash attempt finish, and stops before subsequent selected items. Repeated shutdown signals do not interrupt that cleanup. Its own temporary command files are removed after active requests finish. Terminal commands already handed off continue in Terminal; wait for a newly opened command to start before closing the launcher.

Run the isolated GUI and launcher tests from the checkout:

```bash
MOLE_TEST_NO_AUTH=1 python3 -m unittest discover -s gui -p 'test_*.py' -v
```

The tests use temporary home directories, fake Python launchers, mocked native app and Terminal launches, cancellable fixture jobs, and real helper moves into a temporary fixture Trash. They cover real server SIGHUP/SIGTERM shutdown, repeated signals during an isolated Trash attempt, nested child cleanup, full-budget dispatch, stale or missing move evidence, and disabled operation logging. Launcher tests cover paths with spaces, runtime versions, bounded hung probes, interruption, and child cleanup without opening a GUI. Real shell integration cases run only on macOS as a regular user. They do not clean personal data or request administrator authorization.
