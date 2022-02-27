import requests
import json
import datetime
from dateutil.relativedelta import relativedelta, MO

from .parser import get_transactions
from .models import UserConsent
import os

import boto3
import botocore
from boto3.dynamodb.conditions import Key, Attr

def trigger_consent_request(mobile_number):
    url = "https://fiu-uat.setu.co/consents"

    consent_start_obj = datetime.datetime.now()
    consent_start = consent_start_obj.strftime("%Y-%m-%dT%H:%M:%SZ")
    consent_end = (consent_start_obj + relativedelta(years = 2)).strftime("%Y-%m-%dT%H:%M:%SZ")

    payload = json.dumps({
        "Detail": {
            "consentStart": consent_start,
            "consentExpiry": consent_end,
            "Customer": {
                "id": mobile_number + "@onemoney"
            },
            "FIDataRange": {
                "from": "2021-04-01T00:00:00Z",
                "to": "2021-10-01T00:00:00Z"
            },
            "consentMode": "STORE",
            "consentTypes": [
                "TRANSACTIONS",
                "PROFILE",
                "SUMMARY"
            ],
            "fetchType": "PERIODIC",
            "Frequency": {
                "value": 30,
                "unit": "MONTH"
            },
            "DataLife": {
                "value": 1,
                "unit": "MONTH"
            },
            "DataConsumer": {
                "id": "setu-fiu-id"
            },
            "Purpose": {
                "Category": {
                    "type": "string"
                },
                "code": "102",
                "text": "Personal wealth management application",
                "refUri": "https://api.rebit.org.in/aa/purpose/102.xml"
            },
            "fiTypes": [
                "DEPOSIT"
            ]
        },
        "redirectUrl": "http://35.86.252.148:5000/consent/confirm/"
    })
    headers = {
        'x-client-id': os.getenv("client_id"),
        'x-client-secret': os.getenv("client_secret"),
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 201:
        ob = json.loads(response.content)
        UserConsent.objects.create(
            consent_id = ob['id'],
            consent_start = consent_start,
            consent_end = consent_end,
            customer_id = mobile_number + "@onemoney"
        )
        return True, ob['url']
    else:
        print(response.content, "82")
        return False, None

def check_consent_status(consent_id):
    url = "https://fiu-uat.setu.co/consents/" + consent_id

    payload={}
    headers = {
        'x-client-id': os.getenv("client_id"),
        'x-client-secret': os.getenv("client_secret"),
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    response_content = json.loads(response.content)
    return response_content["status"]

def create_data_session(consent_id):
    url = "https://fiu-uat.setu.co/sessions"
    
    payload = json.dumps({
        "consentId": consent_id,
        "DataRange": {
            "from": "2021-04-01T00:00:00Z",
            "to": "2021-09-30T00:00:00Z"
        },
        "format": "json"
    })
    headers = {
        'x-client-id': os.getenv("client_id"),
        'x-client-secret': os.getenv("client_secret"),
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    response_content = json.loads(response.content)
    print(response_content, "116")
    if 'errorCode' in response_content:
        return 'ERROR', None
    else:
        return response_content["status"], response_content["id"]

def check_if_file_exists_and_update(customer_id, data):
    s3 = boto3.resource('s3')
    try:
        s3_object = s3.Object('vis-devfolio-bucket', "data/" + customer_id + '.json')
        s3_object.load()
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            # write_new_file_to_s3
            s3_object.put(
                Body=(bytes(json.dumps({
                    "transactions": data
                }).encode('UTF-8')))
            )
        else:
            print(e, "136")
    else:
        # get object, and update
        s3_data = s3_object.get()['Body'].read().decode('utf-8')
        json_data = json.loads(s3_data)
        txnIDs = [txn["txn_id"] for txn in json_data["transactions"]]
        updated_transactions = [txn for txn in json_data["transactions"]]
        for dt in data:
            if dt["txn_id"] not in txnIDs:
                updated_transactions.append(dt)
        s3_object.put(
            Body=(bytes(json.dumps({
                "transactions": updated_transactions
            }).encode('UTF-8')))
        )

def push_new_to_S3(data, customer_id):
    # create a new json data object, remove the previous ones and push this to S3
    dt = data["Payload"][0]["data"]
    txns = []
    for i in dt:
        for tx in get_transactions(i["decryptedFI"]["account"]["transactions"]["transaction"]):
            txns.append(tx.get_dict())
    check_if_file_exists_and_update(customer_id, txns)

def get_data_from_FI(consent_id, mobile_number):
    try:
        user_consent = UserConsent.objects.filter(customer_id__icontains = mobile_number)
        if len(user_consent) == 0:
            return False
        else:
            url = "https://fiu-uat.setu.co/sessions/{}".format(consent_id)

            payload={}
            headers = {
                'x-client-id': os.getenv("client_id"),
                'x-client-secret': os.getenv("client_secret"),
            }

            response = requests.request("GET", url, headers=headers, data=payload)
            push_new_to_S3(json.loads(response.content), user_consent[0].customer_id)
            return True
    except Exception as e:
        print(response.content)
        return False

def read_personal_data_from_S3(customer_id):
    s3 = boto3.resource('s3')
    try:
        s3_object = s3.Object('vis-devfolio-bucket', "data/" + customer_id + '.json')
        s3_object.load()
        s3_data = s3_object.get()['Body'].read().decode('utf-8')
        json_data = json.loads(s3_data)
        return True, json_data
    except botocore.exceptions.ClientError as e:
        print(e)
        return False, {}

def get_date_time_from_string(timestamp):
    obj_ls = timestamp.split("T")
    date, time = obj_ls
    date = date.split("-")
    time = time.split(":")
    txn_date_time = datetime.datetime(
        int(date[0]), int(date[1]), int(date[2]), int(time[0]), int(time[1]), int(time[2])
    )
    return txn_date_time

def filter_data_from_cache(start, end, mode, txn_type, cached_data):
    try:
        data = [ob for ob in cached_data]
        if mode is not None:
            data = [i for i in data if i["mode"] == mode]
        if txn_type is not None:
            data = [i for i in data if i["transaction_type"] == txn_type]
        if start is not None:
            start_obj = get_date_time_from_string(start)
            data = [i for i in data if get_date_time_from_string(i["transaction_timestamp"]) >= start_obj]
        if end is not None:
            end_obj = get_date_time_from_string(end)
            data = [i for i in data if get_date_time_from_string(i["transaction_timestamp"]) <= end_obj]
        return True, data
    except Exception as e:
        print(e)    
        return False, {}

def get_dynamodb_data():
    dynamodb = boto3.resource('dynamodb', region_name = 'us-west-2')
    table = dynamodb.Table('vis-fintech')
    response = table.scan()
    data = response['Items']

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])
    return data