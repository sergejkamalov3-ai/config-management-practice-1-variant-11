"""Проверки парсера и команд первого этапа."""

import io
import unittest
from contextlib import redirect_stdout

from src.errors import ShellError
from src.shell import Shell


class ShellTests(unittest.TestCase):
    """Проверить ввод, выход и ошибки команд."""

    def setUp(self):
        """Создать новую оболочку."""
        self.shell = Shell()

    def test_parser(self):
        """Парсер разделяет последовательности пробелов."""
        output = io.StringIO()
        with redirect_stdout(output):
            self.shell.execute("  find    /  ")
        self.assertEqual(output.getvalue(), "/\n")

    def test_empty(self):
        """Пустая строка ничего не делает."""
        self.shell.execute("  ")
        self.assertTrue(self.shell.running)

    def test_errors(self):
        """Неверные команды и аргументы вызывают ошибку."""
        for line in ("unknown", "cd a b", "exit 1"):
            with self.subTest(line=line), self.assertRaises(ShellError):
                self.shell.execute(line)

    def test_exit_and_prompt(self):
        """В приглашении есть имя VFS; exit завершает цикл."""
        self.assertIn("demo", self.shell.prompt)
        self.shell.execute("exit")
        self.assertFalse(self.shell.running)
