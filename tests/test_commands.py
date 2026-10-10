"""Проверки команд ls, cd, find и clear."""

import io
import unittest
from contextlib import redirect_stdout

from src.errors import ShellError
from src.shell import Shell
from src.vfs import VFS


class CommandTests(unittest.TestCase):
    """Проверить вывод, переходы и неверные аргументы."""

    def set_up(self):
        """Загрузить многоуровневую VFS."""
        self.shell = Shell()
        self.shell.vfs = VFS.load("examples/vfs/deep.json")

    def output(self, line):
        """Выполнить команду с перехватом stdout."""
        stream = io.StringIO()
        with redirect_stdout(stream):
            self.shell.execute(line)
        return stream.getvalue()

    def test_ls(self):
        """Скрытые имена и права зависят от флагов."""
        self.set_up()
        self.assertNotIn(".hidden", self.output("ls"))
        self.assertIn(".hidden", self.output("ls -a"))
        self.assertIn("drwxr-xr-x", self.output("ls -l"))
        self.assertIn("-rw-r--r--", self.output("ls -l /welcome.txt"))
        self.assertEqual(self.output("ls /empty"), "")

    def test_cd(self):
        """Абсолютные и относительные переходы меняют приглашение."""
        self.set_up()
        for line in ("cd /home/student", "cd ./docs", "cd .."):
            self.shell.execute(line)
        self.assertIn("deep:/home/student$", self.shell.prompt)
        self.shell.execute("cd ../../..")
        self.assertEqual(self.shell.cwd, "/")
        self.shell.execute("cd")
        self.assertEqual(self.shell.cwd, "/")

    def test_find(self):
        """Фильтры имени и типа применяются одновременно."""
        self.set_up()
        text = self.output("find /home -name *.txt -type f")
        self.assertEqual(text.splitlines(), [
            "/home/student/docs/readme.txt", "/home/student/notes.txt"])
        self.assertIn("/home/student/docs", self.output("find / -type d"))
        self.assertIn("./home", self.output("find"))

    def test_clear(self):
        """Clear выводит точную ANSI-последовательность."""
        self.set_up()
        self.assertEqual(self.output("clear"), "\033[2J\033[H")

    def test_errors(self):
        """Ошибки команды не меняют текущий каталог."""
        self.set_up()
        for line in ("ls -z", "cd /welcome.txt", "cd a b",
                     "find / -type z", "find / -name", "clear x",
                     "ls /missing", "cd /welcome.txt/.."):
            with self.subTest(line=line), self.assertRaises(ShellError):
                self.shell.execute(line)
        self.assertEqual(self.shell.cwd, "/")

    def test_permissions(self):
        """Вход требует x, перечисление требует r и x."""
        self.set_up()
        self.shell.vfs.get("/home").mode = 0o000
        for line in ("cd /home", "ls /home", "find /home"):
            with self.subTest(line=line), self.assertRaises(ShellError):
                self.output(line)
