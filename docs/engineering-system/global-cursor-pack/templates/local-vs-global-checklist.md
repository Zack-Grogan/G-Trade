# Local vs global checklist

Use when adding a new config or automation.

- [ ] **Commit to repo:** Repo-specific behavior, conventions, docs, templates, scripts that only read/write repo paths. No secrets.
- [ ] **Global user config:** MCP URLs/tokens, Cursor settings, user-level hooks. Never commit secrets.
- [ ] **Global team config:** Linear workspace, GitHub org, Railway project, branch protection. Manual admin.
- [ ] **Hybrid:** Template in repo (e.g. under global-cursor-pack/); install or copy to user/team config with documented steps.
- [ ] **Manual external step:** Auth, OAuth, or admin UI. Document in global-setup-guide.md; do not claim "done" in repo.
