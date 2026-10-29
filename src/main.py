import tkinter as tk
from tkinter import scrolledtext
import getpass
import socket
import sys
import argparse
import xml.etree.ElementTree as ET


def get_window_title():
    """Возвращает заголовок окна из данных ОС."""
    username = getpass.getuser()
    hostname = socket.gethostname()
    return f"Эмулятор-[{username}@{hostname}]"


def append_output(widget, text):
    """Добавляет текст в область вывода."""
    widget.insert(tk.END, text + "\n")
    widget.see(tk.END)


def load_vfs(vfs_path):
    """Загружает виртуальную файловую систему из XML-файла."""
    try:
        tree = ET.parse(vfs_path)
        root = tree.getroot()
        return root
    except FileNotFoundError:
        return None
    except ET.ParseError:
        return None


def get_current_dir(vfs_root, current_path):
    """Возвращает элемент текущей директории по пути."""
    if not current_path:
        return vfs_root
    parts = current_path.strip("/").split("/")
    current = vfs_root
    for part in parts:
        found = False
        for child in current:
            if child.tag == "dir" and child.get("name") == part:
                current = child
                found = True
                break
        if not found:
            return None
    return current


def execute_command(cmd, args, widget, vfs_root, current_path_ref):
    """Выполняет команду с учётом VFS."""
    if cmd == "exit":
        sys.exit(0)
    if cmd == "ls":
        current_dir = get_current_dir(vfs_root, current_path_ref[0])
        if current_dir is None:
            append_output(widget, "Ошибка: директория не найдена")
            return
        items = []
        for child in current_dir:
            items.append(child.get("name"))
        if items:
            append_output(widget, "  ".join(items))
        else:
            append_output(widget, "(пусто)")
    elif cmd == "cd":
        if not args:
            current_path_ref[0] = ""
            return
        target = args[0]
        if target == "..":
            parts = current_path_ref[0].strip("/").split("/")
            if len(parts) > 1:
                current_path_ref[0] = "/".join(parts[:-1])
            else:
                current_path_ref[0] = ""
            return
        current_dir = get_current_dir(vfs_root, current_path_ref[0])
        if current_dir is None:
            append_output(widget, "Ошибка: директория не найдена")
            return
        found = False
        for child in current_dir:
            if child.tag == "dir" and child.get("name") == target:
                if current_path_ref[0]:
                    current_path_ref[0] = current_path_ref[0] + "/" + target
                else:
                    current_path_ref[0] = target
                found = True
                break
        if not found:
            append_output(widget, f"Ошибка: директория '{target}' не найдена")
    else:
        append_output(widget, f"Ошибка: неизвестная команда '{cmd}'")


def process_input(user_input, widget, vfs_root, current_path_ref):
    """Разбирает ввод и запускает команду."""
    parts = user_input.strip().split()
    if not parts:
        return
    command = parts[0]
    arguments = parts[1:]
    execute_command(command, arguments, widget, vfs_root, current_path_ref)


def run_startup_script(script_path, widget, vfs_root, current_path_ref):
    """Читает и выполняет команды из стартового скрипта."""
    append_output(widget, f"--- Запуск скрипта: {script_path} ---")
    try:
        with open(script_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                append_output(widget, f"> {line}")
                process_input(line, widget, vfs_root, current_path_ref)
        append_output(widget, "--- Скрипт завершен ---")
    except FileNotFoundError:
        append_output(widget, f"Ошибка: файл скрипта '{script_path}' не найден.")
    except Exception as error:
        append_output(widget, f"Ошибка при чтении скрипта: {error}")


def main():
    """Создаёт и запускает GUI эмулятора с поддержкой аргументов."""
    parser = argparse.ArgumentParser(description="Эмулятор терминала")
    parser.add_argument('--vfs', help='Путь к файлу виртуальной ФС')
    parser.add_argument('--script', help='Путь к стартовому скрипту')
    args = parser.parse_args()

    print(f"[DEBUG] Путь к VFS: {args.vfs}")
    print(f"[DEBUG] Путь к скрипту: {args.script}")

    vfs_root = None
    if args.vfs:
        vfs_root = load_vfs(args.vfs)
        if vfs_root is None:
            print(f"[ERROR] Не удалось загрузить VFS из '{args.vfs}'")

    current_path_ref = [""]

    root = tk.Tk()
    root.title(get_window_title())
    root.geometry("600x500")

    output = scrolledtext.ScrolledText(root, wrap=tk.WORD)
    output.pack(expand=True, fill="both", padx=5, pady=5)

    entry = tk.Entry(root, font=("Arial", 12))
    entry.pack(fill="x", padx=5, pady=(0, 10))
    entry.focus()

    def on_enter_pressed(event):
        user_input = entry.get()
        append_output(output, f"> {user_input}")
        process_input(user_input, output, vfs_root, current_path_ref)
        entry.delete(0, tk.END)

    entry.bind("<Return>", on_enter_pressed)

    if args.script:
        run_startup_script(args.script, output, vfs_root, current_path_ref)

    root.mainloop()


if __name__ == "__main__":
    main()