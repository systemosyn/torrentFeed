
import csv
import fnmatch
import json
from pathlib import Path
import re
import shutil
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

from common_tools import check_exists_by_id, closeAdds, newBackupDB, launch_browser


def move_last_torrent_files_to_torrent_folder_2(path):
    remotePath="/Volumes/Home/torrentFeed"
    # remotePath=os.path.expanduser('~')+"/dev/mnt/torrentFeed"
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
        logger.info("nas path mounted")
        required=sqlite_is_new_torrent_requirement_3(filename)
        if required :
            try:
                copy(fileInDownloadsWithoutSpaces, remotePath)
            except FileNotFoundError as e:
                logger.error(e)
            finally:
                os.remove(fileInDownloadsWithoutSpaces)
            logger.info("copying done!")        
    else :
        logger.info(filename+" already processed.")
        os.remove(fileInDownloadsWithoutSpaces)

def botDifferentPages_1(numberOfPage, sortUsed):
    result=launch_browser(r'/Users/clementoudin/dev/5.4.1_0', sortUsed, 'animeUrl')
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
                if check_exists_by_id(browser, By.XPATH,'/html/body/div[1]/div[3]/div[2]/div[2]/div[2]/div[2]/a/img'):
                    torrentButton=browser.find_element(By.XPATH,'/html/body/div[1]/div[3]/div[2]/div[2]/div[2]/div[2]/a/img')
                    torrentButton.click()
                    time.sleep(5)
                    ## todo add the else part ##
                    if macPlatform :
                        list_of_files = glob.glob(os.path.expanduser('~')+'/Downloads/*.torrent') # * means all if need specific format then *.csv
                        fileInDownloads = max(list_of_files, key=os.path.getctime)
                        move_last_torrent_files_to_torrent_folder_2(os.path.expanduser('~')+'/dev/mnt/torrentFeed/')
                        logger.info("THE CODE IS HERE")
                        closeAdds(browser, url)
                        time.sleep(2)
                        browser.get(url)
                else : 
                    logger.error("torrentButton does not exist")
            else:
                logger.error("torrent: "+'/html/body/div[1]/div[3]/div[2]/table/tbody/tr['+str(iteration)+']'+" does not exist")
                newBackupDB()
                return
    newBackupDB()

def botSearch_1(searchItems):
    result=launch_browser(r'/Users/clementoudin/dev/5.4.1_0', '', 'serieUrl')
    browser= result["browser"]
    macPlatform = result["macPlatform"]
    rootUrl = result["rootUrl"]
    offset =result["offset"]
    offset=1
    #numberOfRows = len(browser.find_element(By.XPATH,'/html/body/div[1]/div[3]/div[2]/table/tbody'))
    #rows = browser.find_elements(By.XPATH("/html/body/div[1]/div[3]/div[2]/table/tbody"))
    ## todo add all the xpath in config ##
    ## todo add the loop to iterate into all the torrents --> DONE##
    for search in searchItems:
        url=str(rootUrl).split('torrents/series')[0]+'recherche/'+str(search).replace(' ', '%20')
        browser.get(url)
        getTorrentFromPage(browser, macPlatform, url)
        while check_exists_by_id(browser, By.XPATH,'/html/body/div[1]/div[3]/div[2]/ul/li[4]/a'):
            torrentPageElem=browser.find_element(By.XPATH,'/html/body/div[1]/div[3]/div[2]/ul/li[4]/a')
            torrentPageElem.click()
            parent = browser.window_handles[0]
            browser.switch_to.window(parent)
            url=browser.current_url
            getTorrentFromPage(browser, macPlatform, url)        
    newBackupDB()


