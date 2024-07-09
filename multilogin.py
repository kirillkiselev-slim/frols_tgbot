import requests
import time
import random
import hashlib
from selenium import webdriver
from selenium.webdriver.chromium.options import ChromiumOptions
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains as Ac


class Mlx:

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.token = None
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def signin(self) -> str:
        url = "https://api.multilogin.com/user/signin"
        payload = {
            "email": self.email,
            "password": hashlib.md5(self.password.encode()).hexdigest()
        }
        r = requests.post(url=url, headers=self.headers, json=payload)
        if r.status_code != 200:
            print("Wrong credentials")
        else:
            json_response = r.json()
            self.token = json_response['data']['token']
            self.headers.update({"Authorization": f"Bearer {self.token}"})
            return self.token

    def start_quick_profile(self, browser_type="mimic"):
        payload = {
            "browser_type": browser_type,
            "os_type": "windows",
            "is_headless": True,
            "automation": "selenium",
            "parameters": {
                "fingerprint": {
                    "localization": {
                        "languages": "en-US",
                        "locale": "en-US",
                        "accept_languages": "en-US,en;q=0.5"
                    },
                    # "cmd_params":
                    #     {
                    #     "params": [
                    #         {
                    #             "flag": "--lang",
                    #             "value": "en"
                    #         },
                    #         {
                    #             "flag": "--intl.accept_languages",
                    #             "value": "en-US"
                    #         }
                    #    ]
                    # }
                },
                "flags": {
                    "audio_masking": "mask",
                    "fonts_masking": "mask",
                    "geolocation_masking": "mask",
                    "geolocation_popup": "prompt",
                    "graphics_masking": "mask",
                    "graphics_noise": "mask",
                    "localization_masking": "mask",
                    "media_devices_masking": "mask",
                    "navigator_masking": "mask",
                    "ports_masking": "mask",
                    "proxy_masking": "disabled",
                    "screen_masking": "mask",
                    "timezone_masking": "mask",
                    "webrtc_masking": "mask"
                }
            }
        }
        try:
            response = requests.post(url="https://launcher.mlx.yt:45001/api/v2/profile/quick", headers=self.headers,
                                     json=payload)
            data = response.json()
            if data['status']['http_code'] != 200:
                message = data['status']['message']
                return None, None, False, message
            else:
                quick_profile_id = data['data']['id']
                quick_profile_port = data['data']['port']
                profile_started = True
                message = data['status']['message']
                return quick_profile_id, quick_profile_port, profile_started, message
        except Exception as e:
            return None, None, False, str(e)

    def start_normal_profile(self, profile_id: str, folder_id: str):
        url = f"https://launcher.mlx.yt:45001/api/v2/profile/f/{folder_id}/p/{profile_id}/start?automation_type=selenium&headless_mode=false"
        response = requests.get(url=url, headers=self.headers)
        if response.status_code != 200:
            message = response.json()['status']['message']
            profile_port = False
            profile_started = False
            print(f"Error at starting profile: {message}")
            return profile_id, profile_port, profile_started, message
        else:
            profile_port = response.json()['data']['port']
            message = response.json()['status']['message']
            profile_started = True
            return profile_id, profile_port, profile_started, message

    def stop_profile(self, profile_id: str):
        url = f"https://launcher.mlx.yt:45001/api/v1/profile/stop/p/{profile_id}"
        r = requests.get(url=url, headers=self.headers)
        if r.status_code != 200:
            print("Can't stop profile")
        else:
            print("Profile stopped")

    def instantiate_driver(self, profile_port: str, browser_type="mimic") -> webdriver:
        if browser_type == 'mimic':
            driver = webdriver.Remote(command_executor=f"http://127.0.0.1:{profile_port}", options=ChromiumOptions())
        elif browser_type == 'stealthfox':
            driver = webdriver.Remote(command_executor=f"http://127.0.0.1:{profile_port}", options=Options())
        return driver

    def get_proxy_details(self, mapped_account, token=None) -> dict:

        if token == None:
            self.token = self.signin()

        self.headers.update({
            "Authorization": f"Bearer {self.token}"
        })
        url = "https://profile-proxy.multilogin.com/v1/proxy/connection_url"
        payload = {
            "country": mapped_account['country_code'],
            "region": mapped_account['region'],
            "city": mapped_account['city'],
            "protocol": "socks5",
            "sessionType": "sticky",
            "IPTTL": 0
        }
        response = requests.post(url=url, headers=self.headers, json=payload)
        if response.status_code != 201:
            print(f"Could not get proxy session: {response.status_code}")
        else:
            session = response.json()['data'].split(':')
            proxy_details = {
                "host": session[0],
                "port": session[1],
                "username": session[2],
                "password": session[3]
            }
            return proxy_details

    def create_profile(self, proxy_details, profile_details, FOLDER_ID):

        if self.token == None:
            self.token = self.signin()

        self.headers.update({
            "Authorization": f"Bearer {self.token}"
        })

        payload = {
            "name": f"{profile_details['first_name']} {profile_details['last_name']}",
            "folder_id": FOLDER_ID,
            "browser_type": "mimic",
            "os_type": "linux",
            "is_headless": False,
            "proxy": {
                "host": proxy_details['host'],
                "type": "socks5",
                "port": proxy_details['port'],
                "username": proxy_details['username'],
                "password": proxy_details['password']
            },
            "parameters": {
                "fingerprint": {
                    "cmd_params": {
                        "params": [
                            {
                                "flag": "disable-notifications",
                                "value": "true"
                            }
                        ]
                    }
                },
                "flags": {
                    "audio_masking": "natural",
                    "fonts_masking": "mask",
                    "geolocation_masking": "mask",
                    "geolocation_popup": "allow",
                    "graphics_masking": "natural",
                    "graphics_noise": "natural",
                    "localization_masking": "mask",
                    "media_devices_masking": "natural",
                    "navigator_masking": "mask",
                    "ports_masking": "natural",
                    "proxy_masking": "custom",
                    "screen_masking": "natural",
                    "timezone_masking": "mask",
                    "webrtc_masking": "mask"
                },
                "storage": {
                    "is_local": False,
                    "save_service_worker": False
                }
            }
        }
        url = "https://api.multilogin.com/profile/create"
        response = requests.post(url=url, headers=self.headers, json=payload)
        if response.status_code != 201:
            print(f"Could not create profile: Error {response.status_code}")
            return None, None, None
        else:
            profile_id = response.json()['data']['ids'][0]
            created = True
            return profile_id, FOLDER_ID, created

    def stop_all_profiles(self):
        requests.get(url="https://launcher.mlx.yt:45001/api/v1/profile/stop_all?type=quick",
                     headers=self.headers)


