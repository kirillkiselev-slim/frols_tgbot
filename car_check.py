import datetime
import logging
import re
from typing import List, Set
import os
import sys
import time
from logging.handlers import RotatingFileHandler
import multiprocessing as mp

import psutil
import requests
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (UnexpectedAlertPresentException,
                                        TimeoutException)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
import telegram
from dotenv import load_dotenv
from telegram.error import TelegramError

from multilogin import Mlx
from exceptions import (
    TokensNotPresentError,
    TelegramConnectionError,
    WebsiteIsNotAvailableError
)

from check_tokens import (
    check_each_token
)
from site_elements import elements

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

WEBSITE = 'http://www.encar.com/fc/fc_carsearchlist.do'
CAR_LINK = 'http://www.encar.com/dc/dc_cardetailview.do&carid='
RETRY_PERIOD = 60
MAIN_MESSAGE = 'Нашли новые машины! Ура! Вот список ссылок: '

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
handler = RotatingFileHandler(
    'monitor_cars.logs', maxBytes=50000000, backupCount=5,
)
logger.addHandler(handler)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)


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


def start_multilogin_profile():
    mlx = Mlx(email=os.getenv('MLX_EMAIL'), password=os.getenv('MLX_PASS'))
    mlx.signin()
    quick_profile_port = mlx.start_quick_profile(browser_type='stealthfox')
    time.sleep(60)
    driver = mlx.instantiate_driver(profile_port=quick_profile_port[1])
    return driver


def stop_profiles():
    mlx = Mlx(email=os.getenv('MLX_EMAIL'), password=os.getenv('MLX_PASS'))
    mlx.signin()
    mlx.stop_all_profiles()


def log_system_usage():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    memory_usage_mb = memory_info.used / (1024 ** 2)
    logger.debug(f'CPU Usage: {cpu_usage}%')
    logger.debug(f'Memory Usage: {memory_usage_mb:.2f} MB')


def set_filters_on_website(driver, website, model=None):
    try:
        wait = WebDriverWait(driver, 35)

        time.sleep(1)

        response = requests.get(website)
        if response.status_code != 200:
            raise WebsiteIsNotAvailableError(
                f'{website} website is not available!\n'
                f'Код ответа сайта: "{response.status_code}"\n'
                f'Адрес запроса: {response.url}'
            )

        driver.get(website)

        audi = wait.until(EC.visibility_of_element_located((
            By.XPATH, elements['audi_link'])))
        audi.click()
        time.sleep(2)

        if model == 'a7':
            audi_a7 = wait.until(EC.visibility_of_element_located((
                By.XPATH, elements['a7_audi'])))
            audi_a7.click()
        else:
            audi_a5 = wait.until(EC.visibility_of_element_located((
                By.XPATH, elements['a5_audi'])))
            audi_a5.click()

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

        if model != 'a5':
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

        page_row = wait.until(EC.element_to_be_clickable((
            By.ID, 'pagerow'
        )))
        select_cars_on_page = Select(page_row)
        select_cars_on_page.select_by_value('50')
        time.sleep(2)

    except UnexpectedAlertPresentException:
        logger.exception(msg='Алерт был вызван на вебсайте и не получилось'
                         'пропарсить информацию.')

    except TimeoutException:
        logger.exception(msg='Не найдены элементы на странице.')


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
    return last_page


def get_car_ids(car_links: List) -> List:
    hrefs = [car.get_attribute('href') for car in car_links]
    pattern = r'carid=(\d+)&'
    car_ids = [re.search(pattern, href).group(1) for href in hrefs
               if re.search(pattern, href)]
    return car_ids


def parse_cars(driver, model=None):
    time_before = datetime.datetime.now()

    wait = WebDriverWait(driver, 25)

    set_filters_on_website(driver, WEBSITE, model)
    last_page = get_last_page(driver=driver)

    all_car_ids = []

    for page in range(1, last_page + 1):
        list_of_cars = wait.until(EC.visibility_of_element_located((
            By.ID, 'sr_normal')))
        car_links = list_of_cars.find_elements(By.TAG_NAME, 'a')

        car_ids = get_car_ids(car_links=car_links)
        all_car_ids.extend(car_ids)

        if page < last_page:
            next_page_element = wait.until(
                EC.element_to_be_clickable((By.XPATH, f'//a[@data-page="{page + 1}"]')))
            next_page_element.click()
            time.sleep(2)

    time_after = datetime.datetime.now()

    distinct_car_ids = set(all_car_ids)

    logger.debug(f'Time taken to extract information of Audi {model.upper()}:'
                 f' {(time_after - time_before).total_seconds():.2f} seconds')
    logger.debug(f'Quantity of Audi {model.upper()}: '
                 f'{len(distinct_car_ids)}')
    return distinct_car_ids


def parse_cars_multiprocess(model: str) -> Set:
    driver = start_multilogin_profile()
    car_ids = parse_cars(driver, model)
    driver.quit()
    return car_ids


def main():
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    parser_before = None
    error_message_not_sent = True
    audi_models = ('a7', 'a5')

    while True:
        try:
            with mp.Pool(processes=len(audi_models)) as pool:
                results = pool.map(parse_cars_multiprocess, audi_models)

            parser_after = sorted([car_id for result in
                                   results for car_id in result])

            if parser_before is not None:
                if parser_before == parser_after:
                    log_system_usage()
                    continue

                new_car_links = [f'{CAR_LINK}{car}' for car in parser_after if
                                 car not in parser_before]
                new_links = '\n'.join(new_car_links)
                log_system_usage()
                logger.debug(msg='Нашли новые машины!')
                message = f'{MAIN_MESSAGE} \U0001F389\n{new_links}'
                send_message(bot, message)

            log_system_usage()
            parser_before = parser_after

        except Exception as e:
            logger.exception(e)
            if error_message_not_sent:
                send_message(bot, '\U0001F198' + str(e))
                error_message_not_sent = False

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