# TODO use it in all bot # 
def getTorrentFromPage(browser, macPlatform, url):
    time.sleep(1)
    for iteration in range(1,51):
        if check_exists_by_id(browser, By.XPATH,'/html/body/div[1]/div[3]/div[2]/table/tbody/tr['+str(iteration)+']'):
            torrentPageElem=browser.find_element(By.XPATH,'/html/body/div[1]/div[3]/div[2]/table/tbody/tr['+str(iteration)+']')
            torrentPageElem.click()
            time.sleep(1)
            parent = browser.window_handles[0]
            browser.switch_to.window(parent)
            if check_exists_by_id(browser, By.XPATH,'/html/body/div[1]/div[3]/div[2]/div[2]/div[2]/div[2]/a/img'):
                torrentButton=browser.find_element(By.XPATH,'/html/body/div[1]/div[3]/div[2]/div[2]/div[2]/div[2]/a/img')
                torrentButton.click()
                time.sleep(1)
                ## todo add the else part ##
                if macPlatform :
                    list_of_files = glob.glob(os.path.expanduser('~')+'/Downloads/*.torrent') # * means all if need specific format then *.csv
                    fileInDownloads = max(list_of_files, key=os.path.getctime)
                    move_last_torrent_files_to_torrent_folder_2(os.path.expanduser('~')+'/dev/mnt/torrentFeed/')
                    closeAdds(browser, url)
                    time.sleep(2)
                    browser.get(url)
            else : 
                logger.error("torrentButton does not exist")
        else:
            logger.error("torrent: "+'/html/body/div[1]/div[3]/div[2]/table/tbody/tr['+str(iteration)+']'+" does not exist")


## add ways to store torrents with unknown fields maybe use plce for each pattern since LANGAGE is always first ##
def torrents_dict_for_SQLite_4(filename):
    matches_platform = ["[_cpasbien.si_]_"]
    matches_langage = ["TRUEFRENCH_", "MULTI_", "VOSTFR_", "VO_"]
    # math d'abord les épisodes si absent récupérer la saison car sans doute un torrent d'une saison entière
    # if fnmatch.fnmatch(file, '*.txt'):
    matches_episode = [r'[E]\d\d_']
    matches_season = [r'[S]\d\d']
    matches_langage_contained_in_other_matches =["FRENCH_"]
    matches_format = [ "WEBRIP_LD", "DVDRIP", "HDLight", "BluRay", "HDTV", "HDCAM_MD", "HDRip", "HDCAM"]
    matches_format_contained_in_other_matches =["WEBRIP_"]
    # matches_resolution = ["720p_", "720_", "1080p_", "1080_", "x264_", "4KLIGHT_ULTRA_HD_x265_", "XviD-RZP_", "x264-RZP_"]
    # matches_resolution_contained_in_other_matches =["4KLIGHT_ULTRA_HD_"]
    bool_platform = False
    bool_langage = False
    bool_format = False
    bool_resolution = False
    bool_episode = False
    bool_saison = False
    media=filename
    dict = {}
    ## todo: add else clause ##
    for pattern_episode in matches_episode:
        res=re.compile(pattern_episode)
        if res.search(filename):
            dict['EPISODE']=res.search(filename).group(0)
            media= filename.replace(dict['EPISODE'], '')
            bool_episode = True
    if not bool_episode:
        dict['EPISODE'] = "UNKNOWN"
    for pattern_saison in matches_season:
        res=re.compile(pattern_saison)
        if res.search(filename):
            dict['SAISON']=res.search(filename).group(0)
            media= media.replace(dict['SAISON'], '')
            bool_saison = True
    if not bool_saison:
        dict['SAISON'] = "UNKNOWN"
    for x in matches_platform:
        if any([x in filename]):
            dict['PLATFORM'] = x
            media= media.replace(x, '')
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
    if dict['SAISON']=="UNKNOWN" and dict['EPISODE']=="UNKNOWN":
        if re.compile(r'Saison_\d').search(filename):
            saison_not_formated=re.compile(r'Saison_\d').search(filename).group(0)
            media= media.replace(re.compile(r'Saison_\d').search(filename).group(0)+'_', '')
            if re.compile(r'\d\d').search(saison_not_formated):       
                dict['SAISON']='S'+re.compile(r'\d\d').search(saison_not_formated).group(0)
                dict['INTEGRAL']= 'True'
                dict['FULLNAME']=filename
                dict['UNDEFINED']='False'
            elif re.compile(r'\d').search(saison_not_formated):
                dict['SAISON']='S0'+re.compile(r'\d').search(saison_not_formated).group(0)
                dict['INTEGRAL']= 'True'
                dict['FULLNAME']=filename
                dict['UNDEFINED']='False'
            else:
                dict['FULLNAME']=filename
                dict['UNDEFINED']='True'
                dict['INTEGRAL']= 'False'
        else:
            dict['FULLNAME']=filename
            dict['UNDEFINED']='True'
            dict['INTEGRAL']= 'False'
    else:
        dict['INTEGRAL']= 'False'
        dict['FULLNAME']=filename
        dict['UNDEFINED']='False'
    dict['NAME']=media.replace(media.split("_")[-1], '')
    dict['ID']=dict['NAME']+dict['SAISON']+dict['EPISODE']+dict['LANGAGE']+dict['FORMAT']
    logger.info(dict['ID'])
    return dict

