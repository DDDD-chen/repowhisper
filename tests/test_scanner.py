import json
import tempfile
import unittest
from pathlib import Path

from repowhisper.render import render_json, render_markdown
from repowhisper.scanner import scan_repository


class ScannerTests(unittest.TestCase):
    def test_detects_python_project_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "pyproject.toml").write_text(
                """
[project]
name = "sample"

[project.scripts]
sample = "sample.cli:main"
""".strip(),
                encoding="utf-8",
            )
            (root / "README.md").write_text("# Sample\n", encoding="utf-8")
            (root / "sample").mkdir()
            (root / "sample" / "cli.py").write_text(
                "def main():\n    return 0\n",
                encoding="utf-8",
            )
            (root / "tests").mkdir()
            (root / "tests" / "test_cli.py").write_text(
                "def test_main():\n    assert True\n",
                encoding="utf-8",
            )

            brief = scan_repository(root)

            self.assertEqual("sample", brief.name)
            self.assertIn("Python", brief.stack)
            self.assertEqual(["pyproject.toml"], [item.path for item in brief.manifests])
            self.assertEqual(["sample/cli.py"], [item.path for item in brief.entrypoints])
            self.assertEqual(["tests/test_cli.py"], [item.path for item in brief.tests])
            self.assertIn("python3 -m pip install -e .", brief.commands["python"])

    def test_skips_dependency_folders(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "package.json").write_text(
                json.dumps({"scripts": {"test": "node test.js"}}),
                encoding="utf-8",
            )
            (root / "node_modules").mkdir()
            (root / "node_modules" / "leftpad.js").write_text("x\n", encoding="utf-8")

            brief = scan_repository(root)

            self.assertEqual(["package.json"], [item.path for item in brief.files])
            self.assertGreaterEqual(brief.skipped_count, 0)
            self.assertIn("npm run test", brief.commands["npm"])

    def test_json_and_markdown_render(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "go.mod").write_text("module example.com/sample\n", encoding="utf-8")
            (root / "main.go").write_text("package main\nfunc main() {}\n", encoding="utf-8")

            brief = scan_repository(root)
            markdown = render_markdown(brief, profile="codex")
            payload = json.loads(render_json(brief))

            self.assertIn("# Repo Brief:", markdown)
            self.assertIn("go test ./...", markdown)
            self.assertEqual(root.name, payload["name"])
            self.assertIn("Go", payload["stack"])

    def test_max_files_prefers_high_signal_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for index in range(20):
                (root / f"doc_{index:02d}.md").write_text("# doc\n", encoding="utf-8")
            (root / "pyproject.toml").write_text('[project]\nname = "sample"\n', encoding="utf-8")
            (root / "app.py").write_text("def main():\n    return 0\n", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "test_app.py").write_text("def test_app():\n    assert True\n", encoding="utf-8")

            brief = scan_repository(root, max_files=4)

            paths = {item.path for item in brief.files}
            self.assertIn("pyproject.toml", paths)
            self.assertIn("app.py", paths)
            self.assertIn("tests/test_app.py", paths)

    def test_focus_paths_keep_changed_files_and_core_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")
            (root / "pyproject.toml").write_text('[project]\nname = "sample"\n', encoding="utf-8")
            (root / "README.md").write_text("# Sample\n", encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "feature.py").write_text("def feature():\n    return 1\n", encoding="utf-8")
            for index in range(20):
                (root / f"doc_{index:02d}.md").write_text("# doc\n", encoding="utf-8")

            brief = scan_repository(root, max_files=5, focus_paths=["src/feature.py"])
            markdown = render_markdown(brief)

            paths = {item.path for item in brief.files}
            self.assertEqual("diff", brief.mode)
            self.assertEqual(["src/feature.py"], brief.focus_paths)
            self.assertIn("src/feature.py", paths)
            self.assertIn("AGENTS.md", paths)
            self.assertIn("pyproject.toml", paths)
            self.assertIn("## Changed Files", markdown)
            self.assertIn("changed file", next(item.reason for item in brief.files if item.path == "src/feature.py"))


if __name__ == "__main__":
    unittest.main()
