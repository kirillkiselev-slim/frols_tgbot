import datetime
import logging
import re
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

A7_list = []

RETRY_PERIOD = 300

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

def set_filter_website(driver, website):
    time.sleep(1)
    driver.get(website)
    driver.maximize_window()
    wait = WebDriverWait(driver, 25)

    audi = wait.until(EC.visibility_of_element_located((
        By.XPATH, elements['audi_link'])))
    audi.click()
    time.sleep(2)

    audi_a7 = wait.until(EC.visibility_of_element_located((
        By.XPATH, elements['a7_audi'])))
    audi_a7.click()
    time.sleep(2)
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
    month1.select_by_value('1')

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

    time.sleep(2)
    wait.until(EC.element_to_be_clickable((
        By.XPATH, elements['diesel_electric']
    ))).click()
    time.sleep(2)
    wait.until(EC.element_to_be_clickable((
        By.XPATH, elements['gasoline_electric']
    ))).click()
    time.sleep(2)
    wait.until(EC.element_to_be_clickable((
        By.XPATH, elements['diesel']
    ))).click()
    time.sleep(2)

    # page_row = wait.until(EC.element_to_be_clickable((
    #     By.ID, 'pagerow'
    # )))
    # select_cars_on_page = Select(page_row)
    # select_cars_on_page.select_by_value('50')
    # time.sleep(2)

    # TODO add alert text exception - UnexpectedAlertPresentException


def get_last_page(driver):
    wait = WebDriverWait(driver, 25)
    wait.until(EC.visibility_of_element_located((
        By.ID, 'pagination')))
    time.sleep(2)
    page_elements = wait.until(EC.visibility_of_all_elements_located((
        By.CLASS_NAME, 'page')))
    last_page_element = page_elements[-1]
    time.sleep(2)
    last_page = int(last_page_element.find_element(
        By.TAG_NAME, 'a').get_attribute('data-page'))
    print("Last page number:", last_page)
    return last_page


def get_car_ids(car_links):
    hrefs = [car.get_attribute('href') for car in car_links]
    pattern = r'carid=(\d+)&'
    car_ids = [re.search(pattern, href).group(1) for href in hrefs
               if re.search(pattern, href)]
    return car_ids


def parse_cars(driver):
    time_before = datetime.datetime.now()

    wait = WebDriverWait(driver, 25)
    set_filter_website(driver=driver, website=WEBSITE)
    last_page = get_last_page(driver=driver)
    all_car_ids = []

    for page in range(1, last_page + 1):
        list_of_cars = wait.until(EC.visibility_of_element_located((By.ID, 'sr_normal')))
        car_links = list_of_cars.find_elements(By.TAG_NAME, 'a')

        car_ids = get_car_ids(car_links=car_links)
        all_car_ids.extend(car_ids)

        if page < last_page:
            next_page_element = wait.until(
                EC.element_to_be_clickable((By.XPATH, f'//a[@data-page="{page + 1}"]')))
            next_page_element.click()

            time.sleep(2)

    time_after = datetime.datetime.now()

    print(f'Time taken to extract information:'
          f' {(time_after - time_before).total_seconds()} seconds')
    print(f'Original list: {len(all_car_ids)};'
          f' List with deleted duplicates: {len(set(all_car_ids))}')
    return set(all_car_ids)


def main():
    new_car_links = f'http://www.encar.com/dc/dc_cardetailview.do&carid={...}'
    a7_parser = parse_cars(driver=open_and_start_multilogin_profile())


main()