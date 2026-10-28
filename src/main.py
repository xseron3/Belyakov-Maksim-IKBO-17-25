import tkinter as tk
from tkinter import scrolledtext
import getpass
import socket
import sys


def get_window_title():
    """Возвращает заголовок окна из данных ОС."""
    username = getpass.getuser()
    hostname = socket.gethostname()
    return f"Эмулятор-[{username}@{hostname}]"


def append_output(widget, text):
    """Добавляет текст в область вывода."""
    widget.insert(tk.END, text + "\n")
    widget.see(tk.END)


def execute_command(cmd, args, widget):
    """Выполняет команду-заглушку или exit."""
    if cmd == "exit":
        sys.exit(0)
    if cmd == "ls":
        append_output(widget, f"ls: аргументы {args}")
    elif cmd == "cd":
        append_output(widget, f"cd: аргументы {args}")
    else:
        append_output(widget, f"Ошибка: неизвестная команда '{cmd}'")


def process_input(user_input, widget):
    """Разбирает ввод и запускает команду."""
    parts = user_input.strip().split()
    if not parts:
        return
    command = parts[0]
    arguments = parts[1:]
    execute_command(command, arguments, widget)


def on_enter_pressed(event, entry, widget):
    """Обработчик нажатия Enter в поле ввода."""
    user_input = entry.get()
    append_output(widget, f"> {user_input}")
    process_input(user_input, widget)
    entry.delete(0, tk.END)


def main():
    """Создаёт и запускает GUI эмулятора."""
    root = tk.Tk()
    root.title(get_window_title())
    root.geometry("600x400")

    output = scrolledtext.ScrolledText(root, wrap=tk.WORD)
    output.pack(expand=True, fill="both", padx=5, pady=5)

    entry = tk.Entry(root)
    entry.pack(fill="x", padx=5, pady=5)
    entry.focus()

    entry.bind(
        "<Return>",
        lambda event: on_enter_pressed(event, entry, output)
    )

    root.mainloop()


if __name__ == "__main__":
    main()