---
name: review
description: Code review via code-reviewer subagent. Identifies issues with correctness, security, maintainability, and performance.
---

# Review

1. **Identify target** - Determine what to review:
   - Current diff: `git diff`
   - Specific PR: `gh pr view <number>`
   - Branch comparison: `git diff main...<branch>`
   - Files in context: Current open files

2. **Dispatch reviewer** - Launch code-reviewer subagent:
   ```
   Task: code-reviewer
   Prompt: Review the following [target] for correctness, security, maintainability, and performance.
         Provide feedback with severity markers (blocker, suggestion, nit).
   ```

3. **Apply feedback** - Address review findings or relay results.

For PRs, consider dispatching **reality-checker** for final validation before merge.
