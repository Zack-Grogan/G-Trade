# Docs tree starter

Minimal skeleton for a new repo:

```
docs/
  README.md           # Index; links to architecture, operator, onboarding
  architecture/
    overview.md       # What runs where, data flow, services
  modules/
    README.md         # Module map or links to code READMEs
  runbooks/
    # One .md per runbook (restart, deploy, incident)
  decisions/
    README.md         # ADRs or notable decisions (optional)
  engineering-system/
    overview.md       # AI operating layer, roles, generated docs
    local-vs-global.md
    cursor-operating-model.md
    linear-workflow.md
    github-workflow.md
    provider-usage-policy.md  # If using an external hosting provider
    openviking-integration.md  # If using OpenViking
    future-project-starter.md
  generated/          # Output of docs-generation script; do not edit
    README.md
  testing.md
  onboarding.md
```

Add runbooks, research, or product docs as needed. Keep authored docs authoritative; generated/ only from script.
