import customtkinter as ctk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import tkinter as tk  # Для переменных (StringVar, BooleanVar) и fallback для текстового поля
import threading

from browser import authorize, check_authorization
from downloader import download_all_videos
from utils import (
    open_log_file,
    open_failed_links_file,
    open_blacklist_file,  # Новая функция для открытия файла черного списка
    select_download_folder,
    set_log_widgets,
    DOWNLOAD_FOLDER
)

# Глобальное событие для управления паузой
pause_event = threading.Event()
pause_event.set()

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

def create_gui():
    # Настройка внешнего вида customtkinter
    ctk.set_appearance_mode("dark")       # "dark", "light" или "system"
    ctk.set_default_color_theme("blue")    # Например, "blue", "green", "dark-blue" и т.д.

    root = ctk.CTk()
    root.title("Beautiful Agony Video Downloader")
    root.geometry("800x950")

    # Главный фрейм, в котором будут располагаться все блоки
    main_frame = ctk.CTkFrame(master=root)
    main_frame.pack(padx=20, pady=20, fill="both", expand=True)

    #########################################
    # 1. Блок авторизации
    auth_frame = ctk.CTkFrame(master=main_frame, fg_color="transparent")
    auth_frame.pack(pady=10, fill="x")

    timer_label = ctk.CTkLabel(master=auth_frame, text="Нажмите 'Пройти авторизацию', чтобы начать.")
    timer_label.pack(side="left", padx=5, pady=5)

    check_button = ctk.CTkButton(master=auth_frame, text="Проверить авторизацию",
                                 state="disabled",
                                 command=lambda: check_authorization(timer_label, root))
    check_button.pack(side="left", padx=5, pady=5)

    auth_button = ctk.CTkButton(master=auth_frame, text="Пройти авторизацию",
                                command=lambda: authorize(timer_label, check_button, root))
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
    select_folder_button = ctk.CTkButton(master=folder_frame, text="Выбрать папку",
                                         command=lambda: select_download_folder(download_folder_var))
    select_folder_button.grid(row=0, column=2, padx=5, pady=5)

    # 2.2 Ввод URL
    url_frame = ctk.CTkFrame(master=settings_frame, fg_color="transparent")
    url_frame.pack(pady=5, fill="x")
    url_label = ctk.CTkLabel(master=url_frame, text="Введите начальный URL:")
    url_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    default_url = "https://beautifulagony.com/public/main.php?page=view&mode=latest&offset=0"
    url_var = tk.StringVar(value=default_url)
    url_entry = ctk.CTkEntry(master=url_frame, textvariable=url_var, width=400)
    url_entry.grid(row=0, column=1, padx=5, pady=5)

    # 2.3 Выбор направления обхода пагинации
    direction_frame = ctk.CTkFrame(master=settings_frame, fg_color="transparent")
    direction_frame.pack(pady=5, fill="x")
    direction_label = ctk.CTkLabel(master=direction_frame, text="Выберите направление обхода пагинации:")
    direction_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    direction_var = tk.StringVar(value="вперёд")
    forward_radio = ctk.CTkRadioButton(master=direction_frame, text="Вперёд",
                                       variable=direction_var, value="вперёд")
    forward_radio.grid(row=0, column=1, padx=5, pady=5)
    backward_radio = ctk.CTkRadioButton(master=direction_frame, text="Назад",
                                        variable=direction_var, value="назад")
    backward_radio.grid(row=0, column=2, padx=5, pady=5)

    #########################################
    # 3. Блок управления загрузкой
    controls_frame = ctk.CTkFrame(master=main_frame, fg_color="transparent")
    controls_frame.pack(pady=10, fill="x")
    download_button = ctk.CTkButton(master=controls_frame, text="Скачать все видео",
                                    command=lambda: threading.Thread(
                                        target=download_all_videos,
                                        args=(
                                            root,
                                            url_var.get(),
                                            1 if direction_var.get() == "вперёд" else -1,
                                            download_folder_var.get(),
                                            pause_event,
                                        ),
                                        daemon=True
                                    ).start())
    download_button.grid(row=0, column=0, padx=5, pady=5)
    open_folder_button = ctk.CTkButton(master=controls_frame, text="Открыть папку загрузок",
                                       command=lambda: open_download_folder(download_folder_var.get()))
    open_folder_button.grid(row=0, column=1, padx=5, pady=5)

    pause_button = ctk.CTkButton(master=controls_frame, text="Пауза", command=lambda: pause_event.clear())
    pause_button.grid(row=1, column=0, padx=5, pady=5)
    resume_button = ctk.CTkButton(master=controls_frame, text="Возобновить", command=lambda: pause_event.set())
    resume_button.grid(row=1, column=1, padx=5, pady=5)
    pause_link_button = ctk.CTkButton(master=controls_frame, text="Пауза обхода ссылок", command=pause_link_processing)
    pause_link_button.grid(row=2, column=0, padx=5, pady=5)
    resume_link_button = ctk.CTkButton(master=controls_frame, text="Возобновить обход ссылок", command=resume_link_processing)
    resume_link_button.grid(row=2, column=1, padx=5, pady=5)

    #########################################
    # 4. Блок работы с черным списком
    blacklist_frame = ctk.CTkFrame(master=main_frame, fg_color="transparent")
    blacklist_frame.pack(pady=10, fill="x")

    def create_blacklist():
        from utils import create_blacklist_from_pages
        # Здесь используется авто-парсинг для режимов "males" и "transgender"
        blacklist = create_blacklist_from_pages()
        messagebox.showinfo("Черный список", f"Черный список создан.\nНайдено чисел: {len(blacklist)}")

    create_blacklist_button = ctk.CTkButton(master=blacklist_frame, text="Создать черный список",
                                            command=lambda: threading.Thread(target=create_blacklist, daemon=True).start())
    create_blacklist_button.grid(row=0, column=0, padx=5, pady=5)

    open_blacklist_button = ctk.CTkButton(master=blacklist_frame, text="Открыть черный список",
                                          command=open_blacklist_file)
    open_blacklist_button.grid(row=0, column=1, padx=5, pady=5)

    #########################################
    # 5. Блок логов
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
    failed_file_button = ctk.CTkButton(master=log_buttons_frame, text="Открыть файл ошибок", command=open_failed_links_file)
    failed_file_button.grid(row=0, column=1, padx=5, pady=5)
    show_only_pages_and_errors = tk.BooleanVar(value=False)
    filter_checkbox = ctk.CTkCheckBox(master=log_buttons_frame, text="Показывать только страницы и ошибки",
                                      variable=show_only_pages_and_errors)
    filter_checkbox.grid(row=0, column=2, padx=5, pady=5)

    set_log_widgets(log_text, show_only_pages_and_errors)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
