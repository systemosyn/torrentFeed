
import json
from pathlib import Path
import shutil
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import time
import os
import logging
from shutil import copy
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

#### HDRip, HDCAM, XviD-RZP, x264-RZP

# from nordvpn_connect import initialize_vpn, rotate_VPN, close_vpn_connection

def check_exists_by_id(browser, by, xpath):
    try:
        browser.find_element(by,xpath)
    except NoSuchElementException:
        return False
    return True


def newBackupDB():
    shutil.copy(os.path.join(os.path.expanduser('~'), 'dev','test.db'), os.path.expanduser('~')+'/dev/backUpTest.db')

def closeAdds(browser, url):
    while (len(browser.window_handles) != 1) :
        browser.switch_to.window(browser.window_handles[1])
        try:
            WebDriverWait(browser, 2).until(EC.alert_is_present(),
                'Timed out waiting for PA creation ' +
                'confirmation popup to appear.')
            alert = browser.switch_to.alert
            alert.accept()
            logger.info("alert accepted")
            logger.info("no alert")
            browser.close()
            parent = browser.window_handles[0]
            browser.switch_to.window(parent)
        except TimeoutException:
            logger.info("no alert")
            browser.close()
            parent = browser.window_handles[0]
            browser.switch_to.window(parent)


def launch_browser(extensionPath, sortUsed, mediaUrl):
    chrome_options = Options()
    chrome_options.add_argument('load-extension=' + extensionPath)
    browser = webdriver.Chrome(chrome_options=chrome_options)
    browser.create_options()
    offset=1
    # browser  = webdriver.Chrome(
    # Open the Website
    browser.maximize_window()
    # os.path.join(os.path.expanduser('~'), 'dev','torrentFeed','config.json') 
    with open(os.path.join(os.path.expanduser('~'), 'dev','torrentFeed','config.json')) as config_file:
        data = json.load(config_file)
    rootUrl=data[mediaUrl]
    macPlatform=data['mac']
    #numberOfRows = len(browser.find_element(By.XPATH,'/html/body/div[1]/div[3]/div[2]/table/tbody'))
    #rows = browser.find_elements(By.XPATH("/html/body/div[1]/div[3]/div[2]/table/tbody"))
    ## todo add all the xpath in config ##
    ## todo add the loop to iterate into all the torrents --> DONE##
    url=rootUrl+"/"+str(offset)+sortUsed
    browser.get(url)
    time.sleep(10)
    closeAdds(browser, url)
    result = {}
    result["browser"]= browser
    result["macPlatform"]= macPlatform
    result["rootUrl"]=rootUrl
    result["url"]=url
    result["offset"]=offset
    return result
    

### todo: export table in csv https://gist.github.com/shitalmule04/82d2091e2f43cb63029500b56ab7a8cc ##
logger = logging.getLogger('cpasbienFeed')
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)
# sqlite_drop_torrent_table()
