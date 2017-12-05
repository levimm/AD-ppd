#coding=utf-8
from openapi_client import openapi_client as client
from core.rsa_client import rsa_client as rsa
from core.http import http_client
import pickle
import json
import time
from datetime import datetime
from datetime import timedelta
from time import gmtime, strftime
import os
import base64
import logging
import logging.handlers
import math

appid="c1cd94864da5425499655ee6d8f38b6e"
#https://ac.ppdai.com/oauth2/login?AppID=c1cd94864da5425499655ee6d8f38b6e&ReturnUrl=http://antdiaries.com
code = "d15ddd6aad244560be73ac7884b98fcc"

root_logger= logging.getLogger()
root_logger.setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler('autobid.log', 'r+', maxBytes=1024*1024, backupCount=100, encoding='utf-8')
formatter = logging.Formatter('[%(asctime)s] - [%(levelname)s] - %(message)s')
handler.setFormatter(formatter)
root_logger.addHandler(handler)

def get_authorize_str():
    try:
        path = os.path.join(os.path.dirname(__file__), 'returncode.txt')
        with open(path, 'r+') as f:
            content = f.read()
            if content =='':
                authorize_str = client.authorize(appid=appid,code=code) 
                authorize_obj = json.loads(authorize_str) 
                #{"OpenID":"xx","AccessToken":"xxx","RefreshToken":"xxx","ExpiresIn":604800}
                access_token = authorize_obj['AccessToken']
                f.write(access_token)
                return access_token
            else:
                return content
    except Exception as e:
        print(e)

###
# get loan list
###
def get_loan_list(index, date = None): # date "2015-11-11 12:00:00.000"
    access_url = "http://gw.open.ppdai.com/invest/LLoanInfoService/LoanList"
    if date is None:
        data = {
            "PageIndex": index
        }
    else:
        data =  {
            "PageIndex": index, 
            "StartDateTime": date
        }
    sort_data = rsa.sort(data)
    sign = rsa.sign(sort_data)
    list_result = client.send(access_url, json.dumps(data), appid, sign)

    # check result
    list_result_obj = json.loads(list_result)
    if list_result_obj["Result"] == 1:
        return list_result_obj
    else:
        logging.warning("Error: fail to get load list.")
        print("Error: fail to get load list.")
        return None

###
# get loan detail list
# parameter
#[
#            23886149,
#            23886150
#        ]
###
def get_loan_detail_list(idList):
    access_url = "http://gw.open.ppdai.com/invest/LLoanInfoService/BatchListingInfos"
    data = {
        "ListingIds": idList
    }
    sort_data = rsa.sort(data)
    sign = rsa.sign(sort_data)
    list_result = client.send(access_url, json.dumps(data), appid, sign)

    # check result
    list_result_obj = json.loads(list_result.decode('utf-8'))
    if list_result_obj["Result"] == 1:
        return list_result_obj
    else:
        logging.warning("Error: fail to get load detail list.")
        print("Error: fail to get load detail list.")
        return None



###
# make real bid here
###
def make_bid(listing_id, amount):
    access_url = "http://gw.open.ppdai.com/invest/BidService/Bidding"
    access_token = get_authorize_str()
    data = {
        "ListingId": listing_id, 
        "Amount": amount,
        "UseCoupon":"true"
    }
    sort_data = rsa.sort(data)
    sign = rsa.sign(sort_data)
    list_result = client.send(access_url, json.dumps(data), appid, sign,access_token)
    
    # check result
    list_result_obj = json.loads(list_result)
    if list_result_obj["Result"] == 0:
        return list_result_obj
    else:
        logging.warning("Warning: fail to make bid %s. Reason: %s", listing_id, list_result_obj["ResultMessage"])
        print("Warning: fail to make bid %s. Reason: %s. Code: %s" % (listing_id, list_result_obj["ResultMessage"], list_result_obj["Result"]))
        return None


###
# ifttt notification
###
def trigger_ifttt(event, value1, value2, value3):
    print("ready to trigger ifttt")
    logging.info("ready to trigger ifttt")
    trigger_url = "https://maker.ifttt.com/trigger/%s/with/key/dYb4ZEIKS2NZKWhWI5TMww" % event
    data = {
        "value1": value1,
        "value2": value2,
        "value3": value3
    }
    status_code, response = http_client.http_post(trigger_url, json.dumps(data).encode("utf-8"))
    if status_code == 200:
        print("ifttt trigger event sent.")
        logging.info("ifttt trigger event sent.")


