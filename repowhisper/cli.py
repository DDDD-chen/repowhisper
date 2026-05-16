import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from . import __version__
from .render import render_agents, render_json, render_markdown, write_output
from .scanner import scan_repository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repowhisper",
        description="Generate a compact AI-ready brief for a code repository.",
    )
    parser.add_argument("path", nargs="?", default=".", help="Repository path to scan.")
    parser.add_argument("--write", metavar="FILE", help="Write output to FILE instead of stdout.")
    parser.add_argument(
        "--agents",
        action="store_true",
        help="Write AGENTS.md in the scanned repository.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format.",
    )
    parser.add_argument(
        "--profile",
        choices=("generic", "codex", "claude", "cursor"),
        default="generic",
        help="Tune wording for a target coding assistant.",
    )
    parser.add_argument("--max-files", type=int, default=400, help="Maximum files to scan.")
    parser.add_argument("--max-depth", type=int, default=5, help="Maximum tree depth to render.")
    parser.add_argument(
        "--max-snippet-lines",
        type=int,
        default=24,
        help="Maximum lines per compact snippet.",
    )
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        help="Glob of files to include. Can be repeated.",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Glob of files to exclude. Can be repeated.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        brief = scan_repository(
            Path(args.path),
            max_files=args.max_files,
            max_depth=args.max_depth,
            max_snippet_lines=args.max_snippet_lines,
            include=args.include,
            exclude=args.exclude,
        )
    except (FileNotFoundError, NotADirectoryError, PermissionError) as exc:
        parser.error(str(exc))
        return 2

    if args.format == "json":
        content = render_json(brief)
    else:
        content = render_markdown(brief, profile=args.profile)

    if args.write:
        output_path = Path(args.write).expanduser()
        if not output_path.is_absolute():
            output_path = Path.cwd() / output_path
        write_output(output_path, content)
        print(f"Wrote {output_path}", file=sys.stderr)
    else:
        sys.stdout.write(content)

    if args.agents:
        agents_path = brief.root / "AGENTS.md"
        write_output(agents_path, render_agents(brief))
        print(f"Wrote {agents_path}", file=sys.stderr)

    return 0
