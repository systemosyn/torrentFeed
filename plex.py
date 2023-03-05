
import json
import os
import sqlite3
from plexapi.server import PlexServer
from plexapi.library import LibrarySection
import imdb
import logging
import datetime

def plexstuffs():
    conn = sqlite3.connect('test.db')
    with open(os.path.expanduser('~')+'/dev/torrentFeed/config.json') as config_file:
        data = json.load(config_file)
    plexBaseUrl=data['plexBaseUrl']
    plexToken=data['plexToken']
    ia = imdb.IMDb()
    plex = PlexServer(plexBaseUrl, plexToken)
    # section = plex.library.section("Films")
    mediaPathAndRate={}
    notFoundMovie=[]
    sections=plex.library.section("Films").search()
    for x in range(len(sections)): 
        video=sections[x]
        file_path = video.media[0].parts[0].file
        if len(video.guids)>0 and 'imdb' in video.guids[0].id:
            try:
                imdbData=ia.get_movie(video.guids[0].id.replace('imdb://tt','')).data
                # print(video.title, video.guids[0])
                if 'rating' in imdbData:
                    mediaPathAndRate[file_path]=str(imdbData['rating'])+"______"+video.guids[0].id.replace('imdb://tt','')
                else :
                    notFoundMovie.append(file_path)
            except:
                logger.error("error")
                notFoundMovie.append(file_path)
            # print('media:'+file_path+'  rate:'+str(mediaPathAndRate[file_path]))
        else :
            notFoundMovie.append(file_path)
        logger.info("Get rate from imDB progress: "+str(float("{:.2f}".format(100*x/len(sections))))+"%")
    sqlite_insert_rate_in_table(mediaPathAndRate)
    sqlite_insert_rate_not_found_in_table(notFoundMovie)
    logger.info(str(float("{:.2f}".format(100*len(notFoundMovie)/(len(notFoundMovie)+len(mediaPathAndRate)))))+"%")

def list_files_to_delete():
    conn = sqlite3.connect('test.db')
    sqlite_select_query_not_found = """SELECT * from MEDIARATENOTFOUND"""
    cur = conn.cursor()
    cur.execute(sqlite_select_query_not_found)
    medias_not_found = cur.fetchall()
    currentyear=str(datetime.date.today().year)
    lastyear=str(datetime.date.today().year-1)
    pattern_to_avoid_deletion=['Trilogie', 'Trilogy', 'trilogy', 'Integral', 'Intégral', 'Integrale', 'Intégrale', 'trilogy','trilogie', currentyear, lastyear ]
    listOfFilesToRemove=[]
    for row in medias_not_found:
        id=row[0]
        has_pattern=False
        for x in pattern_to_avoid_deletion:
            if any([x in id]):
                has_pattern=True
        if not has_pattern:
            filepathToRemove='/Volumes/Video/'+id.replace('/share/Video/','')
            listOfFilesToRemove.append(filepathToRemove)
    sqlite_select_query_rate="SELECT FILEPATH FROM MEDIAPATHANDRATE WHERE (FILEPATH NOT LIKE ? AND FILEPATH NOT LIKE ?) AND (CAST(RATE AS INTEGER) < 4.4)  --case-insensitive "
    cur.execute(sqlite_select_query_rate,('%'+currentyear+'%','%'+lastyear+'%'))
    medias_low_rate = cur.fetchall()
    logger.info('medias_not_found: '+str(len(listOfFilesToRemove)))
    logger.info('medias_low_rate: '+str(len(medias_low_rate)))
    for row_rate in medias_low_rate:
        id=row_rate[0]
        filepathToRemove='/Volumes/Video/'+id.replace('/share/Video/','')
        listOfFilesToRemove.append(filepathToRemove)
        # sql = 'DELETE FROM tasks WHERE id=?'
    conn.commit()
    conn.close()
    # for x in listOfFilesToRemove:
    #     logger.info(x)
    return listOfFilesToRemove

