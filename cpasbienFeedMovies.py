
import csv
import json
from pathlib import Path
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import time
import glob
import os
import logging
from shutil import copy
import sqlite3
from plexapi.server import PlexServer
from selenium.webdriver.chrome.options import Options

from common_tools import check_exists_by_id, launch_browser, newBackupDB, closeAdds

#### HDRip, HDCAM, XviD-RZP, x264-RZP

# from nordvpn_connect import initialize_vpn, rotate_VPN, close_vpn_connection


def move_last_torrent_files_to_torrent_folder(torrent_path,remote_path,mac_platform):
    """ Function that will check torrent requirement and move it to the Nas folder."""
    list_of_files = glob.glob(os.path.expanduser('~')+torrent_path) # * means all if need specific format then *.csv
    file_in_downloads = max(list_of_files, key=os.path.getctime)
    file_in_downloads_without_spaces=file_in_downloads.replace(" ", "_")
    file_in_downloads_without_spaces=file_in_downloads_without_spaces.replace("(", "_")
    file_in_downloads_without_spaces=file_in_downloads_without_spaces.replace(")", "_")
    file_in_downloads_without_spaces=file_in_downloads_without_spaces.replace("'", "_")
    os.rename(file_in_downloads, file_in_downloads_without_spaces)
    if mac_platform :
        filename = file_in_downloads_without_spaces.split("/")[-1]
    else:
        filename = file_in_downloads_without_spaces.split("\\")[-1]
    logger.info("______%s______",remote_path+filename)
    if not Path(remote_path+filename).is_file():
        logger.info("nas path mounted")
        required=sqlite_is_new_torrent_requirement(filename)
        if required :
            try:
                copy(file_in_downloads_without_spaces, remote_path)
            except FileNotFoundError as exception:
                logger.error(exception)
            finally:
                os.remove(file_in_downloads_without_spaces)
            logger.info("copying done!")      
    else :
        logger.info("%s already processed.",filename)
        os.remove(file_in_downloads_without_spaces)

# Initiate the browser, to run without conf just put the driver this way: cp chromedriver /usr/local/bin
## todo add windows config##

def bot_different_pages(number_of_page, sort_used):
    """ Main Function that will download torrent from the website."""
    result=launch_browser(r'/Users/clementoudin/dev/5.4.1_0',sort_used, 'filmUrl')
    browser= result["browser"]
    mac_platform = result["macPlatform"]
    root_url = result["rootUrl"]
    offset =result["offset"]
    for i in range(number_of_page):
        url=root_url+"/"+str(i*50+offset)+sort_used
        browser.get(url)
        time.sleep(2)
        for iteration in range(1,51):
            if check_exists_by_id(browser, By.XPATH,'/html/body/div[1]/div[3]/div[2]/table/tbody/tr['+str(iteration)+']'):
                torrent_page_elem=browser.find_element(By.XPATH,'/html/body/div[1]/div[3]/div[2]/table/tbody/tr['+str(iteration)+']')
                torrent_page_elem.click()
                time.sleep(2)
                parent = browser.window_handles[0]
                browser.switch_to.window(parent)
                if check_exists_by_id(browser, By.XPATH,'//*[@id="infosficher"]/div[2]'):
                    torrent_button=browser.find_element(By.XPATH,'//*[@id="infosficher"]/div[2]')
                    torrent_button.click()
                    time.sleep(5)
                    ## todo add the else part ##
                    if mac_platform :
                        torrent_path='/Downloads/*.torrent'
                        remote_path="/Volumes/Home/torrentFeed"
                        move_last_torrent_files_to_torrent_folder(torrent_path,remote_path,mac_platform)
                        closeAdds(browser, url)
                        browser.get(url)
                        time.sleep(2)
                    else:
                        torrent_path='\\Downloads\\*.torrent'
                        remote_path='Z:\\torrentFeed'
                        move_last_torrent_files_to_torrent_folder(torrent_path,remote_path,mac_platform)
                        closeAdds(browser, url)
                        browser.get(url)
                        time.sleep(2)                 
                    time.sleep(2)
                else : 
                    logger.error("torrentButton does not exist")
            else:
                logger.error("torrent: "+'/html/body/div[1]/div[3]/div[2]/table/tbody/tr['+str(iteration)+']'+" does not exist")
    newBackupDB()

