import os
import pickle
import time
import requests
import threading
import tkinter as tk  # Для использования виджетов в GUI
from urllib.parse import urlparse, parse_qs
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import write_log, save_failed_link

# Глобальные переменные для отслеживания состояния загрузки
is_downloading_video = False
is_processing_links = False
current_video_url = None
current_video_name = None

# Глобальный флаг для сбора ссылок (чтобы не запускать несколько потоков)
is_collecting_links = False

def find_and_download_video(driver, root, video_link, download_folder, pause_event, blacklist):
    try:
        driver.get(video_link)
        from utils import cookies_path
        if os.path.exists(cookies_path):
            with open(cookies_path, "rb") as file:
                cookies = pickle.load(file)
                for cookie in cookies:
                    driver.add_cookie(cookie)
            driver.refresh()
        video_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, '//div[@id="playerinfo"]//a[@class="download_links_href"]')
            )
        )
        video_options = []
        for video_element in video_elements:
            vid_url = video_element.get_attribute("href")
            try:
                response = requests.head(vid_url, allow_redirects=True)
                size_bytes = int(response.headers.get('Content-Length', 0))
                video_options.append((vid_url, size_bytes))
            except Exception as e:
                write_log(f"Ошибка при определении размера для ссылки: {vid_url}. Ошибка: {e}", log_type="error")
        if video_options:
            largest_video = max(video_options, key=lambda x: x[1])
            largest_video_url, largest_video_size = largest_video
            video_name = largest_video_url.split("/")[-1].split("?")[0]
            for num in blacklist:
                if num in video_name:
                    write_log(f"Пропуск {video_name}: содержит число {num} из черного списка.", log_type="info")
                    return
            write_log(f"Выбрана самая большая версия видео: {video_name} ({largest_video_size / (1024 ** 2):.2f} MB)", log_type="info")
            from tkinter import ttk
            progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
            progress_bar.pack(pady=(5, 10))
            progress_label = tk.Label(root, text=f"Загрузка {video_name}...", font=("Helvetica", 14))
            progress_label.pack(pady=(5, 15))
            download_video(largest_video_url, download_folder, video_name, pause_event, progress_label, progress_bar, blacklist)
            progress_label.destroy()
            progress_bar.destroy()
        else:
            write_log(f"Не найдено доступных версий видео для ссылки: {video_link}", log_type="error")
    except Exception as e:
        write_log(f"Ошибка при обработке видео {video_link}: {e}", log_type="error")
        save_failed_link(video_link)

