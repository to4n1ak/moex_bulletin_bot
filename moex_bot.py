import datetime
import io
import logging
import time
from PyPDF2 import PdfReader
from urllib.request import Request, urlopen
from logging.handlers import RotatingFileHandler

import exceptions
from telegram import Bot
from telegram.error import TelegramError

logging.basicConfig(
    level=logging.DEBUG,
    filename='program.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('my_logger.log', maxBytes=5000000, backupCount=5)
logger.addHandler(handler)


CURRENT_HOUR = datetime.datetime.now().hour  # время для проверки публикации
CURRENT_DAY = datetime.datetime.now().day  # день для адреса запроса
CURRENT_MONTH = datetime.datetime.now().month  # месяц для адреса запроса
CURRENT_YEAR = datetime.datetime.now().year  # год для адреса запроса
RETRY_TIME = 60  # время ожидания в работе основной функции main
TELEGRAM_TOKEN = '5726169661:AAHeEwMXdw33WL5suC-A87JV_42cRHJ5rc0'
TELEGRAM_CHAT_ID = 434968700


def define_date_for_link():
    """Определяем дату для включения в адрес запроса"""
    if CURRENT_HOUR >= 19 and CURRENT_HOUR <= 23:
        link_date = f'{CURRENT_DAY}{CURRENT_MONTH}{CURRENT_YEAR}'
    else:
        link_date = f'{CURRENT_DAY - 1}{CURRENT_MONTH}{CURRENT_YEAR}'
    return link_date


def define_currency_link(link_date):
    """Определяем ссылку для бюллетеня по Валютному рынку."""
    currency_link = f'https://iss.moex.com/file/Currency_{link_date}.pdf'
    return currency_link


def define_metal_link(link_date):
    """Определяем ссылку для бюллетеня по Рынку драгоценных металлов."""
    metal_link = f'https://iss.moex.com/file/Metal_{link_date}.pdf'
    return metal_link


def define_otccu_link(link_date):
    """Определяем ссылку для бюллетеня по Рынку OTC."""
    otccu_link = f'https://iss.moex.com/file/OtcCu_{link_date}.pdf'
    return otccu_link


def date_for_message():
    """Определяем дату для включения в текст сообщения"""
    if CURRENT_HOUR >= 19 and CURRENT_HOUR <= 23:
        message_date = f'{CURRENT_DAY}.{CURRENT_MONTH}.{CURRENT_YEAR}'
    else:
        message_date = f'{CURRENT_DAY - 1}.{CURRENT_MONTH}.{CURRENT_YEAR}'
    return message_date


def get_currency_bulletin(currency_link):
    """Проверяем содержание бюллетеня по Валютному рынку."""
    request = Request(currency_link, headers={})
    remote_file = urlopen(request).read()
    remote_file_bytes = io.BytesIO(remote_file)
    pdfdoc_remote = PdfReader(remote_file_bytes, strict=False)
    page = pdfdoc_remote.pages[0]
    try:
        if 'FINAL' in page.extract_text():
            currency_message = 'итоговый бюллетень по валюте - Ok'
        elif f'Version: {CURRENT_HOUR}' in page.extract_text():
            currency_message = 'бюллетень по валюте на 19 часов - Ok'
    except Exception as error:
        raise Exception(f'Ошибка запроса: {error}')
    return currency_message


def get_metal_bulletin(metal_link):
    """Проверяем содержание бюллетеня по Рынку драгоценных металлов."""
    request = Request(metal_link, headers={})
    remote_file = urlopen(request).read()
    remote_file_bytes = io.BytesIO(remote_file)
    pdfdoc_remote = PdfReader(remote_file_bytes, strict=False)
    page = pdfdoc_remote.pages[0]
    try:
        if 'FINAL' in page.extract_text():
            metal_message = 'итоговый бюллетень по ДМ - Ok'
        elif f'Version: {CURRENT_HOUR}' in page.extract_text():
            metal_message = 'бюллетень по ДМ на 19 часов - Ok'
    except Exception as error:
        raise Exception(f'Ошибка запроса: {error}')
    return metal_message


def get_otccu_bulletin(otccu_link):
    """Проверяем содержание бюллетеня по Рынку OTC."""
    request = Request(otccu_link, headers={})
    remote_file = urlopen(request).read()
    remote_file_bytes = io.BytesIO(remote_file)
    pdfdoc_remote = PdfReader(remote_file_bytes, strict=False)
    page = pdfdoc_remote.pages[0]
    try:
        if (f'{CURRENT_DAY - 1}.{CURRENT_MONTH}.'
            f'{CURRENT_YEAR}') in page.extract_text():
            otccu_message = 'итоговый бюллетень по OTC - Ok'
        elif (f'{CURRENT_DAY - 1}.{CURRENT_MONTH}.'
              f'{CURRENT_YEAR}') not in page.extract_text():
            otccu_message = 'итоговый бюллетень по OTC не опубликован'
    except Exception as error:
        raise Exception(f'Ошибка запроса: {error}')
    return otccu_message


def get_message(currency_message, metal_message, otccu_message, message_date):
    """Формируем сообщение по итогам проверки бюллетеней."""
    if CURRENT_HOUR >= 19 and CURRENT_HOUR <= 23:
        bot_message = (f'Проверка публикации бюллетеней на сайте'
                       f' за {message_date}:'
                       '\n'
                       f'- {currency_message};'
                       '\n'
                       f'- {metal_message}.')
    else:
        bot_message = (f'Проверка публикации бюллетеней на сайте'
                       f' за {message_date}:'
                       '\n'
                       f'- {currency_message};'
                       '\n'
                       f'- {metal_message};'
                       '\n'
                       f'- {otccu_message}.')
    return bot_message


def send_message(bot, bot_message):
    """Отправляем сообщение в Телеграмм."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, bot_message)
    except TelegramError as error:
        raise exceptions.SendMessageError(
            f'Ошибка при отправке сообщения в Телеграмм: {error}'
        )


def main():
    """Основная функция для работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    last_message = ''

    while True:
        try:
            link_date = define_date_for_link()
            currency_link = define_currency_link(link_date)
            metal_link = define_metal_link(link_date)
            otccu_link = define_otccu_link(link_date)
            currency_message = get_currency_bulletin(currency_link)
            metal_message = get_metal_bulletin(metal_link)
            otccu_message = get_otccu_bulletin(otccu_link)
            message_date = date_for_message()
            bot_message = get_message(currency_message, metal_message,
                                      otccu_message, message_date)
            if bot_message != last_message:
                send_message(bot, bot_message)
                logger.info(f'Отправлено сообщение {bot_message}')
            else:
                logger.debug('Сообщение для отправки не сформировано')
        except Exception as error:
            raise Exception(f'Сбой в работе программы {error}')
        finally:
            last_message = bot_message
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
