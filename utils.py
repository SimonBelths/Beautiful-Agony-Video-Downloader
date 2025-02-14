import os
import json
import webbrowser
import tkinter as tk
import requests
from bs4 import BeautifulSoup
import time
import datetime
import ctypes
from email.utils import parsedate_to_datetime
from mutagen.mp4 import MP4

# ======================= Функции работы с конфигурацией =======================
CONFIG_FILE = "config.json"

def load_config():
    """Загружает настройки из файла config.json."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config
        except Exception as e:
            print(f"Ошибка загрузки конфигурации: {e}")
    return {}

def save_config(config):
    """Сохраняет настройки в файл config.json."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка сохранения конфигурации: {e}")

# ======================= Константы и пути к файлам =======================
DOWNLOAD_FOLDER = r"S:\Test"
cookies_path = "cookies.pkl"
log_file_path = "logs.txt"
failed_links_path = "failed_links.txt"

# Если лог-файл существует, очищаем его
if os.path.exists(log_file_path):
    with open(log_file_path, "w", encoding="utf-8") as f:
        f.write("")

# Виджеты для логирования (будут заданы из GUI)
log_text = None
show_only_pages_and_errors = None

# ======================= Функции логирования =======================
def set_log_widgets(text_widget, checkbox_var):
    global log_text, show_only_pages_and_errors
    log_text = text_widget
    show_only_pages_and_errors = checkbox_var

def write_log(message, log_type="info"):
    from datetime import datetime
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"{log_entry}\n")
    if show_only_pages_and_errors is not None and show_only_pages_and_errors.get():
        if log_type not in ["page", "error"]:
            return
    if log_text is not None:
        log_text.insert(tk.END, f"{log_entry}\n")
        log_text.see(tk.END)

def save_failed_link(link):
    with open(failed_links_path, "a", encoding="utf-8") as failed_file:
        failed_file.write(f"{link}\n")

def open_log_file():
    if os.path.exists(log_file_path):
        webbrowser.open(log_file_path)
    else:
        from tkinter import messagebox
        messagebox.showerror("Ошибка", "Файл с логами не найден!")

def open_failed_links_file():
    if os.path.exists(failed_links_path):
        webbrowser.open(failed_links_path)
    else:
        from tkinter import messagebox
        messagebox.showerror("Ошибка", "Файл с ошибками не найден!")

# ======================= Функции для работы с папкой загрузки =======================
def select_download_folder(download_folder_var):
    from tkinter import filedialog, messagebox
    folder = filedialog.askdirectory(initialdir=DOWNLOAD_FOLDER)
    if folder:
        download_folder_var.set(folder)
        # Загружаем текущую конфигурацию, обновляем путь и сохраняем
        config = load_config()
        config["download_folder"] = folder
        save_config(config)
        messagebox.showinfo("Папка загрузок", f"Выбрана папка: {folder}")

# ======================= Функции для работы с чёрным списком =======================
def create_blacklist_for_mode(mode):
    base_url = "https://beautifulagony.com/public/main.php?page=view&mode={}&offset={}"
    blacklist = set()
    page = 0
    while True:
        offset = page * 20
        url = base_url.format(mode, offset)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                elements = soup.find_all("font", class_="agonyid")
                page_numbers = set()
                for el in elements:
                    text = el.get_text(strip=True)
                    if text.startswith("#"):
                        num = text[1:]
                        if num.isdigit() and len(num) == 4:
                            page_numbers.add(num)
                if not page_numbers:
                    print(f"Режим {mode}: страница с offset={offset} не содержит номеров. Завершаем перебор.")
                    break
                print(f"Режим {mode}: найдено {len(page_numbers)} номеров на странице с offset={offset}.")
                blacklist.update(page_numbers)
                page += 1
            else:
                print(f"Не удалось загрузить страницу: {url}. Статус: {response.status_code}")
                break
        except Exception as e:
            print(f"Ошибка при обработке {url}: {e}")
            break
    return blacklist

def create_blacklist_from_pages(modes=["males", "transgender"], output_file="blacklist.txt"):
    total_blacklist = set()
    for mode in modes:
        print(f"Начало парсинга для режима: {mode}")
        mode_blacklist = create_blacklist_for_mode(mode)
        print(f"Режим {mode}: найдено {len(mode_blacklist)} номеров.")
        total_blacklist.update(mode_blacklist)
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for num in sorted(total_blacklist):
                f.write(num + "\n")
        print(f"Черный список создан, найдено всего {len(total_blacklist)} номеров. Файл: {output_file}")
    except Exception as e:
        print(f"Ошибка при записи файла черного списка: {e}")
    return total_blacklist

def load_blacklist(filename="blacklist.txt"):
    blacklist = set()
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                num = line.strip()
                if num:
                    blacklist.add(num)
    except Exception as e:
        print(f"Ошибка при загрузке файла черного списка: {e}")
    return blacklist

def open_blacklist_file():
    if os.path.exists("blacklist.txt"):
        webbrowser.open("blacklist.txt")
    else:
        from tkinter import messagebox
        messagebox.showerror("Ошибка", "Файл черного списка не найден!")

# ======================= Функции для работы с датами и метаданными =======================
def parse_release_date(date_text):
    from datetime import datetime
    try:
        dt = datetime.strptime(date_text, "%d %b %Y - %H:%M")
        return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
    except Exception as e:
        print(f"Ошибка парсинга даты: {e}")
        return None

def get_media_created(file_path):
    timestamp = os.path.getctime(file_path)
    return time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(timestamp))

def get_data_modified(file_path):
    timestamp = os.path.getmtime(file_path)
    return time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(timestamp))

def set_media_created(file_path, remote_date_str):
    try:
        remote_dt = parsedate_to_datetime(remote_date_str)
    except Exception as e:
        print(f"Ошибка при разборе даты: {e}")
        return False
    timestamp = remote_dt.timestamp()
    os.utime(file_path, (timestamp, timestamp))
    if os.name == 'nt':
        FILE_WRITE_ATTRIBUTES = 0x100
        handle = ctypes.windll.kernel32.CreateFileW(file_path, FILE_WRITE_ATTRIBUTES, 0, None, 3, 0x80, None)
        if handle == -1:
            print("Не удалось открыть файл для изменения даты создания.")
            return False
        win_time = int((timestamp + 11644473600) * 10000000)
        ctime = ctypes.c_longlong(win_time)
        res = ctypes.windll.kernel32.SetFileTime(handle, ctypes.byref(ctime), None, None)
        ctypes.windll.kernel32.CloseHandle(handle)
        return res
    return True

def set_file_title(file_path, title):
    """
    Устанавливает значение тега Title (©nam) для MP4-файла с помощью mutagen.
    """
    try:
        video = MP4(file_path)
        video["©nam"] = [title]
        video.save()
        print(f"Title установлен: {title}")
        return True
    except Exception as e:
        print(f"Ошибка при установке Title для {file_path}: {e}")
        return False

def set_video_id(file_path, person_id):
    return set_file_title(file_path, person_id)

def sizes_match(actual, expected, tolerance_percent=0.003):
    """
    Возвращает True, если относительная разница между actual и expected не превышает tolerance_percent.
    Выводит отладочную информацию.
    """
    diff = abs(actual - expected)
    allowed = tolerance_percent * expected
    print(f"[DEBUG] Сравнение размеров: actual = {actual}, expected = {expected}, diff = {diff}, allowed = {allowed}")
    return diff <= allowed