## add ways to store torrents with unknown fields maybe use plce for each pattern since LANGAGE is always first ##
def torrents_dict_for_sqlite(filename):
    """ Torrent filename pattern matching. """
    matches_platform = ["[_cpasbien.si_]_"]
    matches_langage = ["TRUEFRENCH_", "MULTI_", "VOSTFR_", "VO_"]
    matches_langage_contained_in_other_matches =["FRENCH_"]
    matches_format = [ "WEBRIP_LD_", "DVDRIP_", "HDLight_", "BluRay_", "HDTV_", "HDCAM_MD_", "HDRip_", "HDCAM_"]
    matches_format_contained_in_other_matches =["WEBRIP_"]
    matches_resolution = ["720p_", "720_", "1080p_", "1080_", "x264_", "4KLIGHT_ULTRA_HD_x265_", "XviD-RZP_", "x264-RZP_"]
    matches_resolution_contained_in_other_matches =["4KLIGHT_ULTRA_HD_"]
    bool_platform = False
    bool_langage = False
    bool_format = False
    bool_resolution = False
    media=filename
    matadata_dict = {}
    for x in matches_platform:
        if any([x in filename]):
            matadata_dict['PLATFORM'] = x
            media= filename.replace(x, '')
            bool_platform = True
    if not bool_platform:
        matadata_dict['PLATFORM'] = "UNKNOWN"
    for y in matches_langage:
        if any([y in media]):
            matadata_dict['LANGAGE'] = y
            media= media.replace(y, '')
            bool_langage = True
    for y in matches_langage_contained_in_other_matches:
        if any([y in media]):
            matadata_dict['LANGAGE'] = y
            media= media.replace(y, '')
            bool_langage = True
    if not bool_langage:
        matadata_dict['LANGAGE'] = "UNKNOWN"
    for z in matches_format:
        if any([z in media]):
            matadata_dict['FORMAT'] = z
            media= media.replace(z, '')
            bool_format = True
    for z in matches_format_contained_in_other_matches:
        if any([z in media]):
            matadata_dict['FORMAT'] = z
            media= media.replace(z, '')
            bool_format = True
    if not bool_format:
        matadata_dict['FORMAT'] = "UNKNOWN"
    for a in matches_resolution:
        if any([a in media]):
            matadata_dict['RESOLUTION'] = a
            media= media.replace(a, '')
            bool_resolution = True
    for a in matches_resolution_contained_in_other_matches:
        if any([a in media]):
            matadata_dict['RESOLUTION'] = a
            media= media.replace(a, '')
            bool_resolution = True
    if not bool_resolution:
        matadata_dict['RESOLUTION'] = "UNKNOWN"
    matadata_dict['NAME']=media.replace(media.split("_")[-1], '')
    matadata_dict['YEAR']= media.split("_")[-1].replace(".torrent", '')
    matadata_dict['ID']=matadata_dict['NAME']+matadata_dict['LANGAGE']+matadata_dict['FORMAT']
    logger.info(matadata_dict['ID'])
    return matadata_dict

