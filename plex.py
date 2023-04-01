
import json
import os
import sqlite3
from plexapi.server import PlexServer
from plexapi.library import LibrarySection
import imdb
import logging
import datetime

def plexstuffs():
    """ Get mapping media imdb rate and filepath 
    """
    with open(os.path.expanduser('~')+'/dev/torrentFeed/config.json', encoding='utf-8') as config_file:
        data = json.load(config_file)
    plex_base_url=data['plexBaseUrl']
    plex_token=data['plexToken']
    access_system = imdb.IMDb()
    plex = PlexServer(plex_base_url, plex_token)
    # section = plex.library.section("Films")
    media_path_and_rate={}
    not_found_movie=[]
    sections=plex.library.section("Films").search()
    index = 0
    for section in enumerate(sections):
        video=section[1]
        file_path = video.media[0].parts[0].file
        if len(video.guids)>0 and 'imdb' in video.guids[0].id:
            try:
                imdb_data=access_system.get_movie(video.guids[0].id.replace('imdb://tt','')).data
                # print(video.title, video.guids[0])
                if 'rating' in imdb_data:
                    media_path_and_rate[file_path]=str(imdb_data['rating'])+"______"+video.guids[0].id.replace('imdb://tt','')
                else :
                    not_found_movie.append(file_path)
            except Exception as exception:
                logger.error("error: %s", exception)
                not_found_movie.append(file_path)
            # print('media:'+file_path+'  rate:'+str(mediaPathAndRate[file_path]))
        else :
            not_found_movie.append(file_path)
        logger.info("Get rate from imDB progress: %s"+str(float("{:.2f}".format(100*index/len(sections))))+"%")
        index += 1 
    sqlite_insert_rate_in_table(media_path_and_rate)
    sqlite_insert_rate_not_found_in_table(not_found_movie)
    logger.info(str(float("{:.2f}".format(100*len(not_found_movie)/(len(not_found_movie)+len(media_path_and_rate)))))+"%")

def list_files_to_delete():
    """ Get file's list for deletion. 
    """
    conn = sqlite3.connect('test.db')
    sqlite_select_query_not_found = """SELECT * from MEDIARATENOTFOUND"""
    cur = conn.cursor()
    cur.execute(sqlite_select_query_not_found)
    medias_not_found = cur.fetchall()
    current_year=str(datetime.date.today().year)
    last_year=str(datetime.date.today().year-1)
    pattern_to_avoid_deletion=['Trilogie', 'Trilogy', 'trilogy', 'Saison', 'EP', 'Integral', 'Intégral', 'Integrale', 'Intégrale', 'trilogy','trilogie', current_year, last_year ]
    list_of_files_to_remove=[]
    for row in medias_not_found:
        id=row[0]
        has_pattern=False
        for x in pattern_to_avoid_deletion:
            if any([x in id]):
                has_pattern=True
        if not has_pattern:
            filepath_to_remove='/Volumes/Video/'+id.replace('/share/Video/','')
            list_of_files_to_remove.append(filepath_to_remove)
    sqlite_select_query_rate="SELECT FILEPATH FROM MEDIAPATHANDRATE WHERE (FILEPATH NOT LIKE ? AND FILEPATH NOT LIKE ?) AND (CAST(RATE AS INTEGER) < 4.4)  --case-insensitive "
    cur.execute(sqlite_select_query_rate,('%'+current_year+'%','%'+last_year+'%'))
    medias_low_rate = cur.fetchall()
    logger.info('medias_not_found: %s',str(len(list_of_files_to_remove)))
    logger.info('medias_low_rate: %s',str(len(medias_low_rate)))
    for row_rate in medias_low_rate:
        id=row_rate[0]
        filepath_to_remove='/Volumes/Video/'+id.replace('/share/Video/','')
        list_of_files_to_remove.append(filepath_to_remove)
        # sql = 'DELETE FROM tasks WHERE id=?'
    conn.commit()
    conn.close()
    # for x in listOfFilesToRemove:
    #     logger.info(x)
    return list_of_files_to_remove

