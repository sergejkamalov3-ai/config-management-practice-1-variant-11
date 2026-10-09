"""Проверки формата JSON, двоичных данных и дерева VFS."""

import json
import tempfile
import unittest
from pathlib import Path

from src.errors import ShellError
from src.vfs import VFS


class VFSTests(unittest.TestCase):
    """Проверить корректные и поврежденные образы."""

    def load_payload(self, payload):
        """Загрузить JSON из временного файла."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "vfs.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return VFS.load(path)

    def test_fixtures(self):
        """Все три образа загружаются; base64 сохраняет байты."""
        for name in ("minimal", "files", "deep"):
            vfs = VFS.load(f"examples/vfs/{name}.json")
            self.assertEqual(vfs.name, name)
        files = VFS.load("examples/vfs/files.json")
        self.assertEqual(files.get("/data.bin").data, b"\x00\x01\x02\xff")

    def test_bad_tree(self):
        """Нельзя иметь узлы без родителя или повторять пути."""
        entry = {"path": "/absent/child", "type": "dir"}
        cases = [[entry], [entry, entry],
                 [{"path": "/a/../b", "type": "dir"}]]
        for entries in cases:
            with self.subTest(entries=entries), self.assertRaises(ShellError):
                self.load_payload({"name": "bad", "entries": entries})

    def test_bad_data_and_mode(self):
        """Неверные base64 и права отклоняются."""
        entry = {"path": "/a", "type": "file", "encoding": "base64",
                 "data": "%%%"}
        with self.assertRaises(ShellError):
            self.load_payload({"name": "bad", "entries": [entry]})
        with self.assertRaises(ShellError):
            VFS.parse_mode("888")

    def test_missing_file_and_bad_header(self):
        """Проверить ошибку чтения и обязательные поля."""
        with self.assertRaises(ShellError):
            VFS.load("not-found.json")
        for payload in ([], {}, {"name": "a", "entries": 1}):
            with self.subTest(payload=payload), self.assertRaises(ShellError):
                self.load_payload(payload)

    def test_path_normalization(self):
        """Родитель корня остается корнем."""
        self.assertEqual(VFS.normalize("../../..", "/home"), "/")
        self.assertEqual(VFS.normalize("./docs/../x", "/home"), "/home/x")
