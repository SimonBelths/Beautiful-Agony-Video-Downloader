import os
import webbrowser
import tkinter as tk
import requests
from bs4 import BeautifulSoup

# Константы и пути к файлам
DOWNLOAD_FOLDER = r"S:\Beautiful Agony"
cookies_path = "cookies.pkl"
log_file_path = "logs.txt"
failed_links_path = "failed_links.txt"

# Виджеты для логирования (будут заданы из GUI)
log_text = None
show_only_pages_and_errors = None

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

def select_download_folder(download_folder_var):
    from tkinter import filedialog, messagebox
    folder = filedialog.askdirectory(initialdir=DOWNLOAD_FOLDER)
    if folder:
        download_folder_var.set(folder)
        messagebox.showinfo("Папка загрузок", f"Выбрана папка: {folder}")

def create_blacklist_for_mode(mode):
    """
    Парсит страницы для заданного режима (например, 'males' или 'transgender')
    и собирает уникальные 4-значные номера.
    Автоматически перебирает страницы с пагинацией до тех пор, пока на странице не окажется номеров.
    Возвращает множество найденных номеров.
    """
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
