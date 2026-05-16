import subprocess
import tempfile
import unittest
from pathlib import Path

from repowhisper.git import changed_paths


class GitTests(unittest.TestCase):
    def test_changed_paths_are_relative_to_scan_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (root / "README.md").write_text("# Sample\n", encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "feature.py").write_text("def feature():\n    return 1\n", encoding="utf-8")

            self.assertEqual(["README.md", "src/feature.py"], changed_paths(root))
            self.assertEqual(["feature.py"], changed_paths(root / "src"))


if __name__ == "__main__":
    unittest.main()
