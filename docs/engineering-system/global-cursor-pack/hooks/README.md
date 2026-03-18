# Hook templates (global install)

These hooks are **templates**. Copy them to a directory that your environment runs (e.g. a scripts directory or Cursor-triggered path) and make them executable. They are not executed from this repo.

## Behaviors

- **destructive-guard:** Warn or block obviously destructive shell commands (e.g. `rm -rf` on broad paths, `git push --force` to main). Example: grep command for dangerous patterns and exit 1 or warn.
- **protected-branch:** Warn on direct push to protected branches (e.g. main, production). Example: check branch name and abort with message.
- **issue-awareness:** Remind to reference an issue in branch name or commit when creating a branch or committing (optional; can print a reminder only).
- **docs-reminder:** After architecture/API/config changes, print a reminder to update docs. Can be run as a post-command or checklist.
- **sensitive-file:** Flag edits to env files, auth config, migrations, infra configs. Example: list of path patterns; warn if any modified file matches.

## Install

1. Copy the script(s) you want to a path in your `PATH` or to a directory your workflow invokes.
2. `chmod +x` the scripts.
3. Integrate with your flow (e.g. git pre-commit, Cursor task, or manual checklist). Cursor does not run shell hooks automatically; you need to wire them (e.g. run script before commit via git hook or team process).

## Example locations

- Git hooks: `.git/hooks/pre-commit` (repo-specific) or a global git template dir.
- Team script dir: e.g. `~/bin/` or `~/.cursor/hooks/` (if you run them from Cursor tasks).
