# v0.2.0 Release Notes

RepoWhisper v0.2.0 adds the two workflows that make the tool easier to try in
real coding-agent sessions.

## Highlights

- `--diff` focuses the brief on current git changes while keeping core repo context
- `--base REF` compares against a base branch, for example `origin/main`
- `--copy` sends the generated brief straight to the system clipboard
- README first screen now shows the PR-review workflow more directly

## Example

```bash
repowhisper . --diff --copy
repowhisper . --diff --base origin/main --write pr-brief.md
```

## Why this matters

Full-repo briefs are useful when an agent enters a project cold. Diff briefs are
useful when you want an agent to review or continue a specific change without
losing repository context.
