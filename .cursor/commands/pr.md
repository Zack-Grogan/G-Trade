---
name: pr
description: Create PR with tests and review. Verifies branch, runs tests, dispatches code-reviewer, creates PR via GitHub.
---

# PR

1. **Verify branch** - Confirm current branch and changes:
   ```bash
   git branch --show-current
   git status
   git diff main...HEAD
   ```

2. **Run tests** - Execute test suite (see test command):
   ```bash
   pytest
   ```

3. **Review** - Dispatch code-reviewer for pre-PR review.

4. **Create PR** - Open PR via GitHub MCP or CLI:
   ```bash
   gh pr create --title "<title>" --body "<description>"
   ```

5. **Link issue** - If Linear issue exists, link in PR body and description.

6. **Update status** - Move Linear issue to In Review (if applicable).
