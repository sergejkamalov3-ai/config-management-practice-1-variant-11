"""Изменения VFS, права доступа и повторная загрузка."""

import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from src.errors import ShellError
from src.shell import Shell
from src.vfs import VFS


class ExtraTests(unittest.TestCase):
    """Проверить мутации в памяти и сохранность JSON на диске."""

    def set_up(self):
        """Запомнить исходные байты и загрузить образ."""
        self.path = Path("examples/vfs/deep.json")
        self.before = self.path.read_bytes()
        self.shell = Shell()
        self.shell.vfs = VFS.load(self.path)

    def test_mkdir(self):
        """Обычный и рекурсивный режимы создают каталоги."""
        self.set_up()
        self.shell.execute("mkdir /a /b")
        self.shell.execute("mkdir -p /a/one/two/three")
        self.shell.execute("mkdir -p /a/one/two/three")
        self.shell.execute("cd /a")
        self.shell.execute("mkdir local")
        self.assertIn("/a/one/two/three", self.shell.vfs.nodes)
        self.assertIn("/a/local", self.shell.vfs.nodes)
        self.assertEqual(self.shell.vfs.get("/a/local").mode, 0o755)

    def test_chmod(self):
        """Изменение прав работает для файлов, каталогов и поддерева."""
        self.set_up()
        self.shell.execute("chmod 600 /welcome.txt /empty")
        self.assertEqual(self.shell.vfs.get("/welcome.txt").mode, 0o600)
        self.shell.execute("chmod -R 700 /home")
        for path in self.shell.vfs.walk("/home"):
            self.assertEqual(self.shell.vfs.get(path).mode, 0o700)

    def test_permissions_after_chmod(self):
        """Запрет прав проявляется в командах, владелец может их вернуть."""
        self.set_up()
        self.shell.execute("chmod 000 /empty")
        for line in ("cd /empty", "ls /empty", "mkdir /empty/x"):
            with self.subTest(line=line), self.assertRaises(ShellError):
                self.shell.execute(line)
        self.shell.execute("chmod 755 /empty")
        self.shell.execute("mkdir /empty/x")

    def test_disk_unchanged(self):
        """Ни mkdir, ни chmod не записывают JSON."""
        self.set_up()
        self.shell.execute("mkdir -p /new/a/b")
        self.shell.execute("chmod -R 700 /home")
        self.assertEqual(self.path.read_bytes(), self.before)
        fresh = VFS.load(self.path)
        self.assertNotIn("/new", fresh.nodes)
        self.assertEqual(fresh.get("/home").mode, 0o755)

    def test_reload(self):
        """vfs-load меняет имя, дерево и текущий каталог."""
        self.set_up()
        self.shell.execute("mkdir /new")
        self.shell.execute("cd /home")
        self.shell.execute("vfs-load examples/vfs/files.json")
        self.assertEqual(self.shell.prompt, "files:/$ ")
        self.assertIn("/data.bin", self.shell.vfs.nodes)
        self.assertNotIn("/new", self.shell.vfs.nodes)

    def test_failed_reload_preserves_state(self):
        """Ошибка загрузки оставляет прежнюю VFS и cwd."""
        self.set_up()
        self.shell.execute("cd /home")
        original = self.shell.vfs
        with self.assertRaises(ShellError):
            self.shell.execute("vfs-load examples/vfs/invalid.json")
        self.assertIs(self.shell.vfs, original)
        self.assertEqual(self.shell.cwd, "/home")

    def test_bad_arguments(self):
        """Ошибочные формы дополнительных команд отклоняются."""
        self.set_up()
        for line in ("mkdir", "mkdir -z /a", "mkdir /home",
                     "mkdir /missing/a", "mkdir -p /welcome.txt/a",
                     "chmod 888 /home", "chmod 700", "chmod 700 /bad",
                     "vfs-load", "vfs-load a b"):
            with self.subTest(line=line), self.assertRaises(ShellError):
                self.shell.execute(line)
