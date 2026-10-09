"""Точка входа в консольный эмулятор."""

from .shell import Shell


def main():
    """Запустить интерактивную оболочку."""
    Shell().repl()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
