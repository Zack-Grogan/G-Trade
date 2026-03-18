# Deciding local vs global

1. Is it repo-specific (conventions, entry points, module names, this app's config)? → **Commit to repo.**
2. Does it contain secrets or auth? → **Never in repo.** Global user/team config or env.
3. Is it a template to reuse in other repos? → **Commit to repo** under docs/engineering-system/global-cursor-pack/ or templates/; install/copy is **manual global** step.
4. Does it require Linear/GitHub/Railway admin or OAuth? → **Manual external admin step.** Document in global-setup-guide.md.
5. Use the checklist in templates/local-vs-global-checklist.md when adding new config or automation.
