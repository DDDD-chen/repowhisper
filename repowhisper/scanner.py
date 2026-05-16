import ast
import fnmatch
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .models import FileInfo, RepoBrief, Snippet


SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    ".idea",
    ".vscode",
    "__pycache__",
    "bower_components",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "site-packages",
    "target",
    "vendor",
    "venv",
}

SKIP_FILE_GLOBS = {
    "*.7z",
    "*.avif",
    "*.bmp",
    "*.class",
    "*.dll",
    "*.dylib",
    "*.egg-info/*",
    "*.exe",
    "*.gif",
    "*.ico",
    "*.jar",
    "*.jpeg",
    "*.jpg",
    "*.lockb",
    "*.map",
    "*.min.css",
    "*.min.js",
    "*.mov",
    "*.mp3",
    "*.mp4",
    "*.o",
    "*.obj",
    "*.pdf",
    "*.png",
    "*.pyc",
    "*.pyo",
    "repowhisper.md",
    "*.so",
    "*.sqlite",
    "*.sqlite3",
    "*.tar",
    "*.tgz",
    "*.ttf",
    "*.webm",
    "*.webp",
    "*.woff",
    "*.woff2",
    "*.zip",
}

LANGUAGES = {
    ".c": "C",
    ".cc": "C++",
    ".clj": "Clojure",
    ".cpp": "C++",
    ".cs": "C#",
    ".css": "CSS",
    ".dart": "Dart",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".go": "Go",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".html": "HTML",
    ".java": "Java",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".lua": "Lua",
    ".md": "Markdown",
    ".php": "PHP",
    ".py": "Python",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".scala": "Scala",
    ".sh": "Shell",
    ".sql": "SQL",
    ".svelte": "Svelte",
    ".swift": "Swift",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".vue": "Vue",
}

MANIFEST_NAMES = {
    "Cargo.toml",
    "Gemfile",
    "go.mod",
    "mix.exs",
    "package.json",
    "pom.xml",
    "pyproject.toml",
    "requirements.txt",
    "setup.cfg",
    "setup.py",
}

DOC_NAMES = {
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "README.md",
    "SECURITY.md",
}

AGENT_NAMES = {
    "AGENTS.md",
    "CLAUDE.md",
    ".cursorrules",
    ".cursor/rules",
    ".github/copilot-instructions.md",
}

ENTRYPOINT_NAMES = {
    "__main__.py",
    "app.py",
    "cli.py",
    "index.html",
    "index.js",
    "index.ts",
    "main.go",
    "main.py",
    "main.rs",
    "server.js",
    "server.ts",
}

CONFIG_NAMES = {
    ".editorconfig",
    ".env.example",
    ".eslintrc",
    ".gitignore",
    ".pre-commit-config.yaml",
    "Dockerfile",
    "Makefile",
    "docker-compose.yml",
    "eslint.config.js",
    "justfile",
    "mypy.ini",
    "ruff.toml",
    "tsconfig.json",
}


def scan_repository(
    root: Path,
    *,
    max_files: int = 400,
    max_depth: int = 5,
    max_snippet_lines: int = 24,
    include: Optional[Sequence[str]] = None,
    exclude: Optional[Sequence[str]] = None,
) -> RepoBrief:
    root = root.expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(str(root))
    if not root.is_dir():
        raise NotADirectoryError(str(root))

    include = tuple(include or ())
    exclude = tuple(exclude or ())
    candidates: List[Tuple[Path, str, int, str, int, str]] = []
    files: List[FileInfo] = []
    language_bytes: Dict[str, int] = defaultdict(int)
    skipped_count = 0

    for path in _walk_files(root):
        rel = _rel(path, root)
        if not _included(rel, include, exclude):
            skipped_count += 1
            continue
        if _should_skip_file(rel, path):
            skipped_count += 1
            continue
        if len(files) >= max_files:
            skipped_count += 1
            continue

        size = _safe_size(path)
        if size > 1_000_000:
            skipped_count += 1
            continue
        kind, score, reason = _classify(rel, path)
        candidates.append((path, rel, size, kind, score, reason))

    candidates.sort(key=lambda item: (-item[4], item[1]))
    selected = candidates[:max_files]
    skipped_count += max(0, len(candidates) - len(selected))

    for path, rel, size, kind, score, reason in selected:
        text = _read_text(path)
        if text is None:
            skipped_count += 1
            continue
        lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
        info = FileInfo(
            path=rel,
            suffix=path.suffix.lower(),
            size=size,
            lines=lines,
            kind=kind,
            score=score,
            reason=reason,
        )
        files.append(info)
        language_bytes[_language_for(path)] += size

    files.sort(key=lambda item: item.path)
    brief = RepoBrief(
        root=root,
        name=_detect_project_name(root) or root.name,
        files=files,
        skipped_count=skipped_count,
        total_bytes=sum(item.size for item in files),
        language_bytes=dict(sorted(language_bytes.items(), key=lambda item: (-item[1], item[0]))),
    )
    brief.manifests = [item for item in files if item.kind == "manifest"]
    brief.docs = [item for item in files if item.kind == "docs"]
    brief.tests = [item for item in files if item.kind == "test"]
    brief.configs = [item for item in files if item.kind == "config"]
    brief.ci = [item for item in files if item.kind == "ci"]
    brief.entrypoints = [item for item in files if item.kind == "entrypoint"]
    brief.commands = _detect_commands(root, brief.manifests)
    brief.stack = _detect_stack(brief)
    brief.warnings = _detect_warnings(brief)
    brief.tree_lines = _render_tree(files, max_depth=max_depth)
    brief.snippets = _collect_snippets(root, brief.top_files, max_snippet_lines)
    return brief


