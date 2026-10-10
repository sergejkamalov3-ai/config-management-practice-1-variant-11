"""Загрузка JSON-файловой системы в оперативную память."""

import base64
import binascii
import json
import posixpath
import re
from dataclasses import dataclass
from pathlib import Path

from .errors import ShellError

DEFAULT_DIR_MODE = 0o755
FIRST_PRINTABLE_CODEPOINT = 32


@dataclass
class Node:
    """Файл или каталог VFS: тип, права и байтовое содержимое."""

    kind: str
    mode: int
    data: bytes = b""


class VFS:
    """Дерево узлов; обращения к исходному файлу только при загрузке."""

    def __init__(self, name, nodes=None):
        """Создать дерево с корневым каталогом."""
        self.name = name
        self.nodes = nodes if nodes is not None else {
            "/": Node("dir", DEFAULT_DIR_MODE)
        }

    @classmethod
    def load(cls, filename):
        """Прочитать JSON и проверить формат до установки новой VFS."""
        try:
            text = Path(filename).read_text(encoding="utf-8")
            payload = json.loads(text)
        except (OSError, UnicodeError, ValueError) as error:
            raise ShellError(f"ошибка загрузки VFS: {error}") from error
        cls.validate_header(payload)
        vfs = cls(payload["name"])
        seen = set()
        for entry in payload["entries"]:
            path, node = cls.decode_entry(entry)
            if path in seen:
                raise ShellError(f"VFS: повторный путь {path}")
            seen.add(path)
            vfs.nodes[path] = node
        vfs.validate_tree()
        return vfs

    @staticmethod
    def validate_header(payload):
        """Проверить имя VFS и список узлов."""
        if not isinstance(payload, dict):
            raise ShellError("VFS: корень JSON должен быть объектом")
        name = payload.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ShellError("VFS: требуется непустое имя name")
        if any(ord(char) < FIRST_PRINTABLE_CODEPOINT for char in name):
            raise ShellError("VFS: управляющие символы в имени")
        if not isinstance(payload.get("entries"), list):
            raise ShellError("VFS: entries должен быть списком")

    @staticmethod
    def validate_path(path):
        """В JSON допустимы только канонические абсолютные пути."""
        if not isinstance(path, str) or not path.startswith("/"):
            raise ShellError("VFS: требуется абсолютный путь")
        parts = path.split("/")[1:]
        if path != "/" and any(p in ("", ".", "..") for p in parts):
            raise ShellError(f"VFS: некорректный путь {path}")
        if any(char.isspace() or ord(char) < FIRST_PRINTABLE_CODEPOINT
               for char in path):
            raise ShellError("VFS: пробелы/управляющие символы в пути")

    @staticmethod
    def parse_mode(value):
        """Преобразовать три восьмеричные цифры в битовую маску."""
        if not isinstance(value, str) or not re.fullmatch(r"[0-7]{3}", value):
            raise ShellError("права должны содержать 3 цифры от 0 до 7")
        return int(value, 8)

    @classmethod
    def decode_entry(cls, entry):
        """Проверить узел JSON и декодировать данные из base64."""
        if not isinstance(entry, dict):
            raise ShellError("VFS: каждый узел должен быть объектом")
        path = entry.get("path")
        cls.validate_path(path)
        kind = entry.get("type")
        if kind not in ("dir", "file"):
            raise ShellError(f"VFS: неизвестный тип узла {path}")
        default = "755" if kind == "dir" else "644"
        mode = cls.parse_mode(entry.get("mode", default))
        if kind == "dir":
            if "data" in entry:
                raise ShellError("VFS: каталог не может содержать data")
            return path, Node(kind, mode)
        if entry.get("encoding") != "base64":
            raise ShellError("VFS: для файла требуется encoding=base64")
        try:
            data = base64.b64decode(entry["data"], validate=True)
        except (KeyError, TypeError, ValueError, binascii.Error) as error:
            raise ShellError(f"VFS: неверные данные base64 {path}") from error
        return path, Node(kind, mode, data)

    def validate_tree(self):
        """Проверить корень и существование родителей-каталогов."""
        if self.nodes["/"].kind != "dir":
            raise ShellError("VFS: корень должен быть каталогом")
        for path in self.nodes:
            if path == "/":
                continue
            parent = posixpath.dirname(path)
            node = self.nodes.get(parent)
            if node is None or node.kind != "dir":
                raise ShellError(f"VFS: нет родительского каталога {parent}")

    @staticmethod
    def normalize(path, cwd="/"):
        """Разрешить относительные пути, точку и переходы к родителю."""
        combined = path if path.startswith("/") else cwd + "/" + path
        stack = []
        for part in combined.split("/"):
            if part in ("", "."):
                continue
            if part == "..":
                if stack:
                    stack.pop()
            else:
                stack.append(part)
        return "/" + "/".join(stack)

    def get(self, path):
        """Найти узел или сообщить об отсутствующем пути."""
        try:
            return self.nodes[path]
        except KeyError as error:
            message = f"нет такого файла или каталога: {path}"
            raise ShellError(message) from error

    def require(self, path, bits):
        """Проверить биты владельца: эмулятор работает как владелец."""
        node = self.get(path)
        if (node.mode & bits) != bits:
            raise ShellError(f"доступ запрещен: {path}")

    def directory(self, path):
        """Проверить, что узел является каталогом."""
        if self.get(path).kind != "dir":
            raise ShellError(f"не является каталогом: {path}")

    def resolve(self, path, cwd="/"):
        """Обойти каждый компонент, проверяя существование и право x."""
        current = "/" if path.startswith("/") else cwd
        for part in path.split("/"):
            if not part:
                continue
            self.directory(current)
            self.require(current, 0o100)
            if part == ".":
                continue
            if part == "..":
                current = posixpath.dirname(current) or "/"
            else:
                current = self.normalize(part, current)
                self.get(current)
        if path.endswith("/"):
            self.directory(current)
        return current

    def children(self, path):
        """Вернуть отсортированные непосредственные дочерние пути."""
        self.directory(path)
        self.require(path, 0o500)
        return sorted(p for p in self.nodes if p != "/"
                      and posixpath.dirname(p) == path)

    def walk(self, path):
        """Обойти дерево итеративно без зависимости от глубины рекурсии."""
        pending = [path]
        while pending:
            current = pending.pop()
            yield current
            if self.get(current).kind == "dir":
                pending.extend(reversed(self.children(current)))

    def mkdir(self, path, cwd="/", parents=False):
        """Создать каталог; -p создает недостающих родителей в памяти."""
        current = "/" if path.startswith("/") else cwd
        parts = [part for part in path.split("/") if part]
        if not parts and not parents:
            raise ShellError(f"mkdir: каталог уже существует: {current}")
        for index, part in enumerate(parts):
            self.directory(current)
            self.require(current, 0o100)
            candidate = self.normalize(part, current)
            last = index == len(parts) - 1
            self.mkdir_component(current, candidate, last, parents)
            current = candidate

    def mkdir_component(self, parent, candidate, last, parents):
        """Проверить существующий компонент или создать недостающий каталог."""
        if candidate in self.nodes:
            self.directory(candidate)
            if last and not parents:
                raise ShellError(f"mkdir: уже существует: {candidate}")
            return
        if not last and not parents:
            raise ShellError(f"mkdir: нет родителя: {candidate}")
        self.require(parent, 0o300)
        self.nodes[candidate] = Node("dir", DEFAULT_DIR_MODE)
