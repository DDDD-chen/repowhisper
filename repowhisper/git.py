import subprocess
from pathlib import Path
from typing import Iterable, List, Optional, Set


class GitError(RuntimeError):
    pass


def changed_paths(root: Path, base: Optional[str] = None) -> List[str]:
    root = root.expanduser().resolve()
    top = Path(_git(root, "rev-parse", "--show-toplevel").strip()).resolve()
    paths: Set[str] = set()

    if base:
        paths.update(_lines(_git(top, "diff", "--name-only", "--diff-filter=ACMRTUXB", f"{base}...HEAD")))

    paths.update(_lines(_git(top, "diff", "--name-only", "--diff-filter=ACMRTUXB")))
    paths.update(_lines(_git(top, "diff", "--cached", "--name-only", "--diff-filter=ACMRTUXB")))
    paths.update(_lines(_git(top, "ls-files", "--others", "--exclude-standard")))
    return sorted(_relative_to_root(top / path, root) for path in paths if path and _is_under(top / path, root))


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ("git", *args),
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError as exc:
        raise GitError("git is not installed or not on PATH") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise GitError(detail or f"git {' '.join(args)} failed") from exc
    return result.stdout


def _lines(text: str) -> Iterable[str]:
    return (line.strip() for line in text.splitlines())


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
    except ValueError:
        return False
    return True


def _relative_to_root(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()
