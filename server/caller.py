import json
import requests
import os
import sys
# print(os.listdir('.'))
sys.path.append('.')
import pickle
import psycopg2
import pandas as pd
import numpy as np
import time

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-a','-host',help='{host ip (defalut=127.0.0.1)}',dest='host',required=False)
parser.add_argument('-p','-port',help='{port number (defalut=1234)}',dest='port',required=False)

args = parser.parse_args()

host = None
if (args.host == None):
    host = "127.0.0.1"
else:
    host = args.host

port = None
if (args.port == None):
   port = 1234 
else:
    port = args.port

event = {}
#sql_string = "create model mdl(pm25 real, pres real) from pm25.csv method uniform size 1000"
#sql_string = "select model count (pm25 real) from mdl where 1000 <= pres <= 1020"
#sql_string = "select model sum (pm25 real) from mdl where 1000 <= pres <= 1020"
#sql_string = "select model avg (pm25 real) from mdl where 1000 <= pres <= 1020"

#sql_string = "create model instacart_order_product_600k (add_to_cart_order real, reordered real) from instacart_order_product_600k.csv method uniform size 1000"
#sql_string = "select model count (add_to_cart_order real) from instacart_order_product_600k where 0.9 <= reordered <= 1.0"
#sql_string = "select model sum (add_to_cart_order real) from instacart_order_product_600k where 0.9 <= reordered <= 1.0"
sql_string = "select model avg (add_to_cart_order real) from instacart_order_product_600k where 0.9 <= reordered <= 1.0"
#sql_string = "show model "
#sql_string = "drop model instacart_order_product_600k"


if (" model " in sql_string):
#    sql_string.replace(" model "," ")
    event['sql_string'] = sql_string
    start = time.time()
    url = "http://" + host + ":" + str(port)

    res = requests.post(url, json=event).json()
    end = time.time()-start

    print()
    print()
    print("======================================================================")
    print (" TO etriml " + url + " -> " + res['result'])
    print()
    print(" REQUEST(SQL)\t>>> " + sql_string)
    print(" RESPONSE(JSON)\t<<< " + str(res))
    print("----------------------------------------------------------------------")
    if ("select " in sql_string):
        if res['result'] == "success" :
            print("    predict\t: %.4f" % res['value'])
            print("    time cost\t: %.4f seconds" % res['cost'])

        else:
            print("    cause\t: " ,res['cause'])
    elif ("create " in sql_string):
        if res['result'] == "success" :
            print("    time cost\t: %.4f seconds" % res['cost'])
        else:
            print("    cause\t: " ,res['cause'])
    elif ("drop " in sql_string):
        if res['result'] == "success" :
            pass
        else:
            print("    cause\t: " ,res['cause'])
    elif ("show " in sql_string):
        if res['result'] == "success" :
            print("    models\t: ", res['value'])
        else:
            pass
    print("----------------------------------------------------------------------")
    print(" Total elapsed time\t: %.4f seconds" % end)

    print("======================================================================")
    print()
    print()

else :
    print ("TO traindb -> ")
