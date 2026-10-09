"""Разбор команд и интерактивный цикл."""

from . import commands
from .errors import ShellError
from .vfs import VFS


class Shell:
    """CLI-оболочка над виртуальной файловой системой."""

    def __init__(self, name="demo"):
        """Создать пустую VFS и таблицу доступных команд."""
        self.vfs = VFS(name)
        self.cwd = "/"
        self.running = True
        self.commands = {
            "ls": commands.ls,
            "cd": commands.cd,
            "find": commands.find,
            "clear": commands.clear,
        }

    @property
    def prompt(self):
        """Вернуть имя VFS и текущий путь в приглашении."""
        return f"{self.vfs.name}:{self.cwd}$ "

    def execute(self, line):
        """Разделить ввод по пробелам и выполнить команду."""
        parts = line.split()
        if not parts:
            return
        command, *args = parts
        if command == "exit":
            if args:
                raise ShellError("exit: аргументы не поддерживаются")
            self.running = False
            return
        handler = self.commands.get(command)
        if handler is None:
            raise ShellError(f"неизвестная команда: {command}")
        handler(self, args)

    def repl(self):
        """Читать команды до exit или конца ввода."""
        while self.running:
            try:
                self.execute(input(self.prompt))
            except ShellError as error:
                print(f"Ошибка: {error}")
            except (EOFError, KeyboardInterrupt):
                print()
                break
