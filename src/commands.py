"""Реализация основных команд оболочки."""

import fnmatch
import posixpath

from .errors import ShellError

MIN_CHMOD_ARGUMENTS = 2


def parse_ls(args):
    """Выделить флаги -a, -l и список путей."""
    flags, paths = set(), []
    options = True
    for arg in args:
        if options and arg == "--":
            options = False
        elif options and arg.startswith("-"):
            if arg == "-" or any(char not in "al" for char in arg[1:]):
                raise ShellError(f"ls: неизвестный флаг {arg}")
            flags.update(arg[1:])
        else:
            paths.append(arg)
    return flags, paths or ["."]


def mode_string(node):
    """Показать тип и девять букв прав доступа."""
    symbols = "rwxrwxrwx"
    rights = "".join(symbol if node.mode & (1 << (8 - index)) else "-"
                     for index, symbol in enumerate(symbols))
    return ("d" if node.kind == "dir" else "-") + rights


def show_entry(vfs, path, name, detailed):
    """Напечатать имя или информацию о типе, правах и размере."""
    node = vfs.get(path)
    if detailed:
        print(f"{mode_string(node)} {len(node.data):>6} {name}")
    else:
        print(name)


def ls(shell, args):
    """Вывести файлы; -a включает скрытые, -l показывает права."""
    flags, paths = parse_ls(args)
    for index, original in enumerate(paths):
        path = shell.vfs.resolve(original, shell.cwd)
        if len(paths) > 1:
            if index:
                print()
            print(f"{original}:")
        if shell.vfs.get(path).kind == "file":
            show_entry(shell.vfs, path, original, "l" in flags)
            continue
        if "a" in flags:
            show_entry(shell.vfs, path, ".", "l" in flags)
            parent = posixpath.dirname(path) or "/"
            show_entry(shell.vfs, parent, "..", "l" in flags)
        for child in shell.vfs.children(path):
            name = posixpath.basename(child)
            if "a" in flags or not name.startswith("."):
                show_entry(shell.vfs, child, name, "l" in flags)


def cd(shell, args):
    """Перейти в каталог; без аргумента перейти в корень."""
    if len(args) > 1:
        raise ShellError("cd: слишком много аргументов")
    path = shell.vfs.resolve(args[0] if args else "/", shell.cwd)
    shell.vfs.directory(path)
    shell.vfs.require(path, 0o100)
    shell.cwd = path


def parse_find(args):
    """Прочитать стартовый путь и фильтры -name, -type."""
    values = list(args)
    start = values.pop(0) if values and not values[0].startswith("-") else "."
    filters = {}
    while values:
        key = values.pop(0)
        if key not in ("-name", "-type") or not values:
            raise ShellError("find: ожидается [-name шаблон] [-type f|d]")
        if key in filters:
            raise ShellError(f"find: повторный фильтр {key}")
        filters[key] = values.pop(0)
    if "-type" in filters and filters["-type"] not in ("f", "d"):
        raise ShellError("find: тип должен быть f или d")
    return start, filters


def find(shell, args):
    """Найти узлы рекурсивно по имени и типу."""
    start, filters = parse_find(args)
    root = shell.vfs.resolve(start, shell.cwd)
    for path in shell.vfs.walk(root):
        name = posixpath.basename(path) or "/"
        pattern = filters.get("-name", "*")
        kind = shell.vfs.get(path).kind
        node_type = "d" if kind == "dir" else "f"
        if not fnmatch.fnmatchcase(name, pattern):
            continue
        if filters.get("-type", node_type) != node_type:
            continue
        suffix = posixpath.relpath(path, root)
        display = start if suffix == "." else posixpath.join(start, suffix)
        print(display)


def clear(shell, args):
    """Очистить ANSI-терминал и поставить курсор в начало."""
    if args:
        raise ShellError("clear: аргументы не поддерживаются")
    print("\033[2J\033[H", end="", flush=True)


def mkdir(shell, args):
    """Создать один или несколько каталогов, включая режим -p."""
    values = list(args)
    parents = bool(values and values[0] == "-p")
    if parents:
        values.pop(0)
    if values and values[0] == "--":
        values.pop(0)
    if not values or any(path.startswith("-") for path in values):
        raise ShellError("mkdir: ожидается [-p] путь [путь ...]")
    for path in values:
        shell.vfs.mkdir(path, shell.cwd, parents)


def chmod(shell, args):
    """Изменить числовые права владельца, группы и остальных; -R."""
    values = list(args)
    recursive = bool(values and values[0] == "-R")
    if recursive:
        values.pop(0)
    if len(values) < MIN_CHMOD_ARGUMENTS:
        raise ShellError("chmod: ожидается [-R] режим путь [путь ...]")
    mode = shell.vfs.parse_mode(values.pop(0))
    targets = set()
    for original in values:
        path = shell.vfs.resolve(original, shell.cwd)
        targets.update(shell.vfs.walk(path) if recursive else [path])
    for path in targets:
        shell.vfs.get(path).mode = mode


def vfs_load(shell, args):
    """Загрузить новый физический JSON, затем сбросить cwd в корень."""
    if len(args) != 1:
        raise ShellError("vfs-load: требуется один путь к JSON-файлу")
    new_vfs = shell.vfs.load(args[0])
    shell.vfs = new_vfs
    shell.cwd = "/"
