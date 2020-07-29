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


def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))


logging.basicConfig(filename='BUGDownloader.log', level=logging.INFO)

if platform.system() == 'Windows':
    localDir = "C:\\Repos\\BUGDownloader\\test"
else:
    localDir = "/home/pi/Ukulele/BUG Chord Charts"

apiURL = "https://script.google.com/macros/s/AKfycbx-0s1grPv0Wj_wXZUDRggB7Eac_c4TGHkMQ1aNOcNv41eCeg/exec"

allFileNames = []
downloadCount = 0
updateCount = 0
existCount = 0
errorCount = 0
removeCount = 0

try:
    logging.info('Session Started at {0}'.format(datetime.now()))

    logging.debug(f'Call web service at {apiURL}')
    apiResult = GetWebResource(apiURL, 5, 30)
    bugSongs = json.loads(apiResult.text)

    logging.info(f'Web Service returned list of {len(bugSongs)} songs')

    # phase 1 - download any files that are not already present locally

    for songKey in bugSongs:
        logging.debug("SongKeyLoop:  Key = {0}".format(songKey))
        song = bugSongs[songKey]
        logging.debug("SongKeyLoop: Title = {0}  Artist = {1}".format(song['title'], song['artist']))
        fileNameBase = song['title'] + ' - ' + song['artist']
        logging.debug("SongKeyLoop: fileNameBase = {0}".format(fileNameBase))
        songURLs = song['URL']
        for urlKey in songURLs:
            logging.debug("UrlKeyLoop: Key = {0}".format(urlKey))
            fileName = (fileNameBase + ' - ' + urlKey + '.pdf').replace('/', '_').replace('\\', '_').replace('⁄', '_')
            logging.debug(f"UrlKeyLoop: FileName = {fileName}")
            allFileNames.append(fileName)
            fileURL = songURLs[urlKey]["URL"]
            filePath = join(localDir, fileName)
            if re.search('scorpex|ozbcoz|drive', fileURL):
                if isfile(filePath):
                    if "LastUpdated" in songURLs[urlKey]:
                        # files hosted on Google drive will have LastUpdated meta-data
                        fileLastUpdated = datetime.strptime(songURLs[urlKey]["LastUpdated"], "%Y-%m-%dT%H:%M:%S.%fZ")
                    else:
                        # for other files (scorpex etc) make a HEAD request to obtain Last-Modified header
                        fileLastUpdatedHeader = GetHeader(fileURL, "Last-Modified", 30)
                        if fileLastUpdatedHeader is None:
                            fileLastUpdated = datetime.fromtimestamp(0)
                        else:
                            fileLastUpdated = datetime.strptime(fileLastUpdatedHeader, "%a, %d %b %Y %H:%M:%S %Z")
                    logging.debug(f"Remote File Last Modified: {fileLastUpdated}")
                    localFileDate = datetime.fromtimestamp(os.path.getmtime(filePath))
                    logging.debug(f"Local File Modification Date: {localFileDate}")
                    if fileLastUpdated > localFileDate:
                        logging.debug("Updating")
                        tempFilePath = join(localDir, "updated_" + fileName)
                        if DownloadFile(tempFilePath, fileURL, 1, 10, False):
                            try:
                                os.remove(filePath)
                                logging.debug(f"deleted: {filePath}")
                                os.rename(tempFilePath, filePath)
                                logging.debug(f"renamed: {tempFilePath} to {filePath}")
                                logging.info(f"updated: {filePath}")
                                updateCount += 1
                            except OSError:
                                logging.error(f"failed to update: {filePath}")
                                errorCount += 1
                        else:
                            logging.warning("error:" + fileName)
                            errorCount += 1
                    else:
                        existCount += 1
                        logging.debug("exists: " + fileName)
                else:
                    logging.debug("downloading: " + fileName)
                    if DownloadFile(join(localDir, fileName), fileURL, 1, 10, False):
                        logging.info("downloaded: " + fileName)
                        downloadCount += 1
                    else:
                        logging.warning("error:" + fileName)
                        errorCount += 1

    # phase 2 - remove any local files that are not in the list provided by the web service

    localFiles = [filename for filename in os.listdir(localDir) if isfile(join(localDir, filename))]

    logging.info(f"Checking {len(localFiles)} local files in {localDir}")

    filesToRemove = [filename for filename in localFiles if filename not in allFileNames]

    for filename in filesToRemove:
        filePath = join(localDir, filename)
        logging.info(f"Removing: {filePath}")
        try:
            os.remove(filePath)
            removeCount += 1
        except OSError:
            logging.error(f"Error trying to remove file {filePath}")

except:
    PrintException()

logging.info(f"Errors: {errorCount}  Downloaded: {downloadCount}  Updated: {updateCount}  Existing: {existCount}  Removed: {removeCount}")
print(f"Errors: {errorCount}  Downloaded: {downloadCount}  Updated: {updateCount}  Existing: {existCount}  Removed: {removeCount}")
