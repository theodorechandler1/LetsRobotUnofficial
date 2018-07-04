from urllib.request import urlopen
from urllib.error import URLError
import time

class ServerHelper:

    @staticmethod
    def isInternetConnected():
        ''' Checks to see if google is available. Assumes you have internet access if that is the case. '''
        try:
            urlopen('https://www.google.com', timeout=1)
            return True
        except URLError as err:
            return False 
            
    @staticmethod
    def getWithRetry(url, secure=True):
        for retryNumber in range(2000):
            try:
                if secure:
                    response = urlopen(url).read()
                else:
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    response = urlopen(url, context=ctx).read()
                break
            except URLError:
                #Could not open url
                #traceback.print_exc()
                time.sleep(2)
        return response