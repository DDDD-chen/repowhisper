import unittest
from unittest import mock

from repowhisper.cli import copy_to_clipboard


class CliTests(unittest.TestCase):
    def test_copy_to_clipboard_uses_first_available_command(self) -> None:
        with mock.patch("repowhisper.cli.shutil.which", side_effect=lambda name: "/usr/bin/pbcopy" if name == "pbcopy" else None):
            with mock.patch("repowhisper.cli.subprocess.run") as run:
                copy_to_clipboard("hello")

        run.assert_called_once_with(("pbcopy",), input="hello", text=True, check=True)

    def test_copy_to_clipboard_errors_without_backend(self) -> None:
        with mock.patch("repowhisper.cli.shutil.which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "No supported clipboard"):
                copy_to_clipboard("hello")

    def test_copy_to_clipboard_reports_failed_backend(self) -> None:
        with mock.patch("repowhisper.cli.shutil.which", return_value="/usr/bin/pbcopy"):
            with mock.patch("repowhisper.cli.subprocess.run", side_effect=OSError("blocked")):
                with self.assertRaisesRegex(RuntimeError, "Clipboard command failed"):
                    copy_to_clipboard("hello")


if __name__ == "__main__":
    unittest.main()
