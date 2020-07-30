import configparser
from datetime import datetime
import json
import linecache
import logging
import os
import platform
import re
import sys
from os.path import isfile, join
from WebRequests import GetWebResource, DownloadFile, GetHeader

# Constants
INI_FILENAME = "BUGDownloader.ini"
INI_MAIN = "MAIN"
INI_MAIN_LOGFILEPATH = 'logFilePath'
INI_MAIN_APIURL = 'apiUrl'
INI_MAIN_LOGLEVEL = 'logLevel'
INI_MAIN_LOGFORMAT = 'logFormat'
INI_PLATFORM_TARGETPATH = 'targetPath'
INI_MAIN_URLFILTERREGEX = 'urlFilterRegex'
INI_MAIN_MAXFILEDELETE = 'maxFileDelete'

def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print(f'EXCEPTION IN ({filename}, LINE {lineno}, "{line.strip()}"): {exc_obj}')


config = configparser.ConfigParser()
config.read(INI_FILENAME)
configMain = config[INI_MAIN]
configPlatform = config[platform.system()]

logging.basicConfig(
    format=configMain.get(INI_MAIN_LOGFORMAT),
    handlers=[logging.FileHandler(
        filename=configMain.get(INI_MAIN_LOGFILEPATH),
        encoding='utf-8',
        mode='a')],
    level=configMain.get(INI_MAIN_LOGLEVEL))

localDir = configPlatform.get(INI_PLATFORM_TARGETPATH)

allFileNames = []
stats = dict(starttime=datetime.now(), downloads=0, updates=0, existing=0, errors=0, removals=0)

try:
    terminal_columns = os.get_terminal_size().columns - 1
except OSError:
    terminal_columns = 80

logging.debug(f'terminal columns: {terminal_columns}')

blankLine = ' ' * terminal_columns

