#coding=utf-8

from openapi_client import openapi_client as client
from core.rsa_client import rsa_client as rsa
from core.http import http_client
import json
import time
from datetime import datetime
from datetime import timedelta
import os
import base64
import logging
import math


appid="c1cd94864da5425499655ee6d8f38b6e"
#https://ac.ppdai.com/oauth2/login?AppID=c1cd94864da5425499655ee6d8f38b6e&ReturnUrl=http://antdiaries.com
code = "d15ddd6aad244560be73ac7884b98fcc"


'''
trigger the email notify about event happened
'''
def trigger_ifttt(event, value1, value2, value3):
    logging.info("ready to trigger ifttt")
    trigger_url = "https://maker.ifttt.com/trigger/%s/with/key/dYb4ZEIKS2NZKWhWI5TMww" % event
    data = {
        "value1": value1,
        "value2": value2,
        "value3": value3
    }

    status_code, response = http_client.http_post(trigger_url, json.dumps(data).encode("utf-8"))
    if status_code == 200:
        logging.info("ifttt trigger event sent.")
        return 0
    else:
        logging.warning("ifttt trigger failed with status code %s", status_code)
        return -1

'''
get authorize string
'''
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


'''
make bid with listing id and amount
'''
def make_bid(listing_id, amount):
    access_url = "http://gw.open.ppdai.com/invest/BidService/Bidding"
    access_token = "1ff70da4-909e-4ce0-ab17-0f75debd5c1d"
    data = {
        "ListingId": listing_id, 
        "Amount": amount,
        "UseCoupon":"true"
    }
    sort_data = rsa.sort(data)
    sign = rsa.sign(sort_data)
    list_result = client.send(access_url, json.dumps(data), appid, sign, access_token)

    # check result
    list_result_obj = json.loads(list_result)
    if list_result_obj["Result"] == 0:
        logging.info("Success to bid %s", listing_id)
        return list_result_obj
    else:
        logging.warning("Warning: fail to make bid %s. Reason: %s", listing_id, list_result_obj["ResultMessage"])
        return None



'''
get loan list that can still be bid
'''
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
        logging.error("Fail to get loan list.")
        return None


'''
get detail loan list
'''
def get_loan_detail_list(listing_ids):
    access_url = "http://gw.open.ppdai.com/invest/LLoanInfoService/BatchListingInfos"
    data = {
        "ListingIds": listing_ids
    }
    sort_data = rsa.sort(data)
    sign = rsa.sign(sort_data)
    list_result = client.send(access_url, json.dumps(data), appid, sign)

    # check result
    list_result_obj = json.loads(list_result.decode('utf-8'))
    if list_result_obj["Result"] == 1:
        return list_result_obj
    else:
        logging.error("Fail to get detail loan list.")
        return None



'''
filter credit loan according to specific constrains
'''
def check_specific_constrains(loan):
    if loan["CurrentRate"] < 16 or loan["CurrentRate"] > 20:
        return False

    # first filter on educate validate
    if loan["GraduateSchool"] is None:
        return False

    # second filter on new guys, NormalCount=正常还款次数  SuccessCount=成功借款次数
    if loan["NormalCount"] < 5 or loan["SuccessCount"] < 3:
        return False

    # thrid filter on OverdueCount
    if loan["OverdueMoreCount"] > 0:
        return False
    if loan["OverdueLessCount"]/loan["NormalCount"] > 0.1:
        return False

    # fourth filter on large amount, OwingAmount=当前待还金额  Amount=本次借款金额  HighestDebt=历史最高负债  HighestPrincipal=历史最高借款
    if loan["OwingAmount"] == 0 and loan["Amount"] > 5000:
        return False
    if loan["Amount"] > 10000 or loan["OwingAmount"] > 20000:
        return False
    if loan["OwingAmount"]/loan["HighestDebt"] > 0.8:
        return False
    if loan["Amount"]/loan["HighestPrincipal"] > 0.9:
        return False

    if loan["CreditCode"] == "A":
        return True
    elif loan["CreditCode"] == "B":
        if loan["SuccessCount"] >= 5 and loan["OverdueLessCount"] <= 3 and loan["NormalCount"] >=10:
            return True
    elif loan["CreditCode"] == "C":
        if loan["SuccessCount"] >= 5 and loan["OverdueLessCount"] <= 1 and loan["NormalCount"] >=15:
            return True
    else:
        return False

    return False