## add tests ##
def sqlite_drop_and_create_torrent_table():
    """ drop and create torrent table. """
    conn = sqlite3.connect('test.db')
    table_exist=conn.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='TORRENT' ''')
    #if the count is 1, then table exists
    if table_exist.fetchone()[0]==1 : 
        conn.execute('''DROP TABLE TORRENT''')
        logger.info('Table drop.')
        ## ID = NAME+LANGAGE+FORMAT ##
        conn.execute('''CREATE TABLE TORRENT
                (ID            TEXT PRIMARY KEY NOT NULL,
                NAME           TEXT             NOT NULL,
                PLATFORM       TEXT             NOT NULL,
                LANGAGE        TEXT             NOT NULL,
                RESOLUTION     TEXT             NOT NULL,
                YEAR           TEXT             NOT NULL,
                FORMAT         TEXT);''')
        logger.info("Table created successfully")
    else :
        conn.execute('''CREATE TABLE TORRENT
                (ID            TEXT PRIMARY KEY NOT NULL,
                NAME           TEXT             NOT NULL,
                PLATFORM       TEXT             NOT NULL,
                LANGAGE        TEXT             NOT NULL,
                RESOLUTION     TEXT             NOT NULL,
                YEAR           TEXT             NOT NULL,
                FORMAT         TEXT);''')
        logger.info("Table created successfully")
    conn.commit()
    #close the connection
    conn.close()
    # sql_query = """SELECT name FROM sqlite_master WHERE type='table';"""
    # cursor=conn.execute(sql_query)
    # logger.info(cursor.fetchall())

def sqlite_create_torrent_table_if_not_exist():
    """ create torrent table if it does not exist. """
    conn = sqlite3.connect('test.db')
    table_exist=conn.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='TORRENT' ''')
    #if the count is 1, then table exists
    if table_exist.fetchone()[0]==1 : 
        logger.info("Table already exist")
    else :
        conn.execute('''CREATE TABLE TORRENT
                (ID            TEXT PRIMARY KEY NOT NULL,
                NAME           TEXT             NOT NULL,
                PLATFORM       TEXT             NOT NULL,
                LANGAGE        TEXT             NOT NULL,
                RESOLUTION     TEXT             NOT NULL,
                YEAR           TEXT             NOT NULL,
                FORMAT         TEXT);''')
        logger.info("Table created successfully")
    # sql_query = """SELECT name FROM sqlite_master WHERE type='table';"""
    # cursor=conn.execute(sql_query)
    # logger.info(cursor.fetchall())
    conn.commit()
    #close the connection
    conn.close()

def sqlite_insert_torrent_in_table(dict):
    """ insertion in torrent table. """
    conn = sqlite3.connect('test.db')
    sql = ''' INSERT INTO TORRENT (ID,NAME,PLATFORM,LANGAGE,RESOLUTION,YEAR,FORMAT) VALUES(?,?,?,?,?,?,?)'''
    row = (dict['ID'], dict['NAME'], dict['PLATFORM'], dict['LANGAGE'], dict['RESOLUTION'], dict['YEAR'], dict['FORMAT']);
    cur = conn.cursor()
    cur.execute(sql, row)
    conn.commit()
    conn.close()

def sqlite_drop_torrent_table():
    """ drop torrent table. """
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    #Doping EMPLOYEE table if already exists
    cursor.execute("DROP TABLE TORRENT")
    logger.info("Table dropped... ")
    #Commit your changes in the database
    conn.commit()
    #Closing the connection
    conn.close()

