#coding=utf-8

from core.http import http_client
from core.rsa_client import rsa_client as rsa
import datetime
import gzip
import time
try:
    import StringIO
except ImportError:
    from io import StringIO
import json


class openapi_client:
    
    AUTHORIZE_URL = "https://ac.ppdai.com/oauth2/authorize"
    
    REFRESHTOKEN_URL = "https://ac.ppdai.com/oauth2/refreshtoken"


    def __init__(self, params):
        '''
        Constructor
        '''
    
    @staticmethod
    def authorize(appid,code):
        data = "{\"AppID\":\"%s\",\"Code\":\"%s\"}" % (appid,code)
        data = data.encode("utf-8")
        result = http_client.http_post(openapi_client.AUTHORIZE_URL,data)
        #result = gzip.GzipFile(fileobj=StringIO.StringIO(result),mode="r")
        #result = result.read().decode("gbk").encode("utf-8")
        # print("authorize_data:%s" % (result))
        return result
        

    @staticmethod
    def refresh_token(appid,openid,refreshtoken):
        data = "{\"AppID\":\"%s\",\"OpenId\":\"%s\",\"RefreshToken\":\"%s\"}" % (appid,openid,refreshtoken)
        result = http_client.http_post(openapi_client.REFRESHTOKEN_URL,data)
        print("refresh_token_data:%s" % (result))
        return result
    
    
    @staticmethod
    def send(url,data,appid,sign,accesstoken=''):
        utctime = datetime.datetime.utcnow()
        timestamp = utctime.strftime('%Y-%m-%d %H:%M:%S')
        headers = {"X-PPD-APPID":appid,
                   "X-PPD-SIGN":sign,
                   "X-PPD-TIMESTAMP":timestamp,
                   "X-PPD-TIMESTAMP-SIGN":rsa.sign("%s%s" % (appid,timestamp)),
                   "Accept":"application/json;charset=UTF-8"}
        if accesstoken.strip():
            headers["X-PPD-ACCESSTOKEN"] = accesstoken
        status_code, response_str = http_client.http_post(url,data.encode('utf-8'),headers=headers)

        while status_code != 200 or response_str is None:
            print("Servie unavailable for a while:", status_code)
            time.sleep(10)
            status_code, response_str = http_client.http_post(url,data.encode('utf-8'),headers=headers)
        
        return response_str
        
        
        