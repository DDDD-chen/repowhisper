from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(frozen=True)
class FileInfo:
    path: str
    suffix: str
    size: int
    lines: int
    kind: str
    score: int
    reason: str


@dataclass(frozen=True)
class Snippet:
    path: str
    start_line: int
    content: str
    reason: str


@dataclass
class RepoBrief:
    root: Path
    name: str
    files: List[FileInfo]
    skipped_count: int
    total_bytes: int
    language_bytes: Dict[str, int]
    manifests: List[FileInfo] = field(default_factory=list)
    docs: List[FileInfo] = field(default_factory=list)
    tests: List[FileInfo] = field(default_factory=list)
    configs: List[FileInfo] = field(default_factory=list)
    ci: List[FileInfo] = field(default_factory=list)
    entrypoints: List[FileInfo] = field(default_factory=list)
    snippets: List[Snippet] = field(default_factory=list)
    commands: Dict[str, List[str]] = field(default_factory=dict)
    stack: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    tree_lines: List[str] = field(default_factory=list)

    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def line_count(self) -> int:
        return sum(item.lines for item in self.files)

    @property
    def top_files(self) -> List[FileInfo]:
        return sorted(self.files, key=lambda item: (-item.score, item.path))
