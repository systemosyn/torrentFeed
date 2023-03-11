
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


def move_last_torrent_files_to_torrent_folder(path):
    list_of_files = glob.glob(os.path.expanduser('~')+'/Downloads/*.torrent') # * means all if need specific format then *.csv
    fileInDownloads = max(list_of_files, key=os.path.getctime)
    fileInDownloadsWithoutSpaces=fileInDownloads.replace(" ", "_")
    fileInDownloadsWithoutSpaces=fileInDownloadsWithoutSpaces.replace("(", "_")
    fileInDownloadsWithoutSpaces=fileInDownloadsWithoutSpaces.replace(")", "_")
    fileInDownloadsWithoutSpaces=fileInDownloadsWithoutSpaces.replace("'", "_")
    os.rename(fileInDownloads, fileInDownloadsWithoutSpaces)
    filename = fileInDownloadsWithoutSpaces.split("/")[-1]
    logger.info("______"+path+filename+"______")
    if not Path(path+filename).is_file():
        #os.system("mv "+fileInDownloadsWithoutSpaces+" "+targetFolder)
        # if not os.path.ismount("/Volumes/Home/torrentFeed"):
        if not os.path.ismount(os.path.expanduser('~')+"/dev/mnt/torrentFeed"):
            logger.error("not yet, mounted...")
            #os.system("mount /home/dat/mnt")

        else:
            logger.info("nas path mounted")
            required=sqlite_is_new_torrent_requirement(filename)
            if required :
                try:
                    copy(fileInDownloadsWithoutSpaces, os.path.expanduser('~')+"/dev/mnt/torrentFeed/")
                except FileNotFoundError as e:
                    logger.error(e)
                finally:
                    os.remove(fileInDownloadsWithoutSpaces)
                logger.info("copying done!")
            
    else :
        logger.info(filename+" already processed.")
        os.remove(fileInDownloadsWithoutSpaces)

# Initiate the browser, to run without conf just put the driver this way: cp chromedriver /usr/local/bin
## todo add windows config##

def botDifferentPages(numberOfPage, sortUsed):
    result=launch_browser(r'/Users/clementoudin/dev/5.4.1_0',sortUsed, 'filmUrl')
    browser= result["browser"]
    macPlatform = result["macPlatform"]
    rootUrl = result["rootUrl"]
    offset =result["offset"]
    for i in range(numberOfPage):
        url=rootUrl+"/"+str(i*50+offset)+sortUsed
        browser.get(url)
        time.sleep(2)
        for iteration in range(1,51):
            if check_exists_by_id(browser, By.XPATH,'/html/body/div[1]/div[3]/div[2]/table/tbody/tr['+str(iteration)+']'):
                torrentPageElem=browser.find_element(By.XPATH,'/html/body/div[1]/div[3]/div[2]/table/tbody/tr['+str(iteration)+']')
                torrentPageElem.click()
                time.sleep(2)
                parent = browser.window_handles[0]
                browser.switch_to.window(parent)
                if check_exists_by_id(browser, By.XPATH,'//*[@id="infosficher"]/div[2]'):
                    torrentButton=browser.find_element(By.XPATH,'//*[@id="infosficher"]/div[2]')
                    torrentButton.click()
                    time.sleep(5)
                    ## todo add the else part ##
                    if macPlatform :
                        move_last_torrent_files_to_torrent_folder(os.path.expanduser('~')+'/dev/mnt/torrentFeed/')
                        closeAdds(browser, url)
                        time.sleep(2)
                        browser.get(url)
                else : 
                    logger.error("torrentButton does not exist")
            else:
                logger.error("torrent: "+'/html/body/div[1]/div[3]/div[2]/table/tbody/tr['+str(iteration)+']'+" does not exist")
    newBackupDB()

## add ways to store torrents with unknown fields maybe use plce for each pattern since LANGAGE is always first ##
def torrents_dict_for_SQLite(filename):
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
    dict = {}
    ## todo: add else clause ##
    for x in matches_platform:
        if any([x in filename]):
            dict['PLATFORM'] = x
            media= filename.replace(x, '')
            bool_platform = True
    if not bool_platform:
        dict['PLATFORM'] = "UNKNOWN"
    for y in matches_langage:
        if any([y in media]):
            dict['LANGAGE'] = y
            media= media.replace(y, '')
            bool_langage = True
    for y in matches_langage_contained_in_other_matches:
        if any([y in media]):
            dict['LANGAGE'] = y
            media= media.replace(y, '')
            bool_langage = True
    if not bool_langage:
        dict['LANGAGE'] = "UNKNOWN"
    for z in matches_format:
        if any([z in media]):
            dict['FORMAT'] = z
            media= media.replace(z, '')
            bool_format = True
    for z in matches_format_contained_in_other_matches:
        if any([z in media]):
            dict['FORMAT'] = z
            media= media.replace(z, '')
            bool_format = True
    if not bool_format:
        dict['FORMAT'] = "UNKNOWN"
    for a in matches_resolution:
        if any([a in media]):
            dict['RESOLUTION'] = a
            media= media.replace(a, '')
            bool_resolution = True
    for a in matches_resolution_contained_in_other_matches:
        if any([a in media]):
            dict['RESOLUTION'] = a
            media= media.replace(a, '')
            bool_resolution = True
    if not bool_resolution:
        dict['RESOLUTION'] = "UNKNOWN"
    dict['NAME']=media.replace(media.split("_")[-1], '')
    dict['YEAR']= media.split("_")[-1].replace(".torrent", '')
    dict['ID']=dict['NAME']+dict['LANGAGE']+dict['FORMAT']
    logger.info(dict['ID'])
    return dict

