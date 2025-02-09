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

def find_and_download_video(driver, root, video_link, download_folder, pause_event, blacklist):
    """
    Находит доступные форматы видео и загружает самую большую версию, если её имя не содержит число из черного списка.
    """
    try:
        driver.get(video_link)

        # Загружаем куки, если они есть
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
            video_url = video_element.get_attribute("href")
            try:
                response = requests.head(video_url, allow_redirects=True)
                size_bytes = int(response.headers.get('Content-Length', 0))
                video_options.append((video_url, size_bytes))
            except Exception as e:
                write_log(f"Ошибка при определении размера для ссылки: {video_url}. Ошибка: {e}", log_type="error")

        if video_options:
            largest_video = max(video_options, key=lambda x: x[1])
            largest_video_url, largest_video_size = largest_video
            video_name = largest_video_url.split("/")[-1].split("?")[0]

            # Проверка: если имя видео содержит число из черного списка, пропускаем загрузку
            for num in blacklist:
                if num in video_name:
                    write_log(f"Пропуск {video_name}: содержит число {num} из черного списка.", log_type="info")
                    return

            write_log(f"Выбрана самая большая версия видео: {video_name} ({largest_video_size / (1024 ** 2):.2f} MB)", log_type="info")

            from tkinter import ttk
            progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
            # Добавляем отступы: сверху 5 пикселей и снизу 10 пикселей
            progress_bar.pack(pady=(5, 10))
            # Указываем увеличенный шрифт для надписи прогресса (например, Helvetica размер 14)
            progress_label = tk.Label(root, text=f"Загрузка {video_name}...", font=("Helvetica", 14))
            # Добавляем отступы: сверху 5 пикселей и снизу 15 пикселей
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
    """
    Скачивает видео с обновлением прогресса, если имя видео не содержит число из черного списка.
    """
    # Дополнительная проверка (на всякий случай)
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

def download_all_videos(root, start_url, step, download_folder, pause_event):
    global is_processing_links
    is_processing_links = True

    from utils import load_blacklist
    blacklist = load_blacklist("blacklist.txt")

    try:
        parsed_url = urlparse(start_url)
        query_params = parse_qs(parsed_url.query)
        current_offset = int(query_params.get("offset", [0])[0])
        current_url = start_url

        from browser import driver
        while True:
            pause_event.wait()
            write_log(f"Обработка страницы: {current_url}", log_type="page")
            driver.get(current_url)
            links = driver.find_elements(By.XPATH, '//a[contains(@href, "page=player&out=bkg&media")]')
            if not links:
                write_log("Видео на странице не найдены. Завершаем обработку.", log_type="info")
                break
            video_links = [link.get_attribute("href") for link in links]
            for video_link in video_links:
                pause_event.wait()
                find_and_download_video(driver, root, video_link, download_folder, pause_event, blacklist)
            current_offset += step * 20
            current_url = f"https://beautifulagony.com/public/main.php?page=view&mode=latest&offset={current_offset}"
    except Exception as e:
        write_log(f"Ошибка при обходе страниц: {e}", log_type="error")
    is_processing_links = False
