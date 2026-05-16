# v0.1.0 Release Notes

RepoWhisper is a local-only CLI that generates compact repository briefs for AI
coding agents.

## Highlights

- Markdown and JSON output
- Optional `AGENTS.md` generation
- Stack, command, docs, test, CI, and entrypoint detection
- Common dependency/build/generated folder filtering
- Zero runtime dependencies
- Hourly GitHub star watcher script

## Suggested Repository Settings

Description:

> Generate compact AI-ready briefs for any code repository.

Topics:

```text
ai
agents
codex
claude
cursor
cli
developer-tools
repository-analysis
```

Website:

```text
https://github.com/DDDD-chen/repowhisper
```

## First Release Body

RepoWhisper v0.1.0 is the first public release.

It scans a repository locally and produces a compact context pack for coding
agents: project map, entrypoints, manifests, tests, likely commands, attention
points, compact snippets, and a paste-ready prompt pack.

This release is intentionally dependency-free and conservative. The next useful
step is collecting examples from real repositories where the scanner should pick
better first-read files or commands.
