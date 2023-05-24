import datetime
import io
import time
import requests
from http import HTTPStatus
from PyPDF2 import PdfReader
from telegram import Bot
from urllib.request import Request, urlopen


CURRENT_HOUR = datetime.datetime.utcnow().hour  # время для проверки публикации
CURRENT_DAY = datetime.datetime.utcnow().day  # день для адреса запроса
CURRENT_MONTH = datetime.datetime.utcnow().month  # месяц для адреса запроса
CURRENT_YEAR = datetime.datetime.utcnow().year  # год для адреса запроса
RETRY_TIME = 60  # время ожидания в работе основной функции main
TELEGRAM_TOKEN = '6024379156:AAFKOSfzXb9MO8PIh2abDlrLEB1HCkNB1BY'
TELEGRAM_CHAT_ID = -892049552


def define_date_for_link():
    """Определяем дату для включения в адрес запроса"""
    link_date = f'{CURRENT_DAY}{CURRENT_MONTH}{CURRENT_YEAR}'
    return link_date


def define_currency_link(link_date):
    """Определяем ссылку для бюллетеня по Валютному рынку."""
    currency_link = f'https://iss.moex.com/file/Currency_{link_date}.pdf'
    return currency_link


def define_metal_link(link_date):
    """Определяем ссылку для бюллетеня по Рынку драгоценных металлов."""
    metal_link = f'https://iss.moex.com/file/Metal_{link_date}.pdf'
    return metal_link


def check_currency_link(currency_link):
    """Проверяем ссылку для бюллетеня по Валютному рынку."""
    currency_check = requests.head(currency_link, verify=False)
    if currency_check.status_code == HTTPStatus.OK:
        currency_status = 'Ok'
    else:
        currency_status = 'False'
    return currency_status


def check_metal_link(metal_link):
    """Проверяем ссылку для бюллетеня по Рынку драгоценных металлов."""
    metal_check = requests.head(metal_link, verify=False)
    if metal_check.status_code == HTTPStatus.OK:
        metal_status = 'Ok'
    else:
        metal_status = 'False'
    return metal_status


def links_check(currency_status, metal_status):
    """Возвращаем итоговый результат проверок всех ссылок"""
    if currency_status == 'Ok' and metal_status == 'Ok':
        links_status = 'Ready'
    else:
        links_status = 'False'
    return links_status


def get_currency_bulletin(currency_link):
    """Проверяем содержание бюллетеня по Валютному рынку."""
    request = Request(currency_link, headers={})
    remote_file = urlopen(request).read()
    remote_file_bytes = io.BytesIO(remote_file)
    pdfdoc_remote = PdfReader(remote_file_bytes, strict=False)
    page = pdfdoc_remote.pages[0]
    if 'FINAL' in page.extract_text():
        currency_message = 'итоговый бюллетень по валюте - Ok'
    if f'Version: {CURRENT_HOUR + 3}' in page.extract_text():
        currency_message = 'бюллетень по валюте на 19 часов - Ok'
    return currency_message


def get_metal_bulletin(metal_link):
    """Проверяем содержание бюллетеня по Рынку драгоценных металлов."""
    request = Request(metal_link, headers={})
    remote_file = urlopen(request).read()
    remote_file_bytes = io.BytesIO(remote_file)
    pdfdoc_remote = PdfReader(remote_file_bytes, strict=False)
    page = pdfdoc_remote.pages[0]
    if 'FINAL' in page.extract_text():
        metal_message = 'итоговый бюллетень по ДМ - Ok'
    if f'Version: {CURRENT_HOUR + 3}' in page.extract_text():
        metal_message = 'бюллетень по ДМ на 19 часов - Ok'
    return metal_message


def get_message(currency_message, metal_message):
    """Формируем сообщение по итогам проверки содержания бюллетеней."""
    bot_message = (f'Проверка публикации бюллетеней на сайте'
                   f' за {CURRENT_DAY}.{CURRENT_MONTH}.{CURRENT_YEAR}:'
                   '\n'
                   f'- {currency_message};'
                   '\n'
                   f'- {metal_message}.')
    return bot_message


def send_message(bot, bot_message):
    """Отправляем сообщение в Телеграмм."""
    bot.send_message(TELEGRAM_CHAT_ID, bot_message)


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    last_message = ''
    while True:
        try:
            if CURRENT_HOUR == 16 or CURRENT_HOUR == 21:
                link_date = define_date_for_link()
                currency_link = define_currency_link(link_date)
                metal_link = define_metal_link(link_date)
                currency_status = check_currency_link(currency_link)
                metal_status = check_metal_link(metal_link)
                links_status = links_check(currency_status, metal_status)
                if links_status == 'Ready':
                    currency_message = get_currency_bulletin(currency_link)
                    metal_message = get_metal_bulletin(metal_link)
                    bot_message = get_message(currency_message, metal_message)
                    if bot_message != last_message:
                        send_message(bot, bot_message)
                        last_message = bot_message
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
