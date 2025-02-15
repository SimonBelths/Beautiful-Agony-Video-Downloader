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
import subprocess

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
    """
    Устанавливает время создания/модификации файла согласно remote_date_str.
    После обновления записывает в лог сообщение об успешном обновлении или ошибке.
    """
    try:
        remote_dt = parsedate_to_datetime(remote_date_str)
    except Exception as e:
        write_log(f"Ошибка при разборе даты '{remote_date_str}' для файла {file_path}: {e}", log_type="error")
        return False
    timestamp = remote_dt.timestamp()
    os.utime(file_path, (timestamp, timestamp))
    if os.name == 'nt':
        FILE_WRITE_ATTRIBUTES = 0x100
        handle = ctypes.windll.kernel32.CreateFileW(file_path, FILE_WRITE_ATTRIBUTES, 0, None, 3, 0x80, None)
        if handle == -1:
            write_log(f"Не удалось открыть файл {file_path} для изменения даты создания.", log_type="error")
            return False
        win_time = int((timestamp + 11644473600) * 10000000)
        ctime = ctypes.c_longlong(win_time)
        res = ctypes.windll.kernel32.SetFileTime(handle, ctypes.byref(ctime), None, None)
        ctypes.windll.kernel32.CloseHandle(handle)
        if res:
            write_log(f"Время создания файла {file_path} успешно установлено как {remote_date_str}.", log_type="info")
        else:
            write_log(f"Не удалось установить время создания файла {file_path}.", log_type="error")
        return res
    write_log(f"Время создания файла {file_path} установлено через os.utime как {remote_date_str}.", log_type="info")
    return True

def set_file_title(file_path, title):
    """
    Устанавливает значение тега Title (©nam) для MP4-файла с помощью mutagen.
    После обновления записывает в лог результат операции.
    """
    try:
        video = MP4(file_path)
        video["©nam"] = [title]
        video.save()
        write_log(f"Title для файла {file_path} успешно установлен: {title}.", log_type="info")
        return True
    except Exception as e:
        write_log(f"Ошибка при установке Title для {file_path}: {e}", log_type="error")
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

# ======================= Новый подход: Извлечение Media Created через exiftool =======================
def get_media_created_exiftool(file_path):
    """
    Извлекает значение Media Create Date из MP4-файла с помощью exiftool.
    Ожидаемый формат: "YYYY:MM:DD HH:MM:SS"
    Возвращает timestamp или None, если извлечение не удалось.
    """
    exiftool_path = r"C:\Portable\Exiftool\exiftool.exe"
    file_path = os.path.normpath(file_path)
    command = [exiftool_path, "-s", "-s", "-s", "-MediaCreateDate", file_path]
    write_log("Exiftool get command: " + " ".join(command), log_type="info")
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            media_date_str = result.stdout.strip()
            write_log(f"Exiftool вернул MediaCreateDate: '{media_date_str}'", log_type="info")
            if media_date_str:
                try:
                    media_dt = datetime.datetime.strptime(media_date_str, "%Y:%m:%d %H:%M:%S")
                    return media_dt.timestamp()
                except Exception as parse_ex:
                    write_log(f"Ошибка парсинга даты из exiftool: {parse_ex}", log_type="error")
                    return None
            else:
                write_log("Exiftool вернул пустую строку для MediaCreateDate", log_type="error")
                return None
        else:
            write_log(f"Exiftool: ошибка извлечения MediaCreateDate: {result.stderr}", log_type="error")
            return None
    except Exception as e:
        write_log(f"Exiftool: исключение при извлечении MediaCreateDate: {e}", log_type="error")
        return None

# ======================= Новый подход: Обновление внутренних MP4 метаданных через exiftool =======================
def update_mp4_internal_dates(file_path, new_date):
    """
    Обновляет внутренние метаданные MP4-файла (MediaCreateDate, CreateDate, ModifyDate)
    с использованием exiftool.
    new_date: строка в формате "YYYY:MM:DD HH:MM:SS"
    """
    import subprocess
    file_path = os.path.normpath(file_path)
    exiftool_path = r"C:\Portable\Exiftool\exiftool.exe"
    command = [
        exiftool_path,
        "-overwrite_original",
        f"-CreateDate={new_date}",
        f"-ModifyDate={new_date}",
        f"-MediaCreateDate={new_date}",
        file_path
    ]
    write_log("Exiftool command: " + " ".join(command), log_type="info")
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            write_log(f"Exiftool: внутренние метаданные MP4 обновлены для '{file_path}' на {new_date}", log_type="info")
        else:
            write_log(f"Exiftool: ошибка обновления метаданных для '{file_path}': {result.stderr}", log_type="error")
    except Exception as e:
        write_log(f"Exiftool: исключение при обновлении метаданных для '{file_path}': {e}", log_type="error")

