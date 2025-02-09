# blacklist.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def extract_video_names_from_page(driver, url):
    """
    Загружает страницу по URL, ожидает появления видео-ссылок и извлекает названия видео.
    Предполагается, что видео-ссылки можно найти по XPath, а их текст или атрибут title являются названием.
    """
    driver.get(url)
    # Ждем, пока на странице появятся ссылки на видео
    video_elements = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located(
            (By.XPATH, '//a[contains(@href, "page=player&out=bkg&media")]')
        )
    )

    video_names = []
    for video in video_elements:
        name = video.text.strip()
        if not name:
            name = video.get_attribute("title")
        if name:
            video_names.append(name)
    return video_names


def update_blacklist(driver, base_url, mode, max_pages=10):
    """
    Проходит по страницам для заданного режима (например, males или transgender) и собирает названия видео.
    """
    blacklist = set()
    for page in range(max_pages):
        offset = page * 20  # предполагается 20 видео на страницу; корректируй по необходимости
        url = f"{base_url}?page=view&mode={mode}&offset={offset}"
        try:
            names = extract_video_names_from_page(driver, url)
            if not names:
                break  # Если на странице нет видео, дальше можно не искать
            blacklist.update(names)
        except Exception as e:
            print(f"Ошибка при обработке {url}: {e}")
            break
    return blacklist


def build_combined_blacklist(driver):
    """
    Собирает чёрный список для режимов "males" и "transgender" и сохраняет его в файл blacklist.txt.
    Возвращает объединённое множество названий.
    """
    base_url = "https://beautifulagony.com/public/main.php"
    blacklist_males = update_blacklist(driver, base_url, mode="males", max_pages=10)
    blacklist_trans = update_blacklist(driver, base_url, mode="transgender", max_pages=10)
    combined_blacklist = blacklist_males.union(blacklist_trans)

    with open("blacklist.txt", "w", encoding="utf-8") as f:
        for name in combined_blacklist:
            f.write(name + "\n")

    return combined_blacklist