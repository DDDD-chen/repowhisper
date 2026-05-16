# Launch Copy

## GitHub Repository Description

Generate compact AI-ready briefs for any code repository. Local-only, zero-dependency CLI for Codex, Claude, Cursor, and other coding agents.

## Hacker News

Title:

Show HN: RepoWhisper - generate AI-ready context briefs for code repos

Body:

I built RepoWhisper because I kept seeing coding agents make avoidable mistakes
when they entered a repo with poor context.

It is a small Python CLI with zero runtime dependencies. Run it inside any repo
and it generates a compact Markdown or JSON brief: project map, manifests,
entrypoints, tests, likely commands, warning signs, and a paste-ready prompt pack.
It can also generate an `AGENTS.md` starter file.

The tool is local-only. No API key, no upload, no telemetry.

I would love feedback on what signals make an agent most effective when it sees a
repo for the first time.

## X / Twitter

I made RepoWhisper: a zero-dependency CLI that turns any codebase or current git
diff into an AI-ready brief for Codex, Claude, Cursor, and other coding agents.

It scans locally and outputs:
- project map
- manifests and entrypoints
- tests and likely commands
- compact snippets
- diff-focused prompt packs
- optional AGENTS.md

No API key. No upload.

Try:

```bash
repowhisper . --diff --copy
```

## LinkedIn

I released RepoWhisper, a small open-source CLI for teams using AI coding tools.

The problem it solves is simple: coding agents often start with incomplete
repository context. RepoWhisper scans a repo locally and generates a concise
brief with the files, commands, conventions, and risk signals an agent should see
first.

It is intentionally boring infrastructure: zero runtime dependencies, Markdown
and JSON output, diff-focused briefs, clipboard handoff, and an optional
`AGENTS.md` generator.

I am looking for feedback from developers using Codex, Claude, Cursor, Copilot,
or similar tools in real repositories.

## Reddit / Dev Tool Communities

I built a small CLI that generates "repo briefs" for coding agents.

The idea: before asking an agent to change a codebase, give it a compact map of
the repo: entrypoints, manifests, tests, likely commands, docs, config, and a few
high-signal snippets.

It runs locally, has no runtime dependencies, and can output Markdown or JSON.
It can also generate a starter `AGENTS.md`.

I am especially interested in what signals people think should be included or
excluded for larger monorepos.