def plex_stuffs_test():
    with open(os.path.expanduser('~')+'/dev/torrentFeed/config.json',encoding='utf-8') as config_file:
        data = json.load(config_file)
    plex_base_url=data['plexBaseUrl']
    plex_token=data['plexToken']
    access_system = imdb.IMDb()
    plex = PlexServer(plex_base_url, plex_token)
    # section = plex.library.section("Films")
    media_path_and_rate={}
    not_found_movie=[]
    sections=plex.library.section("Films").search()
    video=sections[0]
    file_path = video.media[0].parts[0].file
    if len(video.guids)>0 and 'imdb' in video.guids[0].id:
        try:
            imdb_data=access_system.get_movie(video.guids[0].id.replace('imdb://tt','')).data
            # print(video.title, video.guids[0])
            if 'rating' in imdb_data:
                media_path_and_rate[file_path]=str(imdb_data['rating'])+"______"+video.guids[0].id.replace('imdb://tt','')
            else :
                not_found_movie.append(file_path)
        except Exception as exception:
            logger.error("error: %s",exception)
            not_found_movie.append(file_path)
            # print('media:'+file_path+'  rate:'+str(mediaPathAndRate[file_path]))
    else :
        not_found_movie.append(file_path)
    # logger.info(str(float("{:.2f}".format(100*x/len(sections))))+"%")
    sqlite_insert_rate_in_table(media_path_and_rate)
    sqlite_insert_rate_not_found_in_table(not_found_movie)
    logger.info(str(float("{:.2f}".format(100*len(not_found_movie)/(len(not_found_movie)+len(media_path_and_rate)))))+"%")

    # section
    # for section in sections:

def sqlite_create_rate_and_not_found_table_if_not_exist():
    """ Create MEDIAPATHANDRATE and MEDIARATENOTFOUND tables if they don't exist.
    """
    
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
    """ Drop MEDIAPATHANDRATE and MEDIARATENOTFOUND tables if they exist.
    """
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

def sqlite_insert_rate_in_table(media_path_and_rate):
    """ Insert in MEDIAPATHANDRATE.
    """
    conn = sqlite3.connect('test.db')
    #records or rows in a list
    records =  []
    #insert multiple records in a single query
    sql = ''' INSERT INTO MEDIAPATHANDRATE (FILEPATH,GUIDS,RATE) VALUES(?,?,?)'''
    for filepath, v in media_path_and_rate.items():
        rate_guid=v.split("______")
        row = (filepath, rate_guid[1], rate_guid[0])
        records.append(row,) 
    conn.executemany(sql,records)
    conn.commit()
    conn.close()


def sqlite_insert_rate_not_found_in_table(not_found_movie):
    """ Insert in MEDIARATENOTFOUND.
    """
    conn = sqlite3.connect('test.db')
    #records or rows in a list
    records =  []
    #insert multiple records in a single query
    sql = ''' INSERT INTO MEDIARATENOTFOUND (FILEPATH) VALUES(?)'''
    for filepath in not_found_movie:
        row=(filepath,)
        records.append(row)
    conn.executemany(sql,records)
    conn.commit()
    conn.close()

def remove_files_from_fs(list_of_deletion):
    """ Remove file in file system.
    """
    for deletion in enumerate(list_of_deletion):
        #FileNotFoundError
        try:
            os.remove(deletion[1])
        except OSError:
            pass
        logger.info("deletion progress: "+str(float("{:.2f}".format(100*deletion[0]/len(list_of_deletion))))+"%")
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
# logger.info('_____automated_deletion_process_finished_'+number_of_deletion+'_files_deleted_____')
logger.info('_____automated_deletion_process_finished_'+len(list_of_deletion)+'_files_deleted_____')

