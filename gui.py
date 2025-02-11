import customtkinter as ctk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import tkinter as tk  # Для переменных и fallback для текстового поля
import threading

from browser import authorize, check_authorization
from downloader import (
    collect_video_links,
    download_videos_sequential,
    is_processing_links  # Флаг, если понадобится
)
from utils import (
    open_log_file,
    open_failed_links_file,
    open_blacklist_file,  # Функция для открытия файла черного списка
    select_download_folder,
    set_log_widgets,
    DOWNLOAD_FOLDER
)

# Глобальное событие для управления загрузкой видео
pause_event = threading.Event()
pause_event.set()
# Отдельное событие для управления поиском ссылок
search_pause_event = threading.Event()
search_pause_event.set()

def pause_link_processing():
    pause_event.clear()

def resume_link_processing():
    pause_event.set()

def open_download_folder(folder_path):
    import os
    try:
        os.startfile(folder_path)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось открыть папку: {e}")

def stop_downloading():
    import downloader
    downloader.stop_downloading_flag = True

def create_gui():
    # Настройка внешнего вида customtkinter
    ctk.set_appearance_mode("dark")  # "dark", "light" или "system"
    ctk.set_default_color_theme("blue")  # Например, "blue", "green", "dark-blue"

    root = ctk.CTk()
    root.title("Beautiful Agony Video Downloader")
    root.geometry("800x1100")  # Немного увеличенная высота для новых кнопок

    # Главный фрейм для размещения всех блоков
    main_frame = ctk.CTkFrame(master=root)
    main_frame.pack(padx=20, pady=20, fill="both", expand=True)

    #########################################
    # 1. Блок авторизации
    auth_frame = ctk.CTkFrame(master=main_frame, fg_color="transparent")
    auth_frame.pack(pady=10, fill="x")

    timer_label = ctk.CTkLabel(master=auth_frame, text="Нажмите 'Пройти авторизацию', чтобы начать.")
    timer_label.pack(side="left", padx=5, pady=5)

    check_button = ctk.CTkButton(
        master=auth_frame, text="Проверить авторизацию",
        state="disabled",
        command=lambda: check_authorization(timer_label, root)
    )
    check_button.pack(side="left", padx=5, pady=5)

    auth_button = ctk.CTkButton(
        master=auth_frame, text="Пройти авторизацию",
        command=lambda: authorize(timer_label, check_button, root)
    )
    auth_button.pack(side="left", padx=5, pady=5)

    #########################################
    # 2. Блок настроек
    settings_frame = ctk.CTkFrame(master=main_frame, fg_color="transparent")
    settings_frame.pack(pady=10, fill="x")

    # 2.1 Выбор папки загрузки
    folder_frame = ctk.CTkFrame(master=settings_frame, fg_color="transparent")
    folder_frame.pack(pady=5, fill="x")
    folder_label = ctk.CTkLabel(master=folder_frame, text="Выберите папку загрузки:")
    folder_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    download_folder_var = tk.StringVar(value=DOWNLOAD_FOLDER)
    folder_entry = ctk.CTkEntry(master=folder_frame, textvariable=download_folder_var, width=300)
    folder_entry.grid(row=0, column=1, padx=5, pady=5)
    select_folder_button = ctk.CTkButton(
        master=folder_frame, text="Выбрать папку",
        command=lambda: select_download_folder(download_folder_var)
    )
    select_folder_button.grid(row=0, column=2, padx=5, pady=5)

    # 2.2 Ввод URL (начальной страницы для сбора ссылок)
    url_frame = ctk.CTkFrame(master=settings_frame, fg_color="transparent")
    url_frame.pack(pady=5, fill="x")
    url_label = ctk.CTkLabel(master=url_frame, text="Введите начальный URL:")
    url_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    default_url = "https://beautifulagony.com/public/main.php?page=view&mode=latest&offset=0"
    url_var = tk.StringVar(value=default_url)
    url_entry = ctk.CTkEntry(master=url_frame, textvariable=url_var, width=400)
    url_entry.grid(row=0, column=1, padx=5, pady=5)

    #########################################
    # 3. Блок сбора ссылок (Этап 1)
    collection_frame = ctk.CTkFrame(master=main_frame, fg_color="transparent")
    collection_frame.pack(pady=10, fill="x")

    # Переменная для чекбокса остановки поиска после 3 пустых страниц
    stop_empty_pages_var = tk.BooleanVar(value=False)

    # Чекбокс для остановки поиска ссылок, если 3 страницы подряд не дали новых ссылок
    stop_empty_pages_checkbox = ctk.CTkCheckBox(
        master=collection_frame,
        text="Остановить поиск, если 3 страницы подряд без новых ссылок",
        variable=stop_empty_pages_var
    )
    stop_empty_pages_checkbox.grid(row=0, column=3, padx=5, pady=5)

    # Функция для запуска сбора ссылок с изменением логики кнопок
    def start_collecting():
        from downloader import is_collecting_links
        if is_collecting_links:
            messagebox.showinfo("Информация", "Сбор ссылок уже запущен!")
            return
        # Скрываем кнопку "Собрать ссылки на видео"
        collect_button.grid_remove()
        # Показываем кнопки "Остановить поиск ссылок" и "Возобновить поиск ссылок"
        stop_search_button.grid()
        resume_search_button.grid()
        threading.Thread(
            target=lambda: collect_video_links(root, url_var.get(), download_folder_var.get(), search_pause_event, stop_empty_pages_var.get()),
            daemon=True
        ).start()

    collect_button = ctk.CTkButton(
        master=collection_frame, text="Собрать ссылки на видео",
        command=start_collecting
    )
    collect_button.grid(row=0, column=0, padx=5, pady=5)
    # Скрываем кнопку изначально
    collect_button.grid_remove()

    stop_search_button = ctk.CTkButton(
        master=collection_frame, text="Остановить поиск ссылок",
        command=lambda: search_pause_event.clear()
    )
    stop_search_button.grid(row=0, column=1, padx=5, pady=5)
    # Скрываем кнопки поиска изначально
    stop_search_button.grid_remove()

    resume_search_button = ctk.CTkButton(
        master=collection_frame, text="Возобновить поиск ссылок",
        command=lambda: search_pause_event.set()
    )
    resume_search_button.grid(row=0, column=2, padx=5, pady=5)
    resume_search_button.grid_remove()

    #########################################
    # 4. Блок последовательной загрузки (Этап 2) и управление загрузкой
    download_control_frame = ctk.CTkFrame(master=main_frame, fg_color="transparent")
    download_control_frame.pack(pady=10, fill="x")

    # Переменная для чекбокса остановки загрузки после 10 подряд пропущенных видео
    stop_after_skips_var = tk.BooleanVar(value=False)

    # Чекбокс для остановки загрузки, если 10 видео подряд уже скачаны или в черном списке
    stop_after_skips_checkbox = ctk.CTkCheckBox(
        master=download_control_frame,
        text="Остановить загрузку после 10 подряд пропущенных видео",
        variable=stop_after_skips_var
    )
    stop_after_skips_checkbox.grid(row=1, column=0, padx=5, pady=5, columnspan=2)

    # Функция для запуска загрузки с изменением логики кнопок
    def start_downloading():
        # Перед запуском сбрасываем флаг остановки загрузки
        import downloader
        downloader.stop_downloading_flag = False
        # Скрываем кнопку "Скачать видео по ссылкам"
        download_seq_button.grid_remove()
        # Показываем кнопки "Пауза загрузки", "Возобновить загрузку" и "Остановить загрузку"
        pause_button.grid()
        resume_button.grid()
        stop_download_button.grid()
        threading.Thread(
            target=lambda: download_videos_sequential(root, download_folder_var.get(), pause_event, stop_after_skips_var.get()),
            daemon=True
        ).start()

    download_seq_button = ctk.CTkButton(
        master=download_control_frame,
        text="Скачать видео по ссылкам",
        command=start_downloading
    )
    download_seq_button.grid(row=0, column=0, padx=5, pady=5)
    # Скрываем кнопку изначально
    download_seq_button.grid_remove()

    pause_button = ctk.CTkButton(
        master=download_control_frame,
        text="Пауза загрузки",
        command=lambda: pause_event.clear()
    )
    pause_button.grid(row=0, column=1, padx=5, pady=5)
    pause_button.grid_remove()

    resume_button = ctk.CTkButton(
        master=download_control_frame,
        text="Возобновить загрузку",
        command=lambda: pause_event.set()
    )
    resume_button.grid(row=0, column=2, padx=5, pady=5)
    resume_button.grid_remove()

    stop_download_button = ctk.CTkButton(
        master=download_control_frame,
        text="Остановить загрузку после текущего видео",
        command=stop_downloading
    )
    stop_download_button.grid(row=0, column=3, padx=5, pady=5)
    stop_download_button.grid_remove()

    #########################################
    # 5. Блок для открытия файла со ссылками и папки загрузок
    files_frame = ctk.CTkFrame(master=main_frame, fg_color="transparent")
    files_frame.pack(pady=10, fill="x")
    open_links_button = ctk.CTkButton(
        master=files_frame,
        text="Открыть файл со ссылками",
        command=lambda: __import__("os").startfile("video_links.txt")
    )
    open_links_button.grid(row=0, column=0, padx=5, pady=5)
    open_downloads_button = ctk.CTkButton(
        master=files_frame,
        text="Открыть папку загрузок",
        command=lambda: open_download_folder(download_folder_var.get())
    )
    open_downloads_button.grid(row=0, column=1, padx=5, pady=5)

    #########################################
    # 6. Блок работы с чёрным списком
    blacklist_frame = ctk.CTkFrame(master=main_frame, fg_color="transparent")
    blacklist_frame.pack(pady=10, fill="x")

    def create_blacklist():
        from utils import create_blacklist_from_pages
        blacklist = create_blacklist_from_pages()
        messagebox.showinfo("Черный список", f"Черный список создан.\nНайдено чисел: {len(blacklist)}")

    create_blacklist_button = ctk.CTkButton(
        master=blacklist_frame, text="Создать черный список",
        command=lambda: threading.Thread(target=create_blacklist, daemon=True).start()
    )
    create_blacklist_button.grid(row=0, column=0, padx=5, pady=5)
    open_blacklist_button = ctk.CTkButton(
        master=blacklist_frame, text="Открыть черный список",
        command=open_blacklist_file
    )
    open_blacklist_button.grid(row=0, column=1, padx=5, pady=5)

    #########################################
    # 7. Блок логов
    log_frame = ctk.CTkFrame(master=main_frame, fg_color="transparent")
    log_frame.pack(pady=10, fill="both", expand=True)
    try:
        log_text = ctk.CTkTextbox(master=log_frame, wrap="word", width=600, height=200)
    except AttributeError:
        log_text = tk.Text(master=log_frame, wrap="word", width=60, height=15)
    log_text.pack(pady=5, padx=5, fill="both", expand=True)
    log_buttons_frame = ctk.CTkFrame(master=log_frame, fg_color="transparent")
    log_buttons_frame.pack(pady=5, fill="x")
    log_file_button = ctk.CTkButton(master=log_buttons_frame, text="Открыть лог файл", command=open_log_file)
    log_file_button.grid(row=0, column=0, padx=5, pady=5)
    failed_file_button = ctk.CTkButton(master=log_buttons_frame, text="Открыть файл ошибок",
                                       command=open_failed_links_file)
    failed_file_button.grid(row=0, column=1, padx=5, pady=5)
    show_only_pages_and_errors = tk.BooleanVar(value=False)
    filter_checkbox = ctk.CTkCheckBox(master=log_buttons_frame, text="Показывать только страницы и ошибки",
                                      variable=show_only_pages_and_errors)
    filter_checkbox.grid(row=0, column=2, padx=5, pady=5)
    set_log_widgets(log_text, show_only_pages_and_errors)

    # Переназначаем команду кнопки авторизации, чтобы после её нажатия
    # появились кнопки "Собрать ссылки на видео" и "Скачать видео по ссылкам"
    def on_authorize():
        authorize(timer_label, check_button, root)
        collect_button.grid()       # Показываем кнопку сбора ссылок
        download_seq_button.grid()  # Показываем кнопку загрузки видео

    auth_button.configure(command=on_authorize)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