## add tests ##
def sqlite_drop_and_create_torrent_table():
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
    conn = sqlite3.connect('test.db')
    sql = ''' INSERT INTO TORRENT (ID,NAME,PLATFORM,LANGAGE,RESOLUTION,YEAR,FORMAT) VALUES(?,?,?,?,?,?,?)'''
    row = (dict['ID'], dict['NAME'], dict['PLATFORM'], dict['LANGAGE'], dict['RESOLUTION'], dict['YEAR'], dict['FORMAT']);
    cur = conn.cursor()
    cur.execute(sql, row)
    conn.commit()
    conn.close()

def sqlite_drop_torrent_table():
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    #Doping EMPLOYEE table if already exists
    cursor.execute("DROP TABLE TORRENT")
    logger.info("Table dropped... ")
    #Commit your changes in the database
    conn.commit()
    #Closing the connection
    conn.close()

def sqlite_is_torrent_needed(dict):
    ''' Return if a torrent has to be downloaded following this logic: 

    If the LANGAGE from the torrent's dictonary put as parameter is not french --> not required 

    If the torrent is already present in TORRENT table in french and in HD --> not required

    If already present in TORRENT table in french and the FORMAT from the torrent's dictonary put as parameter is not HD --> not required 

    Otherwise the torrent is required.'''
    
    conn = sqlite3.connect('test.db')
    already_downloaded_torrent_execute=conn.execute("SELECT LANGAGE, FORMAT, ID FROM TORRENT WHERE NAME=?", (dict['NAME'],))
    records = already_downloaded_torrent_execute.fetchall()
    print("Total rows are:  ", len(records))
    french=["TRUEFRENCH_", "FRENCH_", "MULTI_"]
    if any([x in dict['LANGAGE'] for x in french]):
        if not len(records)==0:
            for row in records:
                if( (row[0]=="TRUEFRENCH_" or row[0]=="FRENCH_" or row[0]=="MULTI_") and (row[1]=="DVDRIP_" or row[1]=="HDLight_" or row[1]=="BluRay_" or row[1]=="HDTV_")):
                    return False
            for row in records:
                if( (row[0]=="TRUEFRENCH_" or row[0]=="FRENCH_" or row[0]=="MULTI_") and (dict['FORMAT']=="DVDRIP_" or dict['FORMAT']=="HDLight_" or dict['FORMAT']=="BluRay_" or row[1]=="HDTV_")):
                    return True
                else:
                    return False
        else :
            logger.info("media " + dict['NAME'] + " not dowloaded yet") 
            return True
        return True
    else: 
        return False

## todo add parameter 
def test_new_torrent_requirement():
    ''' expected result: Required
    
    BE CAREFUL IT CURRENTLY DROP TORRENT TABLE !
    '''

    filenameToTest="[_cpasbien.si_]_Star_Wars___Episode_II_-_L_Attaque_des_clones_TRUEFRENCH_HDLight_1080_2002.torrent"
    filenameTestConfig1="[_cpasbien.si_]_Star_Wars___Episode_II_-_L_Attaque_des_clones_MULTI_WEBRIP_LD_1080_2002.torrent"
    filenameTestConfig2="[_cpasbien.si_]_Star_Wars___Episode_II_-_L_Attaque_des_clones_VOSTFR_HDLight_1080_2002.torrent" ###
    filenameTestConfig3="[_cpasbien.si_]_Star_Wars___Episode_II_-_L_Attaque_des_clones_FRENCH_DVDRIP_1080_2002.torrent" ###
    dictToTest=torrents_dict_for_SQLite(filenameToTest)
    dictTestConfig1=torrents_dict_for_SQLite(filenameTestConfig1)
    dictTestConfig2=torrents_dict_for_SQLite(filenameTestConfig2)
    dictTestConfig3=torrents_dict_for_SQLite(filenameTestConfig3)
    sqlite_drop_and_create_torrent_table()
    sqlite_insert_torrent_in_table(dictTestConfig1)
    sqlite_insert_torrent_in_table(dictTestConfig2)
    sqlite_insert_torrent_in_table(dictTestConfig3)
    if sqlite_is_torrent_needed(dictToTest):
        sqlite_insert_torrent_in_table(dictToTest)
        logger.info("torrent "+ dictToTest['NAME']+ " is required and inserted to the database")
    else:
        logger.info("torrent "+ dictToTest['NAME']+ " is not required and not inserted to the database")
    sqlite_drop_torrent_table()

def sqlite_is_new_torrent_requirement(filenameToTest):
    dictToTest=torrents_dict_for_SQLite(filenameToTest)
    sqlite_create_torrent_table_if_not_exist()
    if sqlite_is_torrent_needed(dictToTest):
        sqlite_insert_torrent_in_table(dictToTest)
        logger.info("torrent "+ dictToTest['NAME']+ " is required and inserted to the database")
        return True
    else:
        logger.info("torrent "+ dictToTest['NAME']+ " is not required and not inserted to the database")
        return False


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


# YOUR STUFF

# bot()
botDifferentPages(2,'')
# botDifferentPages(3,"/seeds/desc")


#sqlite()
#test_new_torrent_requirement()
# sqlite_drop_torrent_table()

#sqlite_export_torrent_table()


logger.info("finished.")

