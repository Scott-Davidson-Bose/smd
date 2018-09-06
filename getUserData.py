#!/usr/bin/python

import datetime
import getpass
import json
import os
import requests
import sys

original_stdout = sys.stdout
sys.stdout = sys.stderr

basename = os.path.splitext(os.path.basename(sys.argv[0]))[0]

print(basename + " Version 0.0.3")
print("This script allows you to dump out the data in the cloud for your user account.")
print("Please enter the credentials that you use to login to Madrid.\n")

email = raw_input("Email: ")
password = getpass.getpass()

print("\nWorking...\n")
sys.stdout = original_stdout

class EntryPoints:
    commonPrefix = "https://ingress-platform.live-aws-useast1.bose.io/dev/"
    idUserAccountsCore  = commonPrefix + "svc-id-gen-pub/<env>/id-user-accounts-core/"
    idAccountAttrsCore  = commonPrefix + "svc-id-gen-priv/<env>/id-account-attrs-core/"
    idProductPropsCore  = commonPrefix + "svc-id-gen-priv/<env>/id-product-props-core/"
    svcPassportUserInfo = commonPrefix + "svc-passport-user-info/<env>/service/"
    svcPassportCore     = commonPrefix + "svc-passport-core/<env>/passport-core/"

class Urls:
    getAccessToken                = EntryPoints.idUserAccountsCore  + "userAccounts/authenticate"
    getUserAccountInfo_users_id   = EntryPoints.idAccountAttrsCore  + "users/search?bosePersonID=%s"
    getPassportUserInfo_users_id  = EntryPoints.svcPassportUserInfo + "users/%s"
    getPassport_users_id          = EntryPoints.svcPassportCore     + "users/%s"
    getPassport_users_id_products = EntryPoints.svcPassportCore     + "users/%s/products"
    getProductProps_products_id   = EntryPoints.idProductPropsCore  + "products/%s"

def dict_value(dict, key):
    return dict[key] if key in dict else None

def now():
    return datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')

def print_with_rule(s):
    print("// " + s + " " + ("/" * max(0, 128 - len(s))))

def request(msg, env, method, url, data = {}, headers = {}, show_response = True):
    headers["Content-Type"] = "application/json; charset=utf-8"
    url = url.replace("<env>", env)
    response = requests.request(method, url, json=data, headers=headers)
    return {
        "msg":msg,
        "env":env,
        "method":method,
        "url":url,
        "data":data,
        "headers":headers,
        "show_response":show_response,
        "status":response.status_code,
        "result":response.json() if str(response.status_code).startswith("2") else None
    }

# Step 1: Gather all of the data
credentials = { "email":email, "password":password }
data = {}
envs = ["prod", "integration"]
authenticated_envs = []
for env in envs:
    data[env] = {}
    data[env]["task_list"] = []
    data[env]["task_map"] = {}

    msg = "Authentication against User Accounts service"
    task = request(msg, env, "POST", Urls.getAccessToken, credentials, {}, False)
    data[env]["task_list"].append(task)
    data[env]["task_map"]["authenticate"] = task

    if task["status"] != 403:
        authenticated_envs.append(env)

        tokens = task["result"]
        access_token = tokens["access_token"]
        bose_person_id = tokens["bosePersonID"]
        data[env]["bosePersonID"] = bose_person_id

        headers = { "X-Apikey":"9zf6kcZgF5IEsXbrKU6fvG8vFGWzF1Ih", "X-User-Token":access_token }

        msg = "Query of User Accounts for Info"    
        task = request(msg, env, "GET", Urls.getUserAccountInfo_users_id % bose_person_id, {}, headers)
        data[env]["task_list"].append(task)
        data[env]["task_map"]["get_info"] = task

        msg = "Query of Passport for User Info"    
        task = request(msg, env, "GET", Urls.getPassportUserInfo_users_id % bose_person_id, {}, headers)
        data[env]["task_list"].append(task)
        data[env]["task_map"]["get_user"] = task

        msg = "Query of Passport for User Products"
        task = request(msg, env, "GET", Urls.getPassport_users_id_products % bose_person_id, {}, headers)
        data[env]["task_list"].append(task)
        data[env]["task_map"]["get_products"] = task
        # remove pagination envelope
        products = task["result"] = dict_value(task["result"], "results")

        for product in products:
            msg = "Query of Product Properties service"
            task = request(msg, env, "GET", Urls.getProductProps_products_id % product["productID"])
            data[env]["task_list"].append(task)
            data[env]["task_map"]["get_product_properties_for_%s" % product["productID"]] = task

# Step 2: Examine the data and render summary info
print_with_rule("Result of %s for Madrid/Gigya user '%s' at local system time '%s':" % (basename, email, now()))
print("")

if len(authenticated_envs) > 1:
    prod_user_info = data["prod"]["task_map"]["get_user"]["result"]
    int_user_info = data["integration"]["task_map"]["get_user"]["result"]

    user_env_per_prod = dict_value(prod_user_info, "galapagos_environment")
    user_env_per_int = dict_value(int_user_info, "galapagos_environment")
    if user_env_per_prod == user_env_per_int:
        print("// This user is currently in the '%s' environment.\n" % user_env_per_prod)
    else:
        print("// Anomaly: This user is currently in '%s' per prod and '%s' per integration.\n" % (user_env_per_prod, user_env_per_int))

    gigya_id_per_prod = dict_value(prod_user_info, "gigyaID")
    gigya_id_per_int = dict_value(int_user_info, "gigyaID")
    if gigya_id_per_prod == gigya_id_per_int:
        print("// This user's Gigya ID is '%s'.\n" % gigya_id_per_prod)
    else:
        print("// Anomaly: This user's Gigya ID is '%s' per prod and '%s' per integration.\n" % (gigya_id_per_prod, gigya_id_per_int))

elif len(authenticated_envs) > 0:
    user_info = data[authenticated_envs[0]]["task_map"]["get_user"]["result"]
    print("// This user is currently in the '%s' environment.\n" % dict_value(user_info, "galapagos_environment"))
    print("// This user's Gigya ID is '%s'.\n" % dict_value(user_info, "gigyaID"))

for env in authenticated_envs:
    creator = dict_value(data[env]["task_map"]["get_info"]["result"]["data"], "createdByServiceID")
    demo = "DEMO" if creator == "retail-demo-core" else "(non-demo)"
    print("// In %s, this %s user's bosePersonID is %s\n" % (env, demo, data[env]["task_map"]["authenticate"]["result"]["bosePersonID"]))

# Step 3: Render the data
for env in envs:
    print_with_rule("EXAMINION OF ENVIRONMENT: %s" % env)
    if env not in authenticated_envs:
        print("\nERROR: Per the User Accounts service in %s, the given credentials are invalid.\n" % env)
    else:
        print("")
        for task in data[env]["task_list"]:
            print_with_rule(task["msg"] + " in " + task["env"])
            print("//")
            print("// Request: %s %s" % (task["method"], task["url"]))
            print("// Response: %s" % task["status"])
            if task["show_response"]:
                print(json.dumps(task["result"], indent = 2))
            print("")

sys.stdout = sys.stderr
print("Done.")
sys.stdout = original_stdout
