#coding=utf-8
import urllib
import urllib.request
import logging

class http_client:

    REQUEST_HEADER = {'Connection': 'keep-alive',
                  'Cache-Control': 'max-age=0',
                  #'Accept-Encoding': 'gzip, deflate, sdch',
                  'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
                  'Content-Type':'application/json;charset=utf-8'
                  }

    
    '''
    return (status_code, response_str)
    '''
    @staticmethod
    def http_post(url,data,headers={}):
        try:
            req = urllib.request.Request(url)

            for header in http_client.REQUEST_HEADER:
                req.add_header(header, http_client.REQUEST_HEADER[header])

            for head in headers:
                req.add_header(head, headers[head])

            # add proxy if required
            proxy_handler = urllib.request.ProxyHandler({'https': 'web-proxy.sgp.hp.com:8080', 'http': 'web-proxy.sgp.hp.com:8080'})

            opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPCookieProcessor())
            response = opener.open(req,data = data ,timeout=5)

            if response.getcode() == 200:
                return response.getcode(), response.read()
            else: 
                return response.getcode(), None
#             data = StringIO.StringIO(response.read())
#             gzipper = gzip.GzipFile(fileobj=data)
#             return gzipper.read()
        except:
            logging.error("hhhhhh")
            return None, None
