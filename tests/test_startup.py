"""Проверки настроек и выполнения стартового скрипта."""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from src.errors import ShellError
from src.main import parse_args, run_script
from src.shell import Shell


class StartupTests(unittest.TestCase):
    """Проверить echo, exit и остановку по ошибке."""

    def run_text(self, text):
        """Выполнить временный скрипт и вернуть вывод."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "start.txt"
            path.write_text(text, encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                run_script(Shell(), path)
            return output.getvalue()

    def test_parameters(self):
        """Оба параметра принимают пользовательские пути."""
        args = parse_args(["--vfs", "a.json", "--script", "b.txt"])
        self.assertEqual((args.vfs, args.script), ("a.json", "b.txt"))

    def test_echo_and_exit(self):
        """Комментарии пропускаются, после exit команды не выполняются."""
        output = self.run_text("# comment\nls\nexit\nunknown\n")
        self.assertIn("$ ls", output)
        self.assertNotIn("unknown", output)

    def test_error_stops_script(self):
        """Ошибка включает номер строки и останавливает скрипт."""
        with self.assertRaisesRegex(ShellError, "строка 2"):
            self.run_text("ls\nunknown\nexit\n")

    def test_missing_script(self):
        """Отсутствующий скрипт дает понятную ошибку."""
        with self.assertRaisesRegex(ShellError, "прочитать скрипт"):
            run_script(Shell(), "does-not-exist.txt")
