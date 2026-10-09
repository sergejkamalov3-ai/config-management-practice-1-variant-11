"""Разбор команд и интерактивный цикл."""

from .errors import ShellError


class Shell:
    """Минимальная оболочка с командами-заглушками."""

    def __init__(self, name="demo"):
        """Задать имя виртуальной файловой системы."""
        self.name = name
        self.running = True

    @property
    def prompt(self):
        """Вернуть приглашение ко вводу."""
        return f"{self.name}:/$ "

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
        elif command in ("ls", "cd"):
            if len(args) > 1:
                raise ShellError(f"{command}: слишком много аргументов")
            print(f"{command}: {args}")
        else:
            raise ShellError(f"неизвестная команда: {command}")

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
