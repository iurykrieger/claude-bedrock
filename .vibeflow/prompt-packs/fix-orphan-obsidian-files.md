You are only seeing this prompt; there is no context outside it.

---

## Objective

Filter the `obsidian/*.md` copy step in `/bedrock:preserve` Phase 0.2 Step 4 so that node files whose `source_file` frontmatter points to a `/tmp/` path are **not** copied into the vault's cumulative `graphify-out/obsidian/`. This stops the accumulation of permanently orphaned visualization files after each `/bedrock:teach` run.

---

## Definition of Done

- [ ] The bash loop in Phase 0.2 Step 4 of `skills/preserve/SKILL.md` skips any incoming `.md` file whose `source_file` frontmatter value starts with `/tmp/`.
- [ ] Files whose `source_file` is a stable path (repo path, vault path, or empty/absent) are still copied/appended as before.
- [ ] The `graph.json` merge logic (Steps 1–3) is untouched.
- [ ] No new files are created; only `skills/preserve/SKILL.md` is modified.
- [ ] The change is self-documenting in the skill prose (a brief inline note explaining why).

---

## Anti-scope

- Do NOT modify `skills/teach/SKILL.md` — keep `--obsidian` in the graphify invocation.
- Do NOT add cleanup logic for existing orphan files already in the vault (that's a one-shot maintenance task, not a code change).
- Do NOT touch `graph.json` merge logic (Steps 1–3 of Phase 0.2).
- Do NOT add `--obsidian` flag handling or new CLI arguments anywhere.
- Do NOT modify any other skill (`compress`, `sync`, `query`, `setup`).

---

## Budget

≤ 1 file: `skills/preserve/SKILL.md`

---

## Patterns to Follow

**Skill structure (from `.vibeflow/patterns/skill-architecture.md`):**
- Skills are plain markdown — no code runtime. Changes are prose + bash snippets embedded as fenced code blocks.
- Numbered phases use decimal sub-notation: Phase 0.2 Step 4.
- Add no new phase or step; modify only the bash block inside the existing Step 4.

**Bash conventions observed in this codebase:**
```bash
# Pattern already used in Phase 0.2 Step 1 (validation guard):
if [ ! -s "<graphify_output_path>/graph.json" ]; then
  echo "ERROR: ..."
  exit 1
fi

# Pattern for reading frontmatter fields already used elsewhere in the skill:
src_path=$(awk -F'"' '/^source_file:/{print $2; exit}' "$src")
```

**Writing rules:**
- No comments in skill files explaining "why this was added" from a PR perspective — but a short inline note in the prose is acceptable when the guard condition is non-obvious.
- Skill prose is in English; bash variable names are uppercase.

---

## Where to Work

**File:** `skills/preserve/SKILL.md`  
**Section:** Phase 0.2 — **Step 4 — Append `obsidian/*.md` files** (around line 242–260)

Current Step 4 bash block:

```bash
mkdir -p "<VAULT_PATH>/graphify-out/obsidian"
for src in "<graphify_output_path>/obsidian/"*.md; do
  [ -e "$src" ] || continue
  dest="<VAULT_PATH>/graphify-out/obsidian/$(basename "$src")"
  if [ -e "$dest" ]; then
    printf '\n\n---\n\n' >> "$dest"
    cat "$src" >> "$dest"
  else
    cp "$src" "$dest"
  fi
done
```

The fix goes **inside the loop, immediately after the `[ -e "$src" ] || continue` guard**, before the `dest=` line.

---

## Directional Guidance

Add a `source_file` guard using `awk` to extract the value from the file's YAML frontmatter. If the extracted path starts with `/tmp/`, skip the file with `continue`. Keep the `awk` expression consistent with how other frontmatter fields are read elsewhere in the skill (single-pass, exit on first match).

Update the Step 4 prose description (the two bullet points above the bash block) to mention that files with a `/tmp/` `source_file` are skipped — one sentence is enough.

Avoid `grep -P`, `sed -E`, or `python3` for this guard — the `awk` one-liner is the lightest option and consistent with what's already in the skill.

---

## How to Run / Test

This project has no automated test runner. Validate the change manually:

1. Read the modified Step 4 block and confirm the `awk` guard is syntactically correct bash.
2. Confirm the guard only affects the `obsidian/*.md` copy step — not `graph.json`, `GRAPH_REPORT.md`, or `.graphify_analysis.json` steps.
3. Mentally trace through two cases:
   - `source_file: "/tmp/bedrock-teach-1234/graphify-out/obsidian/foo.md"` → skipped (starts with `/tmp/`).
   - `source_file: "/Users/dev/vault/actors/billing-api.md"` → copied as before.
4. Confirm no other section of `skills/preserve/SKILL.md` references Step 4 in a way that would be broken by this change.

After implementing, run `/vibeflow:audit` to verify.