def sqlite_is_torrent_needed(metadata_dict):
    ''' Return if a torrent has to be downloaded following this logic: 

    If the LANGAGE from the torrent's dictonary put as parameter is not french --> not required 

    If the torrent is already present in TORRENT table in french and in HD --> not required

    If already present in TORRENT table in french 
    and the FORMAT from the torrent's dictonary put as parameter is not HD --> not required 

    Otherwise the torrent is required.'''
    conn = sqlite3.connect('test.db')
    already_downloaded_torrent_execute=conn.execute("SELECT LANGAGE, FORMAT, ID FROM TORRENT WHERE NAME=?", (metadata_dict['NAME'],))
    records = already_downloaded_torrent_execute.fetchall()
    print("Total rows are:  ", len(records))
    french=["TRUEFRENCH_", "FRENCH_", "MULTI_"]
    if any([x in metadata_dict['LANGAGE'] for x in french]):
        if not len(records)==0:
            for row in records:
                if( (row[0]=="TRUEFRENCH_" or row[0]=="FRENCH_" or row[0]=="MULTI_") and (row[1]=="DVDRIP_" or row[1]=="HDLight_" or row[1]=="BluRay_" or row[1]=="HDTV_")):
                    return False
            for row in records:
                if( (row[0]=="TRUEFRENCH_" or row[0]=="FRENCH_" or row[0]=="MULTI_") and (metadata_dict['FORMAT']=="DVDRIP_" or metadata_dict['FORMAT']=="HDLight_" or metadata_dict['FORMAT']=="BluRay_" or row[1]=="HDTV_")):
                    return True
                return False
        else :
            logger.info("media %s not dowloaded yet", metadata_dict['NAME']) 
            return True
        return True
    return False

## todo add parameter 
def test_new_torrent_requirement():
    ''' expected result: Required
    
    BE CAREFUL IT CURRENTLY DROP TORRENT TABLE !
    '''

    filename_to_test="[_cpasbien.si_]_Star_Wars___Episode_II_-_L_Attaque_des_clones_TRUEFRENCH_HDLight_1080_2002.torrent"
    filename_test_config1="[_cpasbien.si_]_Star_Wars___Episode_II_-_L_Attaque_des_clones_MULTI_WEBRIP_LD_1080_2002.torrent"
    filename_test_config2="[_cpasbien.si_]_Star_Wars___Episode_II_-_L_Attaque_des_clones_VOSTFR_HDLight_1080_2002.torrent" ###
    filename_test_config3="[_cpasbien.si_]_Star_Wars___Episode_II_-_L_Attaque_des_clones_FRENCH_DVDRIP_1080_2002.torrent" ###
    dict_to_test=torrents_dict_for_sqlite(filename_to_test)
    dict_test_config1=torrents_dict_for_sqlite(filename_test_config1)
    dict_test_config2=torrents_dict_for_sqlite(filename_test_config2)
    dict_test_config3=torrents_dict_for_sqlite(filename_test_config3)
    sqlite_drop_and_create_torrent_table()
    sqlite_insert_torrent_in_table(dict_test_config1)
    sqlite_insert_torrent_in_table(dict_test_config2)
    sqlite_insert_torrent_in_table(dict_test_config3)
    if sqlite_is_torrent_needed(dict_to_test):
        sqlite_insert_torrent_in_table(dict_to_test)
        logger.info("torrent %s is required and inserted to the database", dict_to_test['NAME'])
    else:
        logger.info("torrent %s is not required and not inserted to the database", dict_to_test['NAME'])
    sqlite_drop_torrent_table()

def sqlite_is_new_torrent_requirement(filename_to_test):
    """ Top level function that identify whether a torrent is required to be download 
    and add it to the torrent table. """
    dict_to_test=torrents_dict_for_sqlite(filename_to_test)
    sqlite_create_torrent_table_if_not_exist()
    if sqlite_is_torrent_needed(dict_to_test):
        sqlite_insert_torrent_in_table(dict_to_test)
        logger.info("torrent %s is required and inserted to the database", dict_to_test['NAME'])
        return True
    else:
        logger.info("torrent %s is not required and not inserted to the database", dict_to_test['NAME'])
        return False


# create console handler and set level to debug
logging.basicConfig(filename='/Volumes/Home/movies.log', encoding='utf-8', level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')
logger=logging.getLogger('CPasBienFeed')
# sqlite_drop_torrent_table()
# YOUR STUFF

# bot()
bot_different_pages(1,'')
# botDifferentPages(3,"/seeds/desc")


#sqlite()
#test_new_torrent_requirement()
# sqlite_drop_torrent_table()

#sqlite_export_torrent_table()


logger.info("finished.")