###
# Bid AA
###
def bid_aa():
    request_date = str(datetime.now() + timedelta(minutes=-5))
    init_index = 1
    list_result_obj = get_loan_list(init_index, request_date)
    result = []
    if len(list_result_obj["LoanInfos"]) == 0:
        logging.info("Empty Loan list.")
        print("Empty Loan list %s" % str(datetime.now()))
        return None

    while True:
        for i in list_result_obj["LoanInfos"]:
            if i["CreditCode"] == "AA" and i["Rate"] >= 8:
                obj = make_bid(i["ListingId"], 500)
                if obj is not None:
                    logging.info("Success to bid AA %s", i["ListingId"])
                    print("Success to bid AA %s" % i["ListingId"])
                    trigger_ifttt("bid_aa", obj["ListingId"], obj["ParticipationAmount"], obj["ResultMessage"])
            else:
                logging.info("%s - %s", i["CreditCode"], i["ListingId"])
                print("%s - %s" % (i["CreditCode"], i["ListingId"]))
        
        if len(list_result_obj) < 2000:
            break
        else:
            init_index = init_index + 1
            list_result_obj = get_loan_list(init_index, request_date)

    return result


###
# checkSpecific_constraints
###

def checkSpecific_constraints(loan):
    if loan["CurrentRate"] < 16:
        return False

    # first filter on educate validate
    if loan["GraduateSchool"] is None:
        return False

    # second filter on OverdueMoreCount
    if loan["OverdueMoreCount"] > 0:
        return False
    if loan["OverdueLessCount"] > 5:
        return False

    # third filter on new guys
    if loan["NormalCount"] < 3 or loan["SuccessCount"] < 3:
        return False

    # fourth filter on large amount
    if loan["OwingAmount"] == 0 and loan["Amount"] >= 5000:
        return False
    if loan["Amount"] > 10000:
        return False
    if loan["OwingAmount"]/loan["HighestDebt"] > 0.8:
        return False
    if loan["Amount"]/loan["HighestPrincipal"] > 0.85:
        return False

    # if loan["CreditCode"] == "A":
    #     #if loan["SuccessCount"] >= 3 and loan["OverdueLessCount"] <= 5 and loan["NormalCount"] >=3
    #     return True
    # elif loan["CreditCode"] == "B":
    #     if loan["SuccessCount"] >= 5 and loan["OverdueLessCount"] <= 3 and loan["NormalCount"] >=5:
    #         return True
    # elif loan["CreditCode"] == "C":
    #     if loan["SuccessCount"] >= 7 and loan["OverdueLessCount"] <= 1 and loan["NormalCount"] >=7:
    #         return True
    # else:
    #     return False

    return True

###
# tmp bid
###
def bid_specific_constraints():
    request_date = str(datetime.now() + timedelta(minutes=-10))
    init_index = 1

    list_result_obj = get_loan_list(init_index, request_date)
    loan_info_list = list_result_obj["LoanInfos"]
    loan_list_length = len(loan_info_list)
    if loan_list_length == 0:
        return

    query_count = math.ceil(loan_list_length / 10)
    for i in range(0, query_count):
        listingIds = []
        period = loan_list_length - 10 * i
        period_length = 10
        if period < 10:
            period_length = period

        for j in range(0, period_length):
            #print(loan_info_list[10 * i + j])
            listingIds.append(loan_info_list[10 * i + j]['ListingId'])

        detail_result = get_loan_detail_list(listingIds)
        if detail_result is not None:
            detail_loan_list = detail_result["LoanInfos"]
            for loan in detail_loan_list:
                isSatisfied = checkSpecific_constraints(loan)
                if isSatisfied == True:
                    print("success", loan["ListingId"])
                    #obj = make_bid(loan["ListingId"], 50)
                    #if obj is not None:
                    #logging.info("Success to bid %s - %s", loan["CreditCode"], loan["ListingId"])
                    #print("Success to bid %s - %s" % (loan["CreditCode"], loan["ListingId"]))
                    trigger_ifttt("bid_aa", loan["ListingId"], loan["CreditCode"], loan["CreditCode"])



###
# tmp bid
###
def tmp_bid():
    request_date = str(datetime.now() + timedelta(minutes=-5))
    init_index = 1
    list_result_obj = get_loan_list(init_index, request_date)

    if len(list_result_obj["LoanInfos"]) == 0:
        logging.info("Empty Loan list.")
        print("Empty Loan list %s" % str(datetime.now()))
        return None

    bid_list = list_result_obj["LoanInfos"]
    obj = make_bid(bid_list[0]["ListingId"], -1)
    

print(str(datetime.now()))
while True:
    try:
        bid_specific_constraints()
    # catch all unexpected exceptions
    except Exception as e:
        logging.error(e)
        time.sleep(30)

while False:
    try:
        bid_aa()
        time.sleep(0.1)
    # catch all unexpected exceptions
    except Exception as e:
        logging.error(e)
        time.sleep(30)


# data = json.load(open('data.json'))

#加密/解密
# encrypt_data = "ta5346sw34rfe"
# encrypted = rsa.encrypt(encrypt_data)
# decrypt = rsa.decrypt(encrypted)
# print decrypt
