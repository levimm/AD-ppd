#coding=utf-8
from antdiaries_client import antdiaries_client as client
import time
from datetime import datetime
import os
import logging
import logging.handlers
import sys


root_logger= logging.getLogger()
root_logger.setLevel(logging.INFO)
console = logging.StreamHandler(sys.stdout)
handler = logging.handlers.RotatingFileHandler('autobid.log', 'r+', maxBytes=1024*1024, backupCount=100, encoding='utf-8')
formatter = logging.Formatter('[%(asctime)s] - [%(levelname)s] - %(message)s')
handler.setFormatter(formatter)
root_logger.addHandler(console)
root_logger.addHandler(handler)





print(str(datetime.now()))

retry_count = 0
while True:
    try:
        client.bid_aa()
        retry_count = 0
    except RuntimeError as e:
        logging.error(e)
        retry_count = retry_count + 1
        time.sleep(10 * retry_count)
    except Exception as ex:
        logging.error("Unexpected error!")
        retry_count = retry_count + 1
        time.sleep(10 * retry_count)

# while True:
#     try:
#         bid_aa()
#         time.sleep(0.1)
#     # catch all unexpected exceptions
#     except Exception as e:
#         logging.error(e)
#         time.sleep(30)



#加密/解密
# encrypt_data = "ta5346sw34rfe"
# encrypted = rsa.encrypt(encrypt_data)
# decrypt = rsa.decrypt(encrypted)
# print decrypt
