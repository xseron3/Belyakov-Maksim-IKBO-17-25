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
        return tree.getroot()
    except (FileNotFoundError, ET.ParseError):
        return None


def get_current_dir(vfs_root, path_parts):
    """Возвращает элемент директории по списку частей пути."""
    current = vfs_root
    for part in path_parts:
        found = False
        for child in current:
            if child.tag == "dir" and child.get("name") == part:
                current = child
                found = True
                break
        if not found:
            return None
    return current


def resolve_path(current_parts, target):
    """Преобразует целевой путь в абсолютный список частей."""
    if not target:
        return current_parts
    if target == "/":
        return []

    if target.startswith("/"):
        parts = target[1:].split("/")
        result = []
    else:
        parts = target.split("/")
        result = list(current_parts)

    for part in parts:
        if part == "" or part == ".":
            continue
        elif part == "..":
            if result:
                result.pop()
        else:
            result.append(part)

    return result


def find_file_in_dir(dir_element, filename):
    """Ищет файл в директории и возвращает его элемент."""
    for child in dir_element:
        if child.tag == "file" and child.get("name") == filename:
            return child
    return None


def execute_command(cmd, args, widget, vfs_root, current_path_ref):
    """Выполняет команду с учётом VFS и продвинутых путей."""
    if cmd == "exit":
        sys.exit(0)

    elif cmd == "ls":
        target = args[0] if args else ""
        path_parts = resolve_path(current_path_ref[0], target)
        target_dir = get_current_dir(vfs_root, path_parts)

        if target_dir is None:
            append_output(widget, f"Ошибка: путь '{target or '/'}' не найден")
            return

        items = [child.get("name") for child in target_dir]
        append_output(widget, "  ".join(items) if items else "(пусто)")

    elif cmd == "cd":
        if not args:
            current_path_ref[0] = []
            return

        target = args[0]
        new_parts = resolve_path(current_path_ref[0], target)

        if not new_parts:
            current_path_ref[0] = []
            return

        target_dir = get_current_dir(vfs_root, new_parts)

        if target_dir is None or target_dir.tag != "dir":
            append_output(widget, f"Ошибка: директория '{target}' не найдена")
            return

        current_path_ref[0] = new_parts

    elif cmd == "cp":
        if len(args) < 2:
            append_output(widget, "Использование: cp <источник> <назначение>")
            return

        source = args[0]
        destination = args[1]

        # Разбираем путь к исходному файлу
        source_parts = resolve_path(current_path_ref[0], source)
        if not source_parts:
            append_output(widget, f"Ошибка: файл '{source}' не найден")
            return

        # Получаем имя файла и путь к родительской папке
        source_filename = source_parts[-1]
        source_parent_parts = source_parts[:-1]
        source_parent_dir = get_current_dir(vfs_root, source_parent_parts)

        if source_parent_dir is None:
            append_output(widget, f"Ошибка: путь '{source}' не найден")
            return

        # Ищем файл в родительской папке
        source_file = find_file_in_dir(source_parent_dir, source_filename)
        if source_file is None:
            append_output(widget, f"Ошибка: файл '{source}' не найден")
            return

        # Разбираем путь к назначению
        dest_parts = resolve_path(current_path_ref[0], destination)
        dest_dir = get_current_dir(vfs_root, dest_parts)

        if dest_dir is None or dest_dir.tag != "dir":
            append_output(widget, f"Ошибка: директория назначения '{destination}' не найдена")
            return

        # Создаём копию файла
        new_file = ET.SubElement(dest_dir, "file")
        new_file.set("name", source_filename)

        append_output(widget, f"Файл '{source}' скопирован в '{destination}'")

    else:
        append_output(widget, f"Ошибка: неизвестная команда '{cmd}'")


def process_input(user_input, widget, vfs_root, current_path_ref):
    """Разбирает ввод и запускает команду."""
    parts = user_input.strip().split()
    if not parts:
        return
    execute_command(parts[0], parts[1:], widget, vfs_root, current_path_ref)


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
    """Создаёт и запускает GUI эмулятора."""
    parser = argparse.ArgumentParser(description="Эмулятор терминала")
    parser.add_argument('--vfs', help='Путь к файлу виртуальной ФС')
    parser.add_argument('--script', help='Путь к стартовому скрипту')
    args = parser.parse_args()

    print(f"[DEBUG] Путь к VFS: {args.vfs}")
    print(f"[DEBUG] Путь к скрипту: {args.script}")

    vfs_root = load_vfs(args.vfs) if args.vfs else None
    if args.vfs and vfs_root is None:
        print(f"[ERROR] Не удалось загрузить VFS из '{args.vfs}'")

    current_path_ref = [[]]

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