try:
    logging.info(f'Session Started at {datetime.now()}')

    print('Phase 1 - Download new or updated files')

    print(f'Calling Web Service... ', end='')
    logging.debug(f'Call web service at {configMain.get(INI_MAIN_APIURL)}')
    apiResult = GetWebResource(configMain.get(INI_MAIN_APIURL), 5, 30)
    bugSongs = json.loads(apiResult.text)
    print(f'Found {len(bugSongs)} songs')

    logging.info(f'Web Service returned list of {len(bugSongs)} songs')

    # phase 1 - download any files that are not already present locally

    for songIndex, songKey in enumerate(bugSongs, start=1):

        status = f'\r{blankLine}\rSong {songIndex}/{len(bugSongs)} : '
        print(f'{status}', end='')
        logging.debug(f"SongKeyLoop:  Key = {songKey}")
        song = bugSongs[songKey]
        logging.debug(f"SongKeyLoop: Title = {song['title']}  Artist = {song['artist']}")
        fileNameBase = song['title'] + ' - ' + song['artist']
        logging.debug(f"SongKeyLoop: fileNameBase = {fileNameBase}")
        songURLs = song['URL']

        for fileIndex, urlKey in enumerate(songURLs, start=1):
            status = f'\r{blankLine}\rSong {songIndex}/{len(bugSongs)} File {fileIndex}/{len(songURLs)} : '
            print(f'{status}', end='')
            logging.debug(f"UrlKeyLoop: Key = {urlKey}")
            fileName = (fileNameBase + ' - ' + urlKey + '.pdf').replace('/', '_').replace('\\', '_').replace('⁄', '_')
            logging.debug(f"UrlKeyLoop: FileName = {fileName}")
            allFileNames.append(fileName)
            fileURL = songURLs[urlKey]["URL"]
            filePath = join(localDir, fileName)

            if re.search(configMain.get(INI_MAIN_URLFILTERREGEX), fileURL):
                if isfile(filePath):
                    print(f'{status} Checking remote date...', end='')
                    if "LastUpdated" in songURLs[urlKey]:
                        # files hosted on Google drive will have LastUpdated meta-data
                        fileLastUpdated = datetime.strptime(songURLs[urlKey]["LastUpdated"], "%Y-%m-%dT%H:%M:%S.%fZ")
                    else:
                        # for other files (scorpex etc) make a HEAD request to obtain Last-Modified header
                        fileLastUpdatedHeader = GetHeader(fileURL, "Last-Modified", 30)
                        if fileLastUpdatedHeader is None:
                            # no date? awww bugger - let's hope it's there next time
                            fileLastUpdated = datetime.fromtimestamp(0)
                        else:
                            fileLastUpdated = datetime.strptime(fileLastUpdatedHeader, "%a, %d %b %Y %H:%M:%S %Z")
                    logging.debug(f"Remote File Last Modified: {fileLastUpdated}")
                    localFileDate = datetime.fromtimestamp(os.path.getmtime(filePath))
                    logging.debug(f"Local File Modification Date: {localFileDate}")
                    if fileLastUpdated > localFileDate:
                        logging.debug("Updating")
                        tempFilePath = join(localDir, "updated_" + fileName)
                        print(f'{status} Updating...', end='')
                        if DownloadFile(tempFilePath, fileURL, 1, 10, False):
                            try:
                                os.remove(filePath)
                                logging.debug(f"deleted: {filePath}")
                                os.rename(tempFilePath, filePath)
                                logging.debug(f"renamed: {tempFilePath} to {filePath}")
                                logging.info(f"updated: {filePath}")
                                stats['updates'] += 1
                            except OSError:
                                logging.error(f"failed to update: {filePath}")
                                stats['errors'] += 1
                        else:
                            logging.warning("error:" + fileName)
                            stats['errors'] += 1
                    else:
                        stats['existing'] += 1
                        logging.debug("exists: " + fileName)
                else:
                    logging.debug("downloading: " + fileName)
                    print(f'{status} Downloading...', end='')
                    if DownloadFile(join(localDir, fileName), fileURL, 1, 10, False):
                        logging.info("downloaded: " + fileName)
                        stats['downloads'] += 1
                    else:
                        logging.warning("error:" + fileName)
                        stats['errors'] += 1
            else:
                logging.warning(f"URL excluded by URL filter: {fileURL}")

    print(f'{status} download phase complete')

    # phase 2 - remove any local files that are not in the list provided by the web service

    maxFilesToDelete = configMain.getint(INI_MAIN_MAXFILEDELETE, 10)

    if maxFilesToDelete is None:
        maxFilesToDelete = 10

    if len(bugSongs) < 1:  # skip this phase if web service return zero files
        pass
    else:
        print(f'Phase 2 - Remove any non-relevant local files')
        print(f'Checking local files... ', end='')

        localFiles = [filename for filename in os.listdir(localDir) if isfile(join(localDir, filename))]
        logging.info(f"Checking {len(localFiles)} local files in {localDir}")

        filesToRemove = [filename for filename in localFiles if filename not in allFileNames]
        logging.debug(f'Found {len(filesToRemove)} files to remove')
        print(f'Found {len(filesToRemove)} files to remove of {len(localFiles)} local files')

        if len(filesToRemove) > maxFilesToDelete:
            logging.warning(f'Only the first {maxFilesToDelete} files will be removed')
            print(f'WARNING: Only the first {maxFilesToDelete} files will be removed')
            filesToRemove = filesToRemove[0: maxFilesToDelete]

        for fileIndex, filename in enumerate(filesToRemove, start=1):
            status = f'\r{blankLine}\rRemoving File {fileIndex}/{len(filesToRemove)} : '
            print(f'{status}', end='')
            filePath = join(localDir, filename)
            logging.info(f"Removing: {filePath}")
            try:
                os.remove(filePath)
                stats['removals'] += 1
            except OSError:
                stats['errors'] += 1
                logging.error(f"Error trying to remove file {filePath}")

        if len(filesToRemove) > 0:
            print(f'{status} local file removal complete')

except:
    PrintException()

summary = \
    f"Errors: {stats['errors']}  Downloaded: {stats['downloads']}  Updated: {stats['updates']}  " + \
    f"Existing: {stats['existing']}  Removed: {stats['removals']}"

logging.info(summary)
print(f"Synchronisation Summary:\r\n  {summary}")
