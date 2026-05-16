#!/usr/bin/env python3
"""Poll GitHub stars for a repository and append JSONL snapshots."""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Watch GitHub star count for a repository.")
    parser.add_argument("repo", help="Repository in owner/name form.")
    parser.add_argument("--interval", type=int, default=3600, help="Polling interval in seconds.")
    parser.add_argument("--once", action="store_true", help="Fetch one snapshot and exit.")
    parser.add_argument("--out", default="stars.jsonl", help="JSONL output path.")
    return parser.parse_args()


def fetch_stars(repo: str) -> int:
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "repowhisper-star-watch",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return int(payload["stargazers_count"])


def snapshot(repo: str) -> dict:
    return {
        "repo": repo,
        "stars": fetch_stars(repo),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    args = parse_args()
    out = Path(args.out)
    while True:
        try:
            item = snapshot(args.repo)
        except (urllib.error.URLError, KeyError, ValueError) as exc:
            item = {
                "repo": args.repo,
                "error": str(exc),
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
        line = json.dumps(item, sort_keys=True)
        print(line)
        with out.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        if args.once:
            return 0 if "stars" in item else 1
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
