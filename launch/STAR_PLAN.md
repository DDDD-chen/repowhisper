# RepoWhisper Launch Plan

Goal: make the repository useful enough that developers star it because they want
to try it, remember it, or share it with a teammate.

## Positioning

One-line pitch:

> RepoWhisper generates a compact AI-ready brief for any codebase so coding
> agents start with the right map instead of the loudest files.

Core proof points:

- zero runtime dependencies
- local only, no API key or upload
- Markdown and JSON output
- optional `AGENTS.md` generation
- useful before Codex, Claude, Cursor, and PR reviews

## Launch Checklist

- Publish a public GitHub repository with a clear README
- Add topics: `ai`, `agents`, `codex`, `claude`, `cursor`, `cli`, `developer-tools`
- Pin the repository on the GitHub profile
- Cut `v0.1.0` with release notes
- Post the demo output as a screenshot or gist
- Reply to comments with examples, not slogans
- Track stars hourly with `scripts/star_watch.py`

## Ethical Distribution

Do:

- share in communities where coding agents and developer tools are on-topic
- show concrete before/after prompt quality
- ask for feedback, issues, and examples
- be transparent that this is an early project

Do not:

- buy stars
- mass-DM strangers
- post identical copy everywhere
- use misleading claims about adoption
- ask people to star before they understand the tool

## Hourly Monitoring

```bash
python3 scripts/star_watch.py DDDD-chen/repowhisper --interval 3600 --out stars.jsonl
```

One-shot check:

```bash
python3 scripts/star_watch.py DDDD-chen/repowhisper --once
```
