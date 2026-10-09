"""Параметры запуска и загрузка стартового скрипта."""

import argparse
from pathlib import Path

from .errors import ShellError
from .shell import Shell
from .vfs import VFS


def parse_args(argv=None):
    """Прочитать пути к VFS и стартовому скрипту."""
    parser = argparse.ArgumentParser(description="Эмулятор, вариант 11")
    parser.add_argument("--vfs", default="examples/vfs/deep.json",
                        help="путь к JSON-файлу VFS")
    parser.add_argument("--script", help="путь к стартовому скрипту")
    return parser.parse_args(argv)


def run_script(shell, path):
    """Показать диалог; остановиться при первой ошибке."""
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise ShellError(f"не удалось прочитать скрипт: {error}") from error
    for number, line in enumerate(lines, start=1):
        if not shell.running:
            break
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        print(shell.prompt + line)
        try:
            shell.execute(line)
        except ShellError as error:
            raise ShellError(f"скрипт {path}, строка {number}: {error}")


def main(argv=None):
    """Напечатать настройки, выполнить скрипт и запустить REPL."""
    args = parse_args(argv)
    print(f"[config] vfs={args.vfs}")
    print(f"[config] script={args.script or '(не задан)'}")
    shell = Shell()
    try:
        shell.vfs = VFS.load(args.vfs)
        if args.script:
            run_script(shell, args.script)
    except ShellError as error:
        print(f"Ошибка: {error}")
        return 1
    shell.repl()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
