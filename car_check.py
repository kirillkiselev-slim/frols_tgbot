import logging
from typing import Mapping, List
import os
import sys
import time
from logging.handlers import RotatingFileHandler
from http import HTTPStatus

import requests
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chromium.options import ChromiumOptions
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
import telegram
from dotenv import load_dotenv
from telegram.error import TelegramError

from multilogin import Mlx
from exceptions import (
    EndpointConnectionError,
    TokensNotPresentError,
    TelegramConnectionError,
)

from check_tokens import (
    check_each_token
)
from site_elements import elements

WEBSITE = 'http://www.encar.com/fc/fc_carsearchlist.do'

load_dotenv()

logger = logging.getLogger(__name__)

logger.setLevel(level=logging.DEBUG)

handler = RotatingFileHandler(
    'monitor_cars.logs', maxBytes=50000000, backupCount=5,
)
logger.addHandler(handler)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


def check_tokens():
    """Проверяет наличие необходимых токенов."""
    try:
        check_each_token((TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))
    except TokensNotPresentError as err:
        logger.critical(err)
        sys.exit()


def send_message(bot, message):
    """Отправляет сообщение через бота в чат Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except TelegramError as err:
        raise TelegramConnectionError('Ошибка подключения к'
                                      ' Телеграм') from err

    logger.debug(f'Сообщение отправлено: {message}')


def open_and_start_multilogin_profile():
    mlx = Mlx(email=os.getenv('MLX_EMAIL'), password=os.getenv('MLX_PASS'))
    mlx.signin()
    quick_profile_port = mlx.start_quick_profile()
    driver = mlx.instantiate_driver(profile_port=quick_profile_port[1])
    return driver


# def filter_website(driver, website):
#     options = Options()
#     prefs = {
#         "translate_whitelists": {"ko": "en"},
#         "translate": {"enabled": "true"}
#     }
#     options.add_experimental_option("prefs", prefs)

def filter_website(driver, website):
    time.sleep(1)
    driver.get(website)
    wait = WebDriverWait(driver, 10)

    dd_element1 = wait.until(EC.visibility_of_element_located((
        By.XPATH, elements['audi_link'])))
    dd_element1.click()

    dd_element2 = wait.until(EC.element_to_be_clickable((
        By.XPATH, elements['a7_audi'])))
    dd_element2.click()

    date = wait.until(EC.visibility_of_element_located((
        By.XPATH, '//a[@data-enlog-dt-eventnamegroup="필터" and text()="연식"]'
    )))
    driver.execute_script("arguments[0].scrollIntoView(true);", date)

    driver.execute_script("arguments[0].click();", date)

    year_from = wait.until(EC.visibility_of_element_located((
        By.CLASS_NAME, 'from')))
    select_year1 = year_from.find_element(By.TAG_NAME, 'select')
    year1 = Select(select_year1)
    year1.select_by_value('2020')

    time.sleep(2)
    select_month1 = wait.until(EC.visibility_of_element_located((
        By.CLASS_NAME, 'month')))
    month1 = Select(select_month1)
    month1.select_by_value('2')

    time.sleep(2)
    year_to = wait.until(EC.visibility_of_element_located((
        By.CLASS_NAME, 'to')))
    select_year2 = year_to.find_element(By.TAG_NAME, 'select')
    year2 = Select(select_year2)
    year2.select_by_value('2022')

    time.sleep(2)

    fuel = wait.until(EC.element_to_be_clickable((
        By.XPATH, elements['fuel']
    )))
    driver.execute_script("arguments[0].scrollIntoView(true);", fuel)

    driver.execute_script("arguments[0].click();", fuel)

    time.sleep(1)
    wait.until(EC.element_to_be_clickable((
        By.XPATH, elements['diesel_electric']
    ))).click()
    time.sleep(1)
    wait.until(EC.element_to_be_clickable((
        By.XPATH, elements['gasoline_electric']
    ))).click()
    time.sleep(1)
    wait.until(EC.element_to_be_clickable((
        By.XPATH, elements['diesel']
    ))).click()


filter_website(open_and_start_multilogin_profile(), WEBSITE)

# filter_website(WEBSITE)