## add tests ##
def sqlite_drop_and_create_torrent_table():
    conn = sqlite3.connect('test.db')
    table_exist=conn.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='TORRENTSERIES' ''')
    #if the count is 1, then table exists
    if table_exist.fetchone()[0]==1 : 
        conn.execute('''DROP TABLE TORRENTSERIES''')
        logger.info('Table drop.')
        ## ID = NAME+LANGAGE+FORMAT ##
        conn.execute('''CREATE TABLE TORRENTSERIES
                (ID            TEXT PRIMARY KEY NOT NULL,
                NAME           TEXT             NOT NULL,
                PLATFORM       TEXT             NOT NULL,
                LANGAGE        TEXT             NOT NULL,
                EPISODE        TEXT             NOT NULL,
                SAISON         TEXT             NOT NULL,
                INTEGRAL       TEXT             NOT NULL,
                FULLNAME       TEXT             NOT NULL,
                UNDEFINED      TEXT             NOT NULL,
                FORMAT         TEXT);''')
        logger.info("Table created successfully")
    else :
        conn.execute('''CREATE TABLE TORRENTSERIES
                (ID            TEXT PRIMARY KEY NOT NULL,
                NAME           TEXT             NOT NULL,
                PLATFORM       TEXT             NOT NULL,
                LANGAGE        TEXT             NOT NULL,
                EPISODE        TEXT             NOT NULL,
                SAISON         TEXT             NOT NULL,
                INTEGRAL       TEXT             NOT NULL,
                FULLNAME       TEXT             NOT NULL,
                UNDEFINED      TEXT             NOT NULL,
                FORMAT         TEXT);''')
        logger.info("Table created successfully")
    conn.commit()
    #close the connection
    conn.close()
    # sql_query = """SELECT name FROM sqlite_master WHERE type='table';"""
    # cursor=conn.execute(sql_query)
    # logger.info(cursor.fetchall())

def sqlite_create_torrent_table_if_not_exist_5():
    conn = sqlite3.connect('test.db')
    table_exist=conn.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='TORRENTSERIES' ''')
    #if the count is 1, then table exists
    if table_exist.fetchone()[0]==1 : 
        logger.info("Table already exist")
    else :
        conn.execute('''CREATE TABLE TORRENTSERIES
                (ID            TEXT PRIMARY KEY NOT NULL,
                NAME           TEXT             NOT NULL,
                PLATFORM       TEXT             NOT NULL,
                LANGAGE        TEXT             NOT NULL,
                EPISODE        TEXT             NOT NULL,
                SAISON         TEXT             NOT NULL,
                INTEGRAL       TEXT             NOT NULL,
                FULLNAME       TEXT             NOT NULL,
                UNDEFINED      TEXT             NOT NULL,
                FORMAT         TEXT);''')
        logger.info("Table created successfully")
    # sql_query = """SELECT name FROM sqlite_master WHERE type='table';"""
    # cursor=conn.execute(sql_query)
    # logger.info(cursor.fetchall())
    conn.commit()
    #close the connection
    conn.close()

def sqlite_insert_torrent_in_table_7(dict):
    conn = sqlite3.connect('test.db')
    sql = ''' INSERT OR IGNORE INTO TORRENTSERIES (ID,NAME,PLATFORM,LANGAGE,EPISODE,SAISON,INTEGRAL,FULLNAME,UNDEFINED,FORMAT) VALUES(?,?,?,?,?,?,?,?,?,?)'''
    row = (dict['ID'], dict['NAME'], dict['PLATFORM'], dict['LANGAGE'], dict['EPISODE'], dict['SAISON'], dict['INTEGRAL'], dict['FULLNAME'], dict['UNDEFINED'], dict['FORMAT'])
    cur = conn.cursor()
    cur.execute(sql, row)
    conn.commit()
    conn.close()

def sqlite_drop_torrent_table():
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    #Doping EMPLOYEE table if already exists
    cursor.execute("DROP TABLE TORRENTSERIES")
    logger.info("Table dropped... ")
    #Commit your changes in the database
    conn.commit()
    #Closing the connection
    conn.close()