def plexStuffsTest():
    with open(os.path.expanduser('~')+'/dev/torrentFeed/config.json') as config_file:
        data = json.load(config_file)
    plexBaseUrl=data['plexBaseUrl']
    plexToken=data['plexToken']
    ia = imdb.IMDb()
    plex = PlexServer(plexBaseUrl, plexToken)
    # section = plex.library.section("Films")
    mediaPathAndRate={}
    notFoundMovie=[]
    sections=plex.library.section("Films").search()
    video=sections[0]
    file_path = video.media[0].parts[0].file
    if len(video.guids)>0 and 'imdb' in video.guids[0].id:
        try:
            imdbData=ia.get_movie(video.guids[0].id.replace('imdb://tt','')).data
            # print(video.title, video.guids[0])
            if 'rating' in imdbData:
                mediaPathAndRate[file_path]=str(imdbData['rating'])+"______"+video.guids[0].id.replace('imdb://tt','')
            else :
                notFoundMovie.append(file_path)
        except:
            logger.error("error")
            notFoundMovie.append(file_path)
            # print('media:'+file_path+'  rate:'+str(mediaPathAndRate[file_path]))
    else :
        notFoundMovie.append(file_path)
    # logger.info(str(float("{:.2f}".format(100*x/len(sections))))+"%")
    sqlite_insert_rate_in_table(mediaPathAndRate)
    sqlite_insert_rate_not_found_in_table(notFoundMovie)
    logger.info(str(float("{:.2f}".format(100*len(notFoundMovie)/(len(notFoundMovie)+len(mediaPathAndRate)))))+"%")

    # section
    # for section in sections:

def sqlite_create_rate_and_not_found_table_if_not_exist():
    conn = sqlite3.connect('test.db')
    media_path_and_rate_exist=conn.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='MEDIAPATHANDRATE' ''')
    #if the count is 1, then table exists
    if media_path_and_rate_exist.fetchone()[0]==1 : 
        logger.info("Table MEDIAPATHANDRATE already exist")
    else :
        conn.execute('''CREATE TABLE MEDIAPATHANDRATE
                (FILEPATH      TEXT PRIMARY KEY NOT NULL,
                GUIDS       TEXT             NOT NULL,
                RATE       TEXT             NOT NULL);''')
        logger.info("Table MEDIAPATHANDRATE created successfully")
    media_rate_not_found_exist=conn.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='MEDIARATENOTFOUND' ''')
    #if the count is 1, then table exists
    if media_rate_not_found_exist.fetchone()[0]==1 : 
        logger.info("Table MEDIARATENOTFOUND already exist")
    else :
        conn.execute('''CREATE TABLE MEDIARATENOTFOUND
                (FILEPATH      TEXT PRIMARY KEY NOT NULL);''')
        logger.info("Table MEDIARATENOTFOUND created successfully")
    conn.commit()
    conn.close()

def sqlite_drop_media_table():
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    table_exist=cursor.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='MEDIARATENOTFOUND' ''')
    #if the count is 1, then table exists
    if table_exist.fetchone()[0]==1 : 
        cursor.execute("DROP TABLE MEDIARATENOTFOUND")
    table_exist=cursor.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='MEDIAPATHANDRATE' ''')
    #if the count is 1, then table exists
    if table_exist.fetchone()[0]==1 : 
        cursor.execute("DROP TABLE MEDIAPATHANDRATE")
    logger.info("Table dropped... ")
    #Commit your changes in the database
    conn.commit()
    #Closing the connection
    conn.close()

def sqlite_insert_rate_in_table(mediaPathAndRate):
    conn = sqlite3.connect('test.db')
    #records or rows in a list
    records =  []
    #insert multiple records in a single query
    sql = ''' INSERT INTO MEDIAPATHANDRATE (FILEPATH,GUIDS,RATE) VALUES(?,?,?)'''
    for filepath, v in mediaPathAndRate.items():
        rateGuid=v.split("______")
        row = (filepath, rateGuid[1], rateGuid[0])
        records.append(row,)   
    conn.executemany(sql,records)
    conn.commit()
    conn.close()


def sqlite_insert_rate_not_found_in_table(notFoundMovie):
    conn = sqlite3.connect('test.db')
    #records or rows in a list
    records =  []
    #insert multiple records in a single query
    sql = ''' INSERT INTO MEDIARATENOTFOUND (FILEPATH) VALUES(?)'''
    for filepath in notFoundMovie:
        row=(filepath,)
        records.append(row)   
    conn.executemany(sql,records)
    conn.commit()
    conn.close()

def remove_files_from_fs(list_of_deletion):
    for i in range(len(list_of_deletion)):
        #FileNotFoundError
        os.remove(list_of_deletion[i])
        logger.info("deletion progress: "+str(float("{:.2f}".format(100*i/len(list_of_deletion))))+"%")
    return len(list_of_deletion)
  
logger = logging.getLogger('plex.py')
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

sqlite_drop_media_table()
# logger.info(sqlite3.sqlite_version)
sqlite_create_rate_and_not_found_table_if_not_exist()

# notFoundMovie=[]
# notFoundMovie.append('test')
# notFoundMovie.append('test2')
# sqlite_insert_rate_not_found_in_table(notFoundMovie)

plexstuffs()
list_of_deletion=list_files_to_delete()
number_of_deletion=remove_files_from_fs(list_of_deletion)
logger.info('_____automated_deletion_process_finished_'+number_of_deletion+'_files_deleted_____')

