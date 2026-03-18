#!/usr/bin/env bash
# Converts agency-agents repo .md files to Cursor subagent format in .cursor/agents/
# Usage: run from G-Trade root, or pass AGENCY_REPO and DEST as env vars.

set -euo pipefail

AGENCY_REPO="${AGENCY_REPO:-/Users/zgrogan/Repos/agency-agents}"
DEST="${DEST:-$(cd "$(dirname "$0")/.." && pwd)/.cursor/agents}"

get_field() {
  local field="$1" file="$2"
  awk -v f="$field" '
    /^---$/ { fm++; next }
    fm == 1 && $0 ~ "^" f ": " { sub("^" f ": ", ""); print; exit }
  ' "$file"
}

get_body() {
  awk 'BEGIN{fm=0} /^---$/{fm++; next} fm>=2{print}' "$1"
}

slugify() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//'
}

mkdir -p "$DEST"
count=0

while IFS= read -r -d '' file; do
  name="$(get_field "name" "$file")"
  [[ -z "$name" ]] && continue
  description="$(get_field "description" "$file")"
  body="$(get_body "$file")"
  slug="$(slugify "$name")"
  [[ -z "$slug" ]] && continue

  # Cursor subagent format: name (slug), description, model
  {
    echo "---"
    echo "name: $slug"
    echo "description: ${description:-$name}"
    echo "model: inherit"
    echo "---"
    echo "$body"
  } > "$DEST/${slug}.md"
  (( count++ )) || true
done < <(find "$AGENCY_REPO" -name "*.md" -type f \
  \( -path "*/academic/*" -o -path "*/design/*" -o -path "*/engineering/*" -o -path "*/game-development/*" -o -path "*/marketing/*" -o -path "*/paid-media/*" -o -path "*/sales/*" -o -path "*/product/*" -o -path "*/project-management/*" -o -path "*/testing/*" -o -path "*/support/*" -o -path "*/spatial-computing/*" -o -path "*/specialized/*" \) \
  ! -name "README*" -print0)

echo "Converted $count agents to $DEST"