def sqlite_is_torrent_needed_6(dict):
    ''' Return if a torrent has to be downloaded following this logic: 

    If the LANGAGE from the torrent's dictonary put as parameter is not french --> not required 

    If the torrent is already present in TORRENTSERIES table in french and in HD --> not required

    If already present in TORRENTSERIES table in french and the FORMAT from the torrent's dictonary put as parameter is not HD --> not required 

    Otherwise the torrent is required.'''
    
    conn = sqlite3.connect('test.db')
    table_exist=conn.execute("SELECT count(ID) FROM TORRENTSERIES WHERE ID=?",(dict['NAME'],))
    if table_exist.fetchone()[0]==1 : 
        return False
    if (dict['UNDEFINED']=='True'):
        return True
    if(dict['INTEGRAL']=='True'):
        already_downloaded_torrent_execute=conn.execute("SELECT LANGAGE, FORMAT FROM TORRENTSERIES WHERE NAME=? AND SAISON=? AND INTEGRAL=?", (dict['NAME'], dict['SAISON'], dict['INTEGRAL'],))
        records = already_downloaded_torrent_execute.fetchall()
        french=["TRUEFRENCH_", "FRENCH_", "MULTI_"]
        if any([x in dict['LANGAGE'] for x in french]):
            if not len(records)==0:
                for row in records:
                    if( (row[0]=="TRUEFRENCH_" or row[0]=="FRENCH_" or row[0]=="MULTI_") and (row[1]=="DVDRIP" or row[1]=="HDLight" or row[1]=="BluRay" or row[1]=="HDTV")):
                        return False
                for row in records:
                    if( (row[0]=="TRUEFRENCH_" or row[0]=="FRENCH_" or row[0]=="MULTI_") and (dict['FORMAT']=="DVDRIP" or dict['FORMAT']=="HDLight" or dict['FORMAT']=="BluRay" or dict['FORMAT']=="HDTV")):
                        return True
                    else:
                        return False
            else :
                logger.info("media " + dict['NAME'] + " not dowloaded yet") 
                return True
            return True
        else: 
            return False
    else:
        already_downloaded_integral_torrent_execute=conn.execute("SELECT count(*) FROM TORRENTSERIES WHERE NAME=? AND SAISON=? AND INTEGRAL='True'", (dict['NAME'], dict['SAISON'], ))
        already_downloaded_integral_res=already_downloaded_integral_torrent_execute.fetchone()[0]
        if not already_downloaded_integral_res==0 :
            logger.info('Integral for '+dict['NAME']+' season '+ dict['SAISON']+' already downloaded')
            return False 
        already_downloaded_torrent_execute=conn.execute("SELECT LANGAGE, FORMAT FROM TORRENTSERIES WHERE NAME=? AND SAISON=? AND EPISODE=?", (dict['NAME'], dict['SAISON'], dict['EPISODE'],))
        records = already_downloaded_torrent_execute.fetchall()
        french=["TRUEFRENCH_", "FRENCH_", "MULTI_"]
        if any([x in dict['LANGAGE'] for x in french]):
            if not len(records)==0:
                for row in records:
                    if( (row[0]=="TRUEFRENCH_" or row[0]=="FRENCH_" or row[0]=="MULTI_") and (row[1]=="DVDRIP" or row[1]=="HDLight" or row[1]=="BluRay" or row[1]=="HDTV")):
                        return False
                for row in records:
                    if( (row[0]=="TRUEFRENCH_" or row[0]=="FRENCH_" or row[0]=="MULTI_") and (dict['FORMAT']=="DVDRIP" or dict['FORMAT']=="HDLight" or dict['FORMAT']=="BluRay" or dict['FORMAT']=="HDTV")):
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
    
    BE CAREFUL IT CURRENTLY DROP TORRENTSERIES TABLE !
    '''

    filenameToTest="[_cpasbien.si_]_The_Last_of_Us_S01E01_FRENCH_HDTV.torrent"
    filenameTestConfig1="[_cpasbien.si_]_The_Last_of_Us_S01E01_MULTI_WEBRIP_LD.torrent"
    filenameTestConfig2="[_cpasbien.si_]_The_Last_of_Us_S01E01_VOSTFR_HDLight_1080.torrent" ###
    filenameTestConfig3="[_cpasbien.si_]_The_Last_of_Us_Saison_1_FRENCH_DVDRIP.torrent" ###
    # filenameToTest="[_cpasbien.si_]_Star_Wars___Episode_II_-_L_Attaque_des_clones_TRUEFRENCH_HDLight_1080_2002.torrent"
    # filenameTestConfig1="[_cpasbien.si_]_Star_Wars___Episode_II_-_L_Attaque_des_clones_MULTI_WEBRIP_LD_1080_2002.torrent"
    # filenameTestConfig2="[_cpasbien.si_]_Star_Wars___Episode_II_-_L_Attaque_des_clones_VOSTFR_HDLight_1080_2002.torrent" ###
    # filenameTestConfig3="[_cpasbien.si_]_Star_Wars___Episode_II_-_L_Attaque_des_clones_FRENCH_DVDRIP_1080_2002.torrent" ###
    dictToTest=torrents_dict_for_SQLite_4(filenameToTest)
    dictTestConfig1=torrents_dict_for_SQLite_4(filenameTestConfig1)
    dictTestConfig2=torrents_dict_for_SQLite_4(filenameTestConfig2)
    dictTestConfig3=torrents_dict_for_SQLite_4(filenameTestConfig3)
    sqlite_drop_and_create_torrent_table()
    sqlite_insert_torrent_in_table_7(dictTestConfig1)
    sqlite_insert_torrent_in_table_7(dictTestConfig2)
    sqlite_insert_torrent_in_table_7(dictTestConfig3)
    if sqlite_is_torrent_needed_6(dictToTest):
        sqlite_insert_torrent_in_table_7(dictToTest)
        logger.info("torrent "+ dictToTest['NAME']+ " is required and inserted to the database")
    else:
        logger.info("torrent "+ dictToTest['NAME']+ " is not required and not inserted to the database")
    sqlite_drop_torrent_table()

def sqlite_is_new_torrent_requirement_3(filenameToTest):
    dictToTest=torrents_dict_for_SQLite_4(filenameToTest)
    sqlite_create_torrent_table_if_not_exist_5()
    if sqlite_is_torrent_needed_6(dictToTest):
        sqlite_insert_torrent_in_table_7(dictToTest)
        logger.info("torrent "+ dictToTest['NAME']+ " is required and inserted to the database")
        return True
    else:
        logger.info("torrent "+ dictToTest['NAME']+ " is not required and not inserted to the database")
        return False
## NOT USED ANYMORE ##
def sqlite_export_torrent_table():
    try:
        conn = sqlite3.connect('test.db')
        cursor = conn.cursor()
        cursor.execute("select * from TORRENTSERIES")
        with open("TORRENT_SERIES_DB.csv", "w") as csv_file:
            csv_writer = csv.writer(csv_file, delimiter="\t")
            csv_writer.writerow([i[0] for i in cursor.description])
            csv_writer.writerows(cursor)

        dirpath = os.getcwd() + "/employee_data.csv"
        logger.info("Data exported Successfully into {}".format(dirpath))

    except sqlite3.Error as e:
        logger.error(e)

    # Close database connection
    finally:
        conn.close()

logging.basicConfig(filename='/Volumes/Home/series.log', encoding='utf-8', level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')
logger=logging.getLogger('CPasBienFeed')

# botSearch_1(['LOL sort'])

# YOUR STUFF

# bot()
botDifferentPages_1(15,'')

# ######### PUT FILE ON NAS TEST ###########
# test_file_to_push_on_nas=os.path.expanduser('~')+"/dev/torrentFeed/test.txt"
# remotePath="/Volumes/Home/torrentFeed"
# # remotePath=os.path.expanduser('~')+"/dev/mnt/torrentFeed"
# copy(test_file_to_push_on_nas, remotePath)




# botDifferentPages_1(2,"")

######### OLD TEST ###########
# matches_season = [r'[S]\d\d[E]\d\d_']
# list_of_files = glob.glob(os.path.expanduser('~')+'/dev/torrentFeed/torrentFiles/*.torrent') # * means all if need specific format then *.csv
# for file in list_of_files:
#     fileInDownloadsWithoutSpaces=file.replace(" ", "_")
#     fileInDownloadsWithoutSpaces=fileInDownloadsWithoutSpaces.replace("(", "_")
#     fileInDownloadsWithoutSpaces=fileInDownloadsWithoutSpaces.replace(")", "_")
#     fileInDownloadsWithoutSpaces=fileInDownloadsWithoutSpaces.replace("'", "_")
#     filename = fileInDownloadsWithoutSpaces.split("/")[-1]
#     for pattern_episode in matches_season:

#         res=re.compile(pattern_episode)
#         # res=re.compile(pattern_episode)
#         if res.search(filename):
#             logger.info("file MATCHED: "+filename)
#             found = res.search(filename).group(0)
#             logger.info(found)


# test_new_torrent_requirement()


logger.info("finished.")