class CookieRobot:

    def __init__(self, email_address: str, password: str, \
                 websites: list, profile_id=None, \
                 folder_id=None, \
                 profile_type="quick"):

        self.profile_type = profile_type
        self.folder_id = folder_id
        self.websites = websites
        self.profile_id = profile_id
        self.mlx = Mlx(email_address, password)

    def automation(self):
        try:
            for website in self.websites:
                domain = website.split('//')[1] \
                    .split('/')[0] \
                    .split('.')[0]
                cookie_counter = 0
                self.driver.get(website)
                while cookie_counter < 15:
                    current_page = self.driver.current_url
                    # Watch Youtube videos
                    if "watch?" in current_page:
                        time.sleep(random.randrange(120, 240))
                    # Watch "Shorts" videos on Youtube
                    elif "shorts" in current_page:
                        time.sleep(random.randrange(60, 90))
                    self.scroll_randomly(random.randint(1, 5))
                    link_elements = self.driver.find_elements(By.TAG_NAME, "a")
                    elements_with_domain = []
                    for element in link_elements:
                        element_url = element.get_attribute('href')
                        if element_url == None:
                            continue
                        if domain in element_url:
                            elements_with_domain.append(element)
                    random_link = random.choice(elements_with_domain)
                    try:
                        Ac(self.driver). \
                            move_to_element(random_link). \
                            pause(5). \
                            click(). \
                            perform()
                        cookie_counter += 1
                    except:
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView(true); arguments[0].click();",
                                                       random_link)
                            cookie_counter += 1
                        except:
                            continue
                    finally:
                        time.sleep(random.randint(3, 5))
        except Exception as e:
            print(f"Something happened: {e}")
        finally:
            # Close browser profile and quit driver
            self.driver.quit()
            self.mlx.stop_profile(self.profile_id)

    def scroll_randomly(self, times):
        for _ in range(times):
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            random_position = random.randint(0, total_height)
            self.driver.execute_script(f"window.scrollTo(0, {random_position});")
            time.sleep(random.randint(1, 5))

    def start_profile(self):
        if self.profile_type == "normal":
            try:
                profile_started = False
                while not profile_started:
                    self.profile_id, self.profile_port, profile_started, message = self.mlx. \
                        start_normal_profile(self.token, self.profile_id, self.folder_id)
                    if profile_started:
                        return
                    print(
                        f"Profile couldn't be started. Probably downloading core. Will wait for 60 seconds and try again. Here is the message: {message}")
                    time.sleep(60)
            except Exception as e:
                print(f"Problem with starting profile: {e}")

        elif self.profile_type == "quick":
            try:
                profile_started = False
                while not profile_started:
                    self.profile_id, self.profile_port, profile_started, message = self.mlx.start_quick_profile()
                    if profile_started:
                        return
                    print(
                        f"Profile couldn't be started. Probably downloading core. Will wait for 60 seconds and try again. Here is the message: {message}")
                    time.sleep(60)
            except Exception as e:
                print(f"Problem with starting profile: {e}")

    def run(self):
        self.token = self.mlx.signin()
        self.start_profile()
        self.driver = self.mlx.instantiate_driver(self.profile_port)
        self.automation()
