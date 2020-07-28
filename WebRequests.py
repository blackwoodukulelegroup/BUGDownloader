import requests
import logging

requestHeaders = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}

proxies = None


def GetWebResource(url, maxAttempts, timeout):
    attemptCounter = 0
    successFlag = 0
    while (attemptCounter < maxAttempts) and (successFlag == 0):
        logging.debug("- attempt {0}".format(attemptCounter + 1))
        try:
            if proxies is None:
                response = requests.get(url, headers=requestHeaders, timeout=timeout)
            else:
                response = requests.get(url, headers=requestHeaders, proxies=proxies, timeout=timeout)

            if response.status_code == 200:
                successFlag = 1
            else:
                logging.warning("Requests.Get failed: {0}".format(response.status_code))
                attemptCounter += 1
        except requests.exceptions.RequestException as e:
            logging.exception("GetWebResource Error: {0}".format(e))
            attemptCounter += 1

    if successFlag == 1:
        return response
    else:
        return None


# if testMode is True, a local file will be created, but download won't take place
def DownloadFile(localFilename, url, maxAttempts, timeout, testMode):
    logging.debug("DownloadFile: downloading {} to {}".format(url, localFilename))
    if (testMode == True):
        try:
            localFile = open(localFilename, "wt")
            localFile.write("test")
            localFile.close()
            return True
        except:
            logging.exception("DownloadFile_TestMode: {0}".format(sys.exc_info()[0]))
        return False
    else:
        resource = GetWebResource(url, maxAttempts, timeout)
        if (resource is not None and len(resource.content) > 0):
            try:
                localFile = open(localFilename, "wb")
                localFile.write(resource.content)
                localFile.close()
                return True
            except:
                logging.exception("DownloadFile: {0}".format(sys.exc_info()[0]))
        else:
            return False