# ======================= Функция синхронизации дат (обновлённая) =======================
def synchronize_file_dates(file_path):
    """
    Сравнивает значения времени создания (Data Created), изменения (Data Modified)
    и времени создания медиа (Media Created), извлечённые через exiftool.
    Определяет наименьшее значение и устанавливает его для всех.
    Затем с помощью exiftool обновляет внутренние MP4 метаданные.
    Добавлено подробное логирование каждого шага.
    В конце переустанавливаются системные даты, чтобы Date Modified не менялось.
    """
    import os, time, ctypes
    from datetime import datetime
    try:
        # Извлекаем системные даты
        creation_time = os.path.getctime(file_path)
        modification_time = os.path.getmtime(file_path)
        write_log(
            f"Исходные системные даты для '{file_path}': Created = {time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(creation_time))}, "
            f"Modified = {time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(modification_time))}",
            log_type="info"
        )
        times = [creation_time, modification_time]

        # Извлекаем Media Created через exiftool
        media_time = get_media_created_exiftool(file_path)
        if media_time is not None:
            times.append(media_time)
            write_log(f"Media Created (exiftool) timestamp: {media_time} ({time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(media_time))})", log_type="info")
        else:
            write_log(f"Media Created не найден через exiftool для '{file_path}'", log_type="info")

        # Вычисляем минимальное время
        min_time = min(times)
        write_log(
            f"Минимальное время для '{file_path}': {min_time} ({time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(min_time))})",
            log_type="info"
        )

        # Обновляем MP4 тег "©day" с новым значением (через mutagen)
        try:
            from mutagen.mp4 import MP4
            video = MP4(file_path)
            new_date_str_mp4 = time.strftime("%d-%b-%y %I:%M %p", time.gmtime(min_time))
            video["©day"] = [new_date_str_mp4]
            video.save()
            write_log(f"MP4 тег '©day' обновлён для '{file_path}' на {new_date_str_mp4}", log_type="info")
        except Exception as e:
            write_log(f"Ошибка обновления MP4 тега '©day': {e}", log_type="error")

        # Обновляем системные даты через os.utime
        os.utime(file_path, (min_time, min_time))
        write_log(
            f"os.utime установлено для '{file_path}' на {time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(min_time))}",
            log_type="info"
        )

        # Если Windows, обновляем все даты через Windows API
        if os.name == 'nt':
            from ctypes import wintypes
            kernel32 = ctypes.windll.kernel32
            class FILETIME(ctypes.Structure):
                _fields_ = [("dwLowDateTime", wintypes.DWORD),
                            ("dwHighDateTime", wintypes.DWORD)]
            def unix_to_filetime(t):
                ft = int((t + 11644473600) * 10000000)
                low = ft & 0xFFFFFFFF
                high = ft >> 32
                return FILETIME(low, high)
            ft_struct = unix_to_filetime(min_time)
            FILE_WRITE_ATTRIBUTES = 0x100
            handle = kernel32.CreateFileW(file_path, FILE_WRITE_ATTRIBUTES, 0, None, 3, 0x80, None)
            if handle not in (-1, 0):
                res = kernel32.SetFileTime(handle, ctypes.byref(ft_struct), ctypes.byref(ft_struct), ctypes.byref(ft_struct))
                if res:
                    write_log(
                        f"Windows API: Все времена установлены для '{file_path}' на {time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(min_time))}",
                        log_type="info"
                    )
                else:
                    write_log("Ошибка при установке времени через Windows API", log_type="error")
                kernel32.CloseHandle(handle)
            else:
                write_log("Не удалось открыть файл через Windows API", log_type="error")

        # Обновляем внутренние MP4 метаданные через exiftool
        new_date_str_exif = time.strftime("%Y:%m:%d %H:%M:%S", time.gmtime(min_time))
        update_mp4_internal_dates(file_path, new_date_str_exif)

        # *** Дополнительный шаг: переустанавливаем системные даты после exiftool ***
        os.utime(file_path, (min_time, min_time))
        write_log(
            f"После exiftool: os.utime переустановлено для '{file_path}' на {time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(min_time))}",
            log_type="info"
        )
        if os.name == 'nt':
            from ctypes import wintypes
            kernel32 = ctypes.windll.kernel32
            class FILETIME(ctypes.Structure):
                _fields_ = [("dwLowDateTime", wintypes.DWORD),
                            ("dwHighDateTime", wintypes.DWORD)]
            def unix_to_filetime(t):
                ft = int((t + 11644473600) * 10000000)
                low = ft & 0xFFFFFFFF
                high = ft >> 32
                return FILETIME(low, high)
            ft_struct = unix_to_filetime(min_time)
            FILE_WRITE_ATTRIBUTES = 0x100
            handle = kernel32.CreateFileW(file_path, FILE_WRITE_ATTRIBUTES, 0, None, 3, 0x80, None)
            if handle not in (-1, 0):
                res = kernel32.SetFileTime(handle, ctypes.byref(ft_struct), ctypes.byref(ft_struct), ctypes.byref(ft_struct))
                if res:
                    write_log(
                        f"После exiftool: Windows API: Все времена переустановлены для '{file_path}' на {time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(min_time))}",
                        log_type="info"
                    )
                else:
                    write_log("Ошибка при переустановке времени через Windows API после exiftool", log_type="error")
                kernel32.CloseHandle(handle)
        write_log(f"Синхронизация дат для '{file_path}' завершена.", log_type="info")
    except Exception as e:
        write_log(f"Ошибка синхронизации дат для '{file_path}': {e}", log_type="error")