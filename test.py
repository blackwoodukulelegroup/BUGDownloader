import sys
import os
import json
import requests
import re

localDir = "/home/pi/Ukulele/BUG Chord Charts"
# localDir = "/home/pi/Scripts/BUGDownloader/test"

dirSep = "/"

apiURL = "https://script.google.com/macros/s/AKfycbx-0s1grPv0Wj_wXZUDRggB7Eac_c4TGHkMQ1aNOcNv41eCeg/exec"

proxies = None

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
                response = requests.get(url, timeout=timeout)
            else:
                response = requests.get(url, proxies=proxies, timeout=timeout)
            
            response.raise_for_status()

            successFlag = 1
        except:
            attemptCounter +=1

    if successFlag == 1:
        return response
    else:
        return None
    
def DownloadFile(localFilename, url, proxies, maxAttempts, timeout):
    print("- downloading {} to {}".format(url, localFilename))
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

    for songKey in bugSongs:
        song = bugSongs[songKey]
        fileNameBase = song['title'] + ' - ' + song['artist']
        songURLs = song['URL']
        for urlKey in songURLs:
            fileName = (fileNameBase + ' - ' + urlKey + '.pdf').replace('/','_').replace('\\','_')
            fileURL = songURLs[urlKey]
            if (re.search('drive|scorpex', fileURL)):
                if os.path.isfile(localDir + dirSep + fileName):
                    res = requests.head(fileURL, allow_redirects=True)
                    if 'Last-Modified' in res.headers:
                        print("exists: " + fileName, res.headers['Last-Modified'])
                    else:
                        print("exists: " + fileName)
                else:
                    if DownloadFile(localDir + dirSep + fileName, fileURL, proxies, 1, 10):
                        print("downloaded: " + fileName)
                    else:
                        print("error:" + fileName)

except:
    PrintException()
    # errType, errValue, errTraceback = sys.exc_info()
    # print(errType)
    # print(errValue)
    # print(errTraceback)

print("finished")