import linecache
import sys
import os
import json
import requests
import re

localDir = "/home/pi/Ukulele/BUG Chord Charts"
# localDir = "/home/pi/Scripts/BUGDownloader/test"

requestHeaders = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}

dirSep = "/"

apiURL = "https://script.google.com/macros/s/AKfycbx-0s1grPv0Wj_wXZUDRggB7Eac_c4TGHkMQ1aNOcNv41eCeg/exec"

proxies = None
# proxies = {'http': '127.0.0.1:8888', 'https': '127.0.0.1:8888'}

requestHeaders = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'}

def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))
    
def GetWebResource(url, proxies, maxAttempts, timeout):

    attemptCounter = 0
    successFlag = 0
    while (attemptCounter < maxAttempts) and (successFlag == 0):
        print("- attempt {0}".format(attemptCounter + 1))
        try:
            if proxies is None:
                response = requests.get(url, headers=requestHeaders, timeout=timeout)
            else:
                response = requests.get(url, headers=requestHeaders, proxies=proxies, timeout=timeout)
            
            if response.status_code == 200:
                successFlag = 1
            else:
                print("Requests.Get failed: {0}".format(response.status_code))
                attemptCounter += 1
            
            # response.raise_for_status()

            # successFlag = 1
        except requests.exceptions.RequestException as e:
            print("GetWebResource Error: {0}".format(e))
            attemptCounter +=1

    if successFlag == 1:
        return response
    else:
        return None
    
def DownloadFile(localFilename, url, proxies, maxAttempts, timeout, testMode):
    print("DownloadFile: downloading {} to {}".format(url, localFilename))
    if ( testMode == True ):
        try:
            localFile =  open(localFilename, "wt")
            localFile.write("test")
            localFile.close()
            # if (os.path.exists(localFilename)):
                    # os.remove(localFilename)
            return True
        except:
            print("DownloadFile_TestMode: {0}".format(sys.exc_info()[0]))
        return False
    else: 
        resource = GetWebResource(url, proxies, maxAttempts, timeout)
        if ( resource is not None and len(resource.content) > 0):
            try:
                localFile = open(localFilename, "wb")
                localFile.write(resource.content)
                localFile.close()
                return True
            except:
                print("DownloadFile: {0}".format(sys.exc_info()[0]))
        else:
            return False

downloadCount = 0
existCount = 0
errorCount = 0

try:
    apiResult = GetWebResource(apiURL, proxies, 5, 30)
    bugSongs = json.loads(apiResult.text)

    print("Found {0} songs to download".format(len(bugSongs)))

    errorList = []
    progress = {'errors': 0, 'existing': 0, 'downloaded': 0}

    for songKey in bugSongs:
        print("SongKeyLoop:  Key = {0}".format(songKey))
        song = bugSongs[songKey]
        print("SongKeyLoop: Title = {0}  Artist = {1}".format(song['title'],song['artist']))
        fileNameBase = song['title'] + ' - ' + song['artist']
        print("SongKeyLoop: fileNameBase = {0}".format(fileNameBase))
        songURLs = song['URL']
        for urlKey in songURLs:
            print("UrlKeyLoop: Key = {0}".format(urlKey))
            fileName = (fileNameBase + ' - ' + urlKey + '.pdf').replace('/','_').replace('\\','_').replace('⁄','_')
            print("UrlKeyLoop: FileName = {0}".format(fileName))
            fileURL = songURLs[urlKey]
            if (re.search('scorpex|ozbcoz|drive', fileURL)):
                if os.path.isfile(localDir + dirSep + fileName):
                    existCount += 1
                    print("exists: " + fileName)
                else:
                    print("downloading: " + fileName)
                    if DownloadFile(localDir + dirSep + fileName, fileURL, proxies, 1, 10, False):
                        print("downloaded: " + fileName)
                        downloadCount += 1
                    else:
                        print("error:" + fileName)
                        errorCount += 1

except:
    PrintException()
    # errType, errValue, errTraceback = sys.exc_info()
    # print(errType)
    # print(errValue)
    # print(errTraceback)

print("Errors: {0}  Downloaded: {1}  Existing: {2}".format(errorCount, downloadCount, existCount))

print("finished")