def _walk_files(root: Path) -> Iterable[Path]:
    for current, dir_names, file_names in os.walk(root):
        dir_names[:] = sorted(
            name for name in dir_names if name not in SKIP_DIRS and not name.startswith(".repowhisper")
        )
        for file_name in sorted(file_names):
            yield Path(current) / file_name


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _included(path: str, include: Sequence[str], exclude: Sequence[str]) -> bool:
    if include and not any(fnmatch.fnmatch(path, pattern) for pattern in include):
        return False
    return not any(fnmatch.fnmatch(path, pattern) for pattern in exclude)


def _should_skip_file(rel: str, path: Path) -> bool:
    base = path.name
    if base == ".DS_Store":
        return True
    return any(fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(base, pattern) for pattern in SKIP_FILE_GLOBS)


def _safe_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _read_text(path: Path) -> Optional[str]:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in data[:4096]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return data.decode("utf-8", errors="replace")
        except UnicodeDecodeError:
            return None


def _classify(rel: str, path: Path) -> Tuple[str, int, str]:
    name = path.name
    lower = rel.lower()
    if rel in AGENT_NAMES or name in AGENT_NAMES:
        return "agent", 100, "agent instructions"
    if name in MANIFEST_NAMES:
        return "manifest", 95, "project manifest"
    if rel.startswith(".github/workflows/"):
        return "ci", 80, "CI workflow"
    if name in DOC_NAMES or lower.startswith("docs/") or lower.endswith(".md"):
        return "docs", 65, "documentation"
    if _is_test_path(rel):
        return "test", 75, "test surface"
    if name in ENTRYPOINT_NAMES or lower.endswith("/cli.py"):
        return "entrypoint", 85, "likely entry point"
    if name in CONFIG_NAMES or lower.startswith(".github/"):
        return "config", 60, "configuration"
    if path.suffix.lower() in LANGUAGES:
        return "source", 50, "source file"
    return "other", 20, "supporting file"


def _is_test_path(rel: str) -> bool:
    lower = rel.lower()
    base = lower.rsplit("/", 1)[-1]
    return (
        lower.startswith("test/")
        or lower.startswith("tests/")
        or "/test/" in lower
        or "/tests/" in lower
        or base.startswith("test_")
        or base.endswith("_test.py")
        or base.endswith(".test.js")
        or base.endswith(".test.ts")
        or base.endswith(".spec.js")
        or base.endswith(".spec.ts")
    )


def _language_for(path: Path) -> str:
    if path.name in {"Dockerfile", "Makefile"}:
        return path.name
    return LANGUAGES.get(path.suffix.lower(), "Other")


def _detect_commands(root: Path, manifests: Sequence[FileInfo]) -> Dict[str, List[str]]:
    commands: Dict[str, List[str]] = defaultdict(list)
    manifest_paths = {item.path for item in manifests}

    if "package.json" in manifest_paths:
        data = _load_json(root / "package.json")
        if isinstance(data, dict):
            scripts = data.get("scripts")
            if isinstance(scripts, dict):
                for name in sorted(scripts):
                    commands["npm"].append(f"npm run {name}")

    if "pyproject.toml" in manifest_paths:
        text = _read_text(root / "pyproject.toml") or ""
        if "[project.scripts]" in text:
            commands["python"].append("python3 -m pip install -e .")
        if "[tool.pytest" in text or "pytest" in text:
            commands["python"].append("python3 -m pytest")
        if "unittest" in text:
            commands["python"].append("python3 -m unittest discover -s tests")

    if (root / "tests").is_dir() and any((root / "tests").glob("test*.py")):
        commands["python"].append("python3 -m unittest discover -s tests")

    if "requirements.txt" in manifest_paths:
        commands["python"].append("python3 -m pip install -r requirements.txt")

    if "Cargo.toml" in manifest_paths:
        commands["rust"].extend(["cargo test", "cargo run"])

    if "go.mod" in manifest_paths:
        commands["go"].extend(["go test ./...", "go run ."])

    if (root / "Makefile").exists():
        targets = _make_targets(root / "Makefile")
        commands["make"].extend(f"make {target}" for target in targets[:8])

    if not commands:
        commands["inspect"].append("No obvious commands detected. Check README and manifests.")

    return {key: sorted(set(value)) for key, value in sorted(commands.items())}