def download_video(video_url, output_folder, video_name, pause_event, progress_label, progress_bar, blacklist):
    for num in blacklist:
        if num in video_name:
            write_log(f"Пропуск {video_name}: содержит число {num} из черного списка.", log_type="info")
            return
    global is_downloading_video, current_video_url, current_video_name
    is_downloading_video = True
    current_video_url = video_url
    current_video_name = video_name
    try:
        response = requests.get(video_url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        output_path = os.path.join(output_folder, video_name)
        if os.path.exists(output_path):
            existing_size = os.path.getsize(output_path)
            if existing_size == total_size:
                write_log(f"{video_name} уже скачано, пропуск.", log_type="info")
                return
            else:
                write_log(f"{video_name}: размер не совпадает, перекачка.", log_type="info")
        downloaded = 0
        chunk_size = 8192
        start_time = time.time()
        with open(output_path, "wb") as file:
            for chunk in response.iter_content(chunk_size):
                pause_event.wait()
                file.write(chunk)
                downloaded += len(chunk)
                progress_percent = int(downloaded / total_size * 100)
                progress_bar["value"] = progress_percent
                speed = downloaded / 1024 / max(time.time() - start_time, 1)
                progress_label.config(text=f"{video_name}: {progress_percent}% @ {speed:.2f} KB/s")
        write_log(f"{video_name} скачано успешно.", log_type="info")
    except Exception as e:
        write_log(f"Ошибка при скачивании {video_name}: {e}", log_type="error")
        save_failed_link(video_url)
    is_downloading_video = False


def collect_video_links(root, start_url, download_folder, search_pause_event):
    """
    Обновлённая функция сбора ссылок:
    – Каждая найденная ссылка нормализуется с помощью strip().
    – Если ссылка не содержится в файле video_links.txt, она сразу записывается.
    – Проверка на наличие скачанного видео (по размеру файла) будет выполняться только при загрузке видео.
    """
    global is_collecting_links
    if is_collecting_links:
        write_log("Сбор ссылок уже запущен!", log_type="info")
        return
    is_collecting_links = True

    video_links_file = "video_links.txt"
    existing_links = set()
    if os.path.exists(video_links_file):
        with open(video_links_file, "r", encoding="utf-8") as f:
            for line in f:
                link = line.strip()
                if link:
                    existing_links.add(link)
    links_collected = list(existing_links)

    from urllib.parse import urlparse, parse_qs
    parsed_url = urlparse(start_url)
    query_params = parse_qs(parsed_url.query)
    current_offset = int(query_params.get("offset", [0])[0])
    mode = query_params.get("mode", ["latest"])[0]

    base_url = f"https://beautifulagony.com/public/main.php?page=view&mode={mode}&offset={{}}"
    current_url = base_url.format(current_offset)

    try:
        from browser import driver
        while True:
            search_pause_event.wait()
            write_log(f"Сбор ссылок, страница: {current_url}", log_type="page")
            driver.get(current_url)
            page_links = driver.find_elements(By.XPATH, '//a[contains(@href, "page=player&out=bkg&media")]')
            if not page_links:
                write_log("На странице не найдено видео ссылок, завершаем сбор.", log_type="info")
                break
            from utils import load_blacklist
            blacklist = load_blacklist("blacklist.txt")
            for link in page_links:
                video_link = link.get_attribute("href")
                if video_link:
                    video_link = video_link.strip()  # Нормализуем ссылку
                else:
                    continue
                # Если ссылка уже есть в файле, пропускаем её
                if video_link in existing_links:
                    write_log(f"Ссылка уже существует: {video_link}", log_type="info")
                    continue
                video_name = video_link.split("/")[-1].split("?")[0]
                skip = False
                for num in blacklist:
                    if num in video_name:
                        skip = True
                        break
                if skip:
                    write_log(f"Ссылка {video_link} пропущена из-за черного списка", log_type="info")
                    continue

                # Здесь мы уже не проверяем, скачано ли видео (по размеру), просто добавляем новую ссылку.
                with open(video_links_file, "a", encoding="utf-8") as f:
                    f.write(video_link + "\n")
                existing_links.add(video_link)
                links_collected.append(video_link)
                write_log(f"Новая ссылка добавлена: {video_link}", log_type="info")
            current_offset += 20
            current_url = base_url.format(current_offset)
        write_log(f"Сбор ссылок завершён, собрано {len(links_collected)} ссылок.", log_type="info")
    except Exception as e:
        write_log(f"Ошибка при сборе ссылок: {e}", log_type="error")
    is_collecting_links = False
    return links_collected


def download_videos_sequential(root, download_folder, pause_event):
    from utils import load_blacklist, write_log
    try:
        with open("video_links.txt", "r", encoding="utf-8") as f:
            links = [line.strip() for line in f if line.strip()]
    except Exception as e:
        write_log(f"Ошибка при чтении файла ссылок: {e}", log_type="error")
        return
    if not links:
        write_log("Файл ссылок пуст.", log_type="info")
        return
    write_log("Начало последовательной загрузки видео.", log_type="info")
    import customtkinter as ctk
    progress_window = ctk.CTkToplevel(root)
    progress_window.title("Последовательная загрузка видео")
    progress_window.geometry("600x400")
    progress_container = ctk.CTkFrame(progress_window)
    progress_container.pack(fill="both", expand=True)
    blacklist = load_blacklist("blacklist.txt")
    from browser import driver
    for link in links:
        frame = ctk.CTkFrame(progress_container)
        frame.pack(pady=5, fill="x")
        label = ctk.CTkLabel(frame, text="Подготовка...")
        label.pack(side="left", padx=5)
        progress_bar = ctk.CTkProgressBar(frame, width=300)
        progress_bar.pack(side="left", padx=5)
        download_video_sequential(driver, root, link, download_folder, pause_event, blacklist)
    write_log("Последовательная загрузка завершена.", log_type="info")

def download_video_sequential(driver, root, video_link, download_folder, pause_event, blacklist):
    try:
        driver.get(video_link)
        from utils import cookies_path
        if os.path.exists(cookies_path):
            with open(cookies_path, "rb") as file:
                cookies = pickle.load(file)
                for cookie in cookies:
                    driver.add_cookie(cookie)
            driver.refresh()
        video_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, '//div[@id="playerinfo"]//a[@class="download_links_href"]')
            )
        )
        video_options = []
        for video_element in video_elements:
            vid_url = video_element.get_attribute("href")
            try:
                response = requests.head(vid_url, allow_redirects=True)
                size_bytes = int(response.headers.get('Content-Length', 0))
                video_options.append((vid_url, size_bytes))
            except Exception as e:
                write_log(f"Ошибка при определении размера для ссылки: {vid_url}. Ошибка: {e}", log_type="error")
        if video_options:
            largest_video = max(video_options, key=lambda x: x[1])
            largest_video_url, largest_video_size = largest_video
            video_name = largest_video_url.split("/")[-1].split("?")[0]
            for num in blacklist:
                if num in video_name:
                    write_log(f"Пропуск {video_name}: содержит число {num} из черного списка.", log_type="info")
                    return
            write_log(f"Выбрана самая большая версия видео: {video_name} ({largest_video_size / (1024 ** 2):.2f} MB)", log_type="info")
            from tkinter import ttk
            progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
            progress_bar.pack(pady=(5, 10))
            progress_label = tk.Label(root, text=f"Загрузка {video_name}...", font=("Helvetica", 14))
            progress_label.pack(pady=(5, 15))
            download_video(largest_video_url, download_folder, video_name, pause_event, progress_label, progress_bar, blacklist)
            progress_label.destroy()
            progress_bar.destroy()
        else:
            write_log(f"Не найдено доступных версий видео для ссылки: {video_link}", log_type="error")
    except Exception as e:
        write_log(f"Ошибка при обработке видео {video_link}: {e}", log_type="error")
        save_failed_link(video_link)
