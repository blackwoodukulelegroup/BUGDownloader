import requests
import logging
import sys

requestHeaders = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}

proxies = None

def GetHeader(url, header, timeout):
    logging.debug(f"GetHeader(url='{url}' header='{header}' timeout={timeout})")
    try:
        if proxies is None:
            response = requests.head(url, headers=requestHeaders, timeout=timeout)
        else:
            response = requests.head(url, headers=requestHeaders, proxies=proxies, timeout=timeout)

        if header in response.headers:
            return response.headers[header]

    except requests.exceptions.RequestException as e:
        logging.exception(f"GetHeader Error: {e}")

    return None


def GetWebResource(url, maxAttempts, timeout):
    logging.debug(f"GetWebResource(url='{url}' maxAttempts={maxAttempts} timeout={timeout})")
    attemptCounter = 0
    successFlag = 0
    response = None
    while (attemptCounter < maxAttempts) and (successFlag == 0):
        logging.debug(f"- attempt {attemptCounter + 1} of {maxAttempts}")
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
    logging.debug(F"DownloadFile(localFileName='{localFilename}' url='{url}' " +
                  f"maxAttempts={maxAttempts} timeout={timeout} testMode={testMode}")
    if testMode:
        try:
            localFile = open(localFilename, "wt")
            localFile.write("test")
            localFile.close()
            return True
        except:
            logging.exception(f"DownloadFile_TestMode: {sys.exc_info()[0]}")
        return False
    else:
        resource = GetWebResource(url, maxAttempts, timeout)
        if resource is not None and len(resource.content) > 0:
            try:
                localFile = open(localFilename, "wb")
                localFile.write(resource.content)
                localFile.close()
                return True
            except:
                logging.exception(f"DownloadFile: {sys.exc_info()[0]}")
        else:
            return False
