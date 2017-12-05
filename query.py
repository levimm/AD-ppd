#coding=utf-8
from openapi_client import openapi_client as client
from core.rsa_client import rsa_client as rsa
from core.http import http_client
import pickle
import json
import os
import sys

appid="c1cd94864da5425499655ee6d8f38b6e"

access_url = "http://gw.open.ppdai.com/invest/LLoanInfoService/BatchListingInfos"
data = {
  "ListingIds": sys.argv
}
sort_data = rsa.sort(data)
sign = rsa.sign(sort_data)
list_result = client.send(access_url, json.dumps(data), appid, sign)

list_obj = json.loads(list_result)
print(json.dumps(list_obj, indent=4, sort_keys=True))
