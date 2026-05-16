# Contributing

Thanks for helping make RepoWhisper more useful.

The best contributions are small examples of repository shapes where the brief
could be sharper: monorepos, mixed-language projects, unusual test layouts, or
framework-specific commands.

## Development

Run tests:

```bash
python3 -m unittest discover -s tests
```

Run the CLI against this repository:

```bash
python3 -m repowhisper . --profile codex
```

Generate local artifacts:

```bash
python3 -m repowhisper . --write repowhisper.md --agents
```

## Pull Requests

- Keep changes focused.
- Add or update tests for scanner behavior.
- Prefer deterministic output so generated briefs are easy to diff.
- Avoid adding runtime dependencies unless the benefit is clearly worth it.

## Useful Test Cases

Good fixtures include:

- dependency folders that should be skipped
- project manifests with command scripts
- source files mixed with generated files
- nested tests or framework-specific test names
- repositories with existing `AGENTS.md`, `CLAUDE.md`, or Cursor rules