def _detect_project_name(root: Path) -> Optional[str]:
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        text = _read_text(pyproject) or ""
        in_project = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped == "[project]":
                in_project = True
                continue
            if stripped.startswith("[") and stripped.endswith("]"):
                in_project = False
            if in_project:
                match = re.match(r'name\s*=\s*["\']([^"\']+)["\']', stripped)
                if match:
                    return match.group(1)

    package_json = root / "package.json"
    if package_json.exists():
        data = _load_json(package_json)
        if isinstance(data, dict) and isinstance(data.get("name"), str):
            return str(data["name"])

    return None


def _load_json(path: Path) -> Optional[object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _make_targets(path: Path) -> List[str]:
    text = _read_text(path) or ""
    targets: List[str] = []
    for line in text.splitlines():
        match = re.match(r"^([A-Za-z0-9_.-]+):(?:\s|$)", line)
        if match and not match.group(1).startswith("."):
            targets.append(match.group(1))
    return targets


def _detect_stack(brief: RepoBrief) -> List[str]:
    names = {item.path for item in brief.files}
    suffixes = Counter(item.suffix for item in brief.files)
    stack: List[str] = []
    if "package.json" in names:
        stack.append("Node.js")
    if "pyproject.toml" in names or "requirements.txt" in names or suffixes[".py"]:
        stack.append("Python")
    if "Cargo.toml" in names or suffixes[".rs"]:
        stack.append("Rust")
    if "go.mod" in names or suffixes[".go"]:
        stack.append("Go")
    if suffixes[".tsx"] or suffixes[".jsx"]:
        stack.append("React-like UI")
    if "Dockerfile" in names or "docker-compose.yml" in names:
        stack.append("Docker")
    if brief.ci:
        stack.append("GitHub Actions")
    return stack or ["Unknown or mixed"]


def _detect_warnings(brief: RepoBrief) -> List[str]:
    warnings: List[str] = []
    names = {item.path for item in brief.files}
    if not brief.tests:
        warnings.append("No tests were detected in the scanned files.")
    if not any(item.path.lower().startswith("readme") for item in brief.docs):
        warnings.append("No README was detected.")
    if "AGENTS.md" not in names:
        warnings.append("No AGENTS.md was detected. Use --agents to generate one.")
    if brief.skipped_count > 25:
        warnings.append(f"{brief.skipped_count} files were skipped by limits or filters.")
    return warnings


def _render_tree(files: Sequence[FileInfo], max_depth: int) -> List[str]:
    tree: Dict[str, object] = {}
    for item in files:
        parts = item.path.split("/")
        cursor = tree
        for part in parts[:max_depth]:
            cursor = cursor.setdefault(part, {})  # type: ignore[assignment]
        if len(parts) > max_depth:
            cursor.setdefault("...", {})  # type: ignore[attr-defined]
    lines: List[str] = []

    def visit(node: Dict[str, object], prefix: str = "") -> None:
        items = sorted(node.items(), key=lambda pair: (bool(pair[1]), pair[0]))
        for index, (name, child) in enumerate(items):
            branch = "`-- " if index == len(items) - 1 else "|-- "
            lines.append(prefix + branch + name)
            if isinstance(child, dict) and child:
                next_prefix = prefix + ("    " if index == len(items) - 1 else "|   ")
                visit(child, next_prefix)

    visit(tree)
    return lines


def _collect_snippets(root: Path, top_files: Sequence[FileInfo], max_lines: int) -> List[Snippet]:
    snippets: List[Snippet] = []
    seen: Set[str] = set()
    for item in top_files:
        if item.path in seen or len(snippets) >= 12:
            continue
        seen.add(item.path)
        if item.size > 120_000:
            continue
        text = _read_text(root / item.path)
        if not text:
            continue
        content = _select_snippet(text, item.path, max_lines)
        if content.strip():
            snippets.append(Snippet(path=item.path, start_line=1, content=content, reason=item.reason))
    return snippets


def _select_snippet(text: str, path: str, max_lines: int) -> str:
    lines = text.splitlines()
    if path.endswith(".py"):
        summary = _python_symbol_summary(text)
        if summary:
            return "\n".join(summary[:max_lines])
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join(lines[:max_lines])


def _python_symbol_summary(text: str) -> List[str]:
    try:
        module = ast.parse(text)
    except SyntaxError:
        return []
    result: List[str] = []
    module_doc = ast.get_docstring(module)
    if module_doc:
        result.append('"""' + module_doc.splitlines()[0][:100] + '"""')
    for node in module.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.append(_signature(node))
        elif isinstance(node, ast.ClassDef):
            result.append(f"class {node.name}:")
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    result.append("    " + _signature(child))
    return result


def _signature(node: ast.AST) -> str:
    if isinstance(node, ast.AsyncFunctionDef):
        prefix = "async def"
        args = ast.unparse(node.args) if hasattr(ast, "unparse") else "..."
        return f"{prefix} {node.name}({args}):"
    if isinstance(node, ast.FunctionDef):
        args = ast.unparse(node.args) if hasattr(ast, "unparse") else "..."
        return f"def {node.name}({args}):"
    return ""
