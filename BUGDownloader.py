import linecache
import sys
import os
import json
import requests
import re
import platform

if platform.system() == 'Windows':
    dirSep = "\\"
    localDir = "C:\\Repos\\BUGDownloader\\test"
else:
    dirSep = "/"
    # localDir = "/home/pi/Ukulele/BUG Chord Charts"
    localDir = "/home/pi/Scripts/BUGDownloader/test"

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
    while attemptCounter < maxAttempts and successFlag == 0:
        try:
            if proxies is None:
                response = requests.get(url, timeout=timeout, headers=requestHeaders)
            else:
                response = requests.get(url, proxies=proxies, timeout=timeout, headers=requestHeaders)
            
            response.raise_for_status()

            successFlag = 1
        except:
            attemptCounter +=1

    if successFlag == 1:
        return response
    else:
        return None

def DownloadFile(localFilename, url, proxies, maxAttempts, timeout):
    resource = GetWebResource(url, proxies, maxAttempts, timeout)
    if ( resource is not None and len(resource.content) > 0):
        localFile = open(localFilename, "wb")
        localFile.write(resource.content)
        localFile.close()
        return True
    else:
        return False

try:
    apiResult = GetWebResource(apiURL, proxies, 5, 30)
    bugSongs = json.loads(apiResult.text)

    print("Found {0} songs to download".format(len(bugSongs)))

    errorList = []
    progress = {'errors': 0, 'existing': 0, 'downloaded': 0}

    for songKey in bugSongs:

        print('\rErrors: {0}  Downloaded: {1}  Existing: {2} ... '.format(progress['errors'], progress['downloaded'], progress['existing']), end='')
              
        song = bugSongs[songKey]
        fileNameBase = song['title'] + ' - ' + song['artist']
        songURLs = song['URL']
        for urlKey in songURLs:
            fileName = (fileNameBase + ' - ' + urlKey + '.pdf').replace('/','_').replace('\\','_').replace('?','')
            fileURL = songURLs[urlKey]
            if (re.search('drive|scorpex|ozbcoz', fileURL)):
                if os.path.isfile(localDir + dirSep + fileName):
                    progress['existing'] += 1
                else:
                    if DownloadFile(localDir + dirSep + fileName, fileURL, proxies, 1, 10):
                        progress['downloaded'] += 1
                    else:
                        progress['errors'] += 1
                        errorList.append(fileName)

    print('finished')
    
    if len(errorList) > 0:
        print("failed downloads:")
        for errorFile in errorList:
            print(errorFile)

except:
    PrintException()
    # errType, errValue, errTraceback = sys.exc_info()
    # print(errType)
    # print(errValue)
    # print(errTraceback)

print("finished")
