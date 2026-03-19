# Future project starter

How to reuse this AI operating layer in a new repository.

## What to copy or run

1. **AGENTS.md** — Use the template in `docs/engineering-system/global-cursor-pack/templates/AGENTS-template.md`. Fill in repo purpose, entry points, modules, commands, and conventions.
2. **.cursor/rules/** — Copy the rule pack from this repo (00–80) or use the starter in `global-cursor-pack/templates/`. Adjust any repo-specific paths (e.g. plan file name) in the rules.
3. **Docs tree** — Use `global-cursor-pack/templates/docs-tree-starter` as a skeleton: architecture/, modules/, runbooks/, decisions/, engineering-system/. Add onboarding, testing, and README as needed.
4. **Docs-generation script** — Use the spec in `global-cursor-pack/templates/docs-generation-spec.md` and adapt `scripts/generate_docs_index.py` to the new stack (or port the script and adjust for different languages/tools).
5. **PR/issue templates** — Copy .github/pull_request_template.md and .github/ISSUE_TEMPLATE/ from this repo or from global-cursor-pack/templates/.

## Local vs global checklist

- **In repo:** AGENTS.md, .cursor/rules, docs skeleton, generate_docs_index script, .cursorignore, .github templates, workflow docs.
- **User/team:** MCP config (GitHub, Linear, OpenViking, and any optional provider), auth tokens, Cursor hooks if used. Use `global-cursor-pack/global-setup-guide.md` and install steps there.

## Init command or script

- A future `/init` or `scripts/init-ai-operating-layer.sh` could create the minimal skeleton (AGENTS.md, .cursor/rules, docs/engineering-system/, .github templates) in a new repo. The global-cursor-pack folder in this repo serves as the reference; the init would copy or expand templates. Not required for this repo; document the idea for reuse.
