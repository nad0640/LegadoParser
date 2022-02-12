import os
import subprocess
import sys
import base64
import logging
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.webdriver import WebDriver
from LegadoParser2.config import DEBUG_MODE, USER_AGENT
_driver = None


class WebView(object):
    def __init__(self, userAgent=USER_AGENT):
        if userAgent != USER_AGENT:
            self.driver = getDriverInstance(userAgent)
        elif not self.driver:
            self.driver = getDriverInstance()

    @property
    def driver(self) -> WebDriver:
        global _driver
        return _driver

    @driver.setter
    def driver(self, value):
        global _driver
        _driver = value

    def getResponseByUrl(self, url, javaScript=''):
        # 定义 navigator.platform 为空
        # https://stackoverflow.com/questions/38808968/change-navigator-platform-on-chrome-firefox-or-ie-to-test-os-detection-code
        # 在页面加载前执行Js
        # https://stackoverflow.com/questions/31354352/selenium-how-to-inject-execute-a-javascript-in-to-a-page-before-loading-executi
        # https://developer.mozilla.org/zh-CN/docs/Web/JavaScript/Reference/Global_Objects/Object/defineProperty
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                                    'source': "Object.defineProperty(navigator,'platform',{value:''})"})
        self.driver.get(url)
        # 平滑滚动到底
        self.driver.execute_script(
            "window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
        # time.sleep(0.7)
        if javaScript:
            return self.driver.execute_script(javaScript)
        else:
            return self.driver.page_source

    def getResponseByHtml(self, html, javaScript=''):
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                                    'source': "Object.defineProperty(navigator,'platform',{value:''})"})
        # https://stackoverflow.com/questions/22538457/put-a-string-with-html-javascript-into-selenium-webdriver
        html_bs64 = base64.b64encode(html.encode('utf-8')).decode()
        self.driver.get("data:text/html;base64," + html_bs64)
        self.driver.execute_script(
            "window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
        time.sleep(0.7)
        if javaScript:
            return self.driver.execute_script(javaScript)
        else:
            return self.driver.page_source


def getDriverInstance(userAgent=USER_AGENT):
    chromePath = getChromePath()
    if sys.platform == 'win32' and chromePath:
        user_data_dir = os.path.join(os.path.abspath("."), 'webview\AutomationProfile')

        if DEBUG_MODE:
            subprocess.Popen(
                f'cmd /c ""{chromePath}" --remote-debugging-port=9222 --user-data-dir="{user_data_dir}" --lang=zh-CN --mute-audio --user-agent="{userAgent}""')
        else:
            subprocess.Popen(
                f'cmd /c ""{chromePath}" --remote-debugging-port=9222 --user-data-dir="{user_data_dir}" --lang=zh-CN --headless --disable-gpu --mute-audio --user-agent="{userAgent}""')
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        options.set_capability("detach", True)
        service = Service(executable_path=ChromeDriverManager(log_level=logging.NOTSET).install())
        driver = webdriver.Chrome(service=service, options=options)
    else:
        options = webdriver.ChromeOptions()
        options.set_capability("detach", True)
        if not DEBUG_MODE:
            options.headless = True
        options.add_argument("--mute-audio")
        options.add_argument("--headless")
        # 去除webdriver痕迹
        # https://zhuanlan.zhihu.com/p/328768200
        options.add_argument("disable-blink-features=AutomationControlled")
        options.add_argument(f"user-agent={userAgent}")
        service = Service(executable_path=ChromeDriverManager(log_level=logging.NOTSET).install())
        driver = webdriver.Chrome(service=service, options=options)
    return driver


def getChromePath():
    if sys.platform == 'win32':
        chromePath = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(chromePath):
            chromePath = r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
        if not os.path.exists(chromePath):
            chromePath = ""
    else:
        chromePath = ""
    return chromePath
