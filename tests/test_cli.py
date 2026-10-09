"""Проверки приложения целиком через настоящий процесс Python."""

import subprocess
import sys
import unittest
from pathlib import Path


class CLITests(unittest.TestCase):
    """Проверить REPL, коды возврата и echo стартового скрипта."""

    def run_cli(self, args=(), text=""):
        """Запустить приложение с заданным стандартным вводом."""
        return subprocess.run(
            [sys.executable, "-m", "src.main", *args],
            input=text, text=True, capture_output=True, timeout=10)

    def test_repl(self):
        """После ошибочной команды REPL продолжает принимать ввод."""
        result = self.run_cli(text="unknown\ncd /home\nls\nexit\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("неизвестная команда", result.stdout)
        self.assertIn("deep:/home$", result.stdout)
        self.assertIn("student", result.stdout)

    def test_startup_error_stops(self):
        """Команды после ошибки, включая REPL, не выполняются."""
        result = self.run_cli(
            ["--script", "examples/scripts/stage2_error.txt"],
            text="mkdir /must-not-run\nexit\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("строка 2", result.stdout)
        self.assertNotIn("must-not-run", result.stdout)

    def test_missing_vfs_and_script(self):
        """Ошибки входных файлов имеют код возврата 1."""
        for args in (["--vfs", "absent.json"],
                     ["--script", "absent.txt"]):
            with self.subTest(args=args):
                result = self.run_cli(args)
                self.assertEqual(result.returncode, 1)
                self.assertIn("Ошибка:", result.stdout)
                self.assertNotIn("Traceback", result.stderr)

    def test_invalid_parameter(self):
        """Неподдерживаемые параметры обрабатывает argparse."""
        self.assertEqual(self.run_cli(["--unknown"]).returncode, 2)

    def test_full_demo_and_source_integrity(self):
        """Полный пример завершается и оставляет оба JSON неизменными."""
        paths = [Path(f"examples/vfs/{n}.json") for n in ("deep", "files")]
        before = [path.read_bytes() for path in paths]
        result = self.run_cli(["--script", "examples/scripts/stage5.txt"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("files:/$", result.stdout)
        self.assertIn("/new/a/b/c", result.stdout)
        self.assertEqual([path.read_bytes() for path in paths], before)

    def test_script_without_exit_continues_to_repl(self):
        """Без exit после скрипта продолжается интерактивный ввод."""
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "start.txt"
            path.write_text("cd /home\n", encoding="utf-8")
            result = self.run_cli(["--script", str(path)], "ls\nexit\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("deep:/home$", result.stdout)
        self.assertIn("student", result.stdout)
