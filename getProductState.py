#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
:Abstract: Get product state with user jwt
:Organization:  BOSE CORPORATION
:Author:  Manasi Bhandare
:Date:  April 12, 2018
:Copyright: COPYRIGHT 2017 BOSE CORPORATION ALL RIGHTS RESERVED.
             This program may not be reproduced, in whole or in part in any
             form or any means whatsoever without the written permission of:
                 BOSE CORPORATION
                 The Mountain,
                 Framingham, MA 01701-9168
"""

import sys
import logging
import time
import argparse
import json



try:
	import requests
except ImportError:
	sys.exit("""You need requests!
							Please run 'pip install requests'""")

PRODUCT_STATE = "https://ingress-platform.live-aws-useast1.bose.io/dev/svc-iot-product-state/%s/iot-product-state-core"

USER_JWT = "https://ingress-platform.live-aws-useast1.bose.io/dev/svc-id-gen-pub/%s/id-user-accounts-core/userAccounts/authenticate"

def get_user_jwt(email, password, environment):
	headers={}
	headers['Content-Type'] = 'application/json'
	user_data = {}
	user_data["email"] = email
	user_data["password"] = password


	jwt_environment = 'latest'
	if environment not in ['latest', 'integration']:
		jwt_environment = 'prod' 

	print( "JWT URL: " + USER_JWT % jwt_environment)
	response = requests.post(USER_JWT % jwt_environment, data=json.dumps(user_data), headers=headers)
	if not response.ok:
		print( "ERROR: failed to get user JWT with http code {} and message {}".format(response.status_code, response.reason))
		return None
	response_data = response.json()

	try:
		return response_data["access_token"]
	except:
		print("Unexpected error:", sys.exc_info()[0])
		return None
    

def get_product_state(product_id, email, environment, password):
	
	url = PRODUCT_STATE % environment+"/search?productID=" + product_id
	print( "ENVIRONMENT: " + environment)
	print( "URL: " + url)
	print( "PRODUCTID " + product_id)
	print( "EMAIL " + email)

	headers={}
	headers['Content-Type'] = 'application/json'
	user_jwt = get_user_jwt(email, password, environment)
	if user_jwt != None :
		headers['X-User-Token'] = user_jwt

	response = requests.get(url, headers=headers)
	if response.status_code != requests.codes.ok:
		print( "ERROR: failed to get product state with http code {} and message {}".format(response.status_code, response.reason))
		return
	
	print( response.json())


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--pid", help="Product ID to get state of", required=True)
  parser.add_argument("--email", help="EmailID", required=True)
  parser.add_argument("--env", help="Environment to bind to", required=True)
  parser.add_argument("--p", help="Password", required=True)
	#parser.add_argument("--h", help="params are pid, email, p, env", required=False)

  args = parser.parse_args()

  product_id = None
  email = None
  environment = None
  password = None

  if (args.pid):
    product_id = args.pid

  if (args.email):
    email = args.email

  if (args.env):
    environment = args.env

  if (args.p):
    password = args.p

  if product_id and email and environment and password:
    get_product_state(product_id, email, environment.lower(), password)
    print( "Exited")
  else:
  	print( "Please read help. Use -h")
main()