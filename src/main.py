import tkinter as tk
from tkinter import scrolledtext
import getpass
import socket
import sys
import argparse


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


def run_startup_script(script_path, widget):
    """Читает и выполняет команды из стартового скрипта."""
    append_output(widget, f"--- Запуск скрипта: {script_path} ---")
    try:
        with open(script_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                # Пропускаем пустые строки и комментарии
                if not line or line.startswith('#'):
                    continue

                append_output(widget, f"> {line}")
                process_input(line, widget)
        append_output(widget, "--- Скрипт завершен ---")
    except FileNotFoundError:
        append_output(widget, f"Ошибка: файл скрипта '{script_path}' не найден.")
    except Exception as error:
        append_output(widget, f"Ошибка при чтении скрипта: {error}")


def main():
    """Создаёт и запускает GUI эмулятора с поддержкой аргументов."""
    # 1. Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description="Эмулятор терминала")
    parser.add_argument('--vfs', help='Путь к файлу виртуальной ФС')
    parser.add_argument('--script', help='Путь к стартовому скрипту')
    args = parser.parse_args()

    # 2. Отладочный вывод параметров (виден в консоли PyCharm)
    print(f"[DEBUG] Путь к VFS: {args.vfs}")
    print(f"[DEBUG] Путь к скрипту: {args.script}")

    # 3. Создание графического интерфейса
    root = tk.Tk()
    root.title(get_window_title())
    root.geometry("600x400")

    output = scrolledtext.ScrolledText(root, wrap=tk.WORD)
    output.pack(expand=True, fill="both", padx=5, pady=5)

    entry = tk.Entry(root)
    entry.pack(fill="x", padx=5, pady=5)
    entry.focus()

    def on_enter_pressed(event):
        user_input = entry.get()
        append_output(output, f"> {user_input}")
        process_input(user_input, output)
        entry.delete(0, tk.END)

    entry.bind("<Return>", on_enter_pressed)

    # 4. Если передан скрипт, выполняем его перед запуском цикла
    if args.script:
        run_startup_script(args.script, output)

    root.mainloop()


if __name__ == "__main__":
    main()