class antdiaries_client:

    def __init__(self, params):
        '''
        Constructor
        '''
    

    '''
    bid aa
    '''
    @staticmethod
    def bid_aa():
        request_date = str(datetime.now() + timedelta(minutes=-5))
        init_index = 1
        list_result_obj = get_loan_list(init_index, request_date)
        if len(list_result_obj["LoanInfos"]) == 0:
            logging.info("Empty Loan list.")
            return

        while True:
            for i in list_result_obj["LoanInfos"]:
                if i["CreditCode"] == "AA" and i["Rate"] >= 8:
                    obj = make_bid(i["ListingId"], 500)
                    if obj is not None:
                        logging.info("Success to bid AA %s", i["ListingId"])
                        trigger_ifttt("bid_aa", obj["ListingId"], obj["ParticipationAmount"], obj["ResultMessage"])
            
            if len(list_result_obj["LoanInfos"]) < 2000:
                break
            else:
                init_index = init_index + 1
                list_result_obj = get_loan_list(init_index, request_date)

        return


    '''
    bid risky
    '''
    @staticmethod
    def bid_risky():
        request_date = str(datetime.now() + timedelta(minutes=-5))
        
        list_result_obj = get_loan_list(1, request_date)
        loan_info_list = list_result_obj["LoanInfos"]
        loan_list_length = len(loan_info_list)
        if loan_list_length == 0:
            logging.info("Empty loan list.")
            return

        listingIds = []
        for i in list_result_obj["LoanInfos"]:
            if i["CreditCode"] == "A" or i["CreditCode"] == "B" or i["CreditCode"] == "C":
                if i["Amount"] <= 10000 and i["RemainFunding"]/i["Amount"] >= 0.05:
                    listingIds.append(i["ListingId"])
            
            # only get detail info for 5 loans every time
            if len(listingIds) >= 5:
                detail_result = get_loan_detail_list(listingIds)
                listingIds = []
                if detail_result is not None:
                    detail_loan_list = detail_result["LoanInfos"]
                    for loan in detail_loan_list:
                        if loan["RemainFunding"] < 50:
                            continue
                        is_satisfied = check_specific_constrains(loan)
                        if is_satisfied == True:
                            logging.info("Trying to bid %s with %s left amount", loan["ListingId"], loan["RemainFunding"])
                            obj = make_bid(loan["ListingId"], 100)
                            if obj is not None:
                                logging.info("Success to bid %s - %s", loan["CreditCode"], loan["ListingId"])
                                trigger_ifttt("bid_risky", loan["ListingId"], loan["CreditCode"], obj["ParticipationAmount"])
                        else:
                            logging.info("Not qualified bid %s", loan["ListingId"])
        
        # not enough 5 pre-qualified loan in list
        if len(listingIds) > 0:
            detail_result = get_loan_detail_list(listingIds)
            if detail_result is not None:
                detail_loan_list = detail_result["LoanInfos"]
                for loan in detail_loan_list:
                    if loan["RemainFunding"] < 50:
                        continue
                    is_satisfied = check_specific_constrains(loan)
                    if is_satisfied == True:
                        logging.info("Trying to bid %s with %s left amount", loan["ListingId"], loan["RemainFunding"])
                        obj = make_bid(loan["ListingId"], 100)
                        if obj is not None:
                            logging.info("Success to bid %s - %s", loan["CreditCode"], loan["ListingId"])
                            trigger_ifttt("bid_risky", loan["ListingId"], loan["CreditCode"], obj["ParticipationAmount"])
                    else:
                        logging.info("Not qualified bid %s", loan["ListingId"])
