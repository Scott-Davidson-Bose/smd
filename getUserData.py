#!/usr/bin/python

import datetime
import json
import os
import requests
import sys

basename = os.path.splitext(os.path.basename(sys.argv[0]))[0]

print(basename + " Version 0.0.1")
print("This script allows you to dump out the data in the cloud for your user account.")
print("Please enter the credentials that you use to login to Madrid.\n")

email = raw_input("Email: ")
password = raw_input("Password: ")
credentials = { "email":email, "password":password }

print("\nWorking...\n")
output_file = basename + ".txt"
original_stdout = sys.stdout
sys.stdout = open(output_file, "w")

class EntryPoints:
    commonPrefix = "https://ingress-platform.live-aws-useast1.bose.io/dev/"
    idUserAccountsCore  = commonPrefix + "svc-id-gen-pub/<env>/id-user-accounts-core/userAccounts/authenticate"
    idProductPropsCore  = commonPrefix + "svc-id-gen-priv/<env>/id-product-props-core/"
    svcPassportUserInfo = commonPrefix + "svc-passport-user-info/<env>/service/"
    svcPassportCore     = commonPrefix + "svc-passport-core/<env>/passport-core/"

class Urls:
    getAccessToken                = EntryPoints.idUserAccountsCore
    getPassportUserInfo_users_id  = EntryPoints.svcPassportUserInfo + "users/%s"
    getPassport_users_id          = EntryPoints.svcPassportCore     + "users/%s"
    getPassport_users_id_products = EntryPoints.svcPassportCore     + "users/%s/products"
    getProductProps_products_id   = EntryPoints.idProductPropsCore  + "products/%s"

def now():
    return datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')

def printWithRule(s):
    print("// " + s + " " + ("/" * max(0, 128 - len(s))))
    
def request(msg, env, method, url, data = {}, headers = {}, showResponse = True):
    headers["Content-Type"] = "application/json; charset=utf-8"
    url = url.replace("<env>", env)
    printWithRule(msg + " in " + env)
    print("//")
    print("// Request: %s %s" % (method, url))

    response = requests.request(method, url, json=data, headers=headers)

    result = response.json() if str(response.status_code).startswith("2") else None

    print("// Response: %s" % response.status_code)
    if showResponse:
        print(json.dumps(result, indent = 2))
    print("")
    return response.status_code, result

printWithRule("Result of %s for Madrid/Gigya user '%s' at local system time '%s':" % (basename, email, now()))

data = {}
print ""
for env in ["prod", "integration"]:
    data[env] = {}
    printWithRule("EXAMINING ENVIRONMENT: %s" % env)
    print("")    

    status, tokens = request("Authenticating against User Accounts service",
                             env, "POST", Urls.getAccessToken, credentials, {}, False)

    if status == 403:
        print("ERROR: Per the User Accounts service in %s, the given credentials are invalid.\n" % env)
    else:
        access_token = tokens["access_token"]
        bose_person_id = tokens["bosePersonID"]
        headers = { "X-Apikey":"9zf6kcZgF5IEsXbrKU6fvG8vFGWzF1Ih", "X-User-Token":access_token }
    
        status, data[env]["user"] = request("Querying Passport for User Info",
                                            env, "GET", Urls.getPassportUserInfo_users_id % bose_person_id, {}, headers)
    
        status, products_results = request("Querying Passport for User Products",
                                           env, "GET", Urls.getPassport_users_id_products % bose_person_id, {}, headers)
        data[env]["products"] = products_results["results"]
    
        for product in data[env]["products"]:
            status, product["productProperties"] = request("Querying Product Properties service",
                                                           env, "GET", Urls.getProductProps_products_id % product["productID"])
sys.stdout = original_stdout
os.system("cat "+ output_file)
print("Done. Output is available in " + output_file)
