import json
import os
from cmd import Cmd

# import boto3
import pickle
import numpy as np
from flask import Flask, request, json

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-p','-port',help='{port number (defalut=1234}',dest='port',required=False)
parser.add_argument('-t','-target',help='{target model (dw=datawarehouse | mf=mlflow) | default=mf}',dest='target',required=False)

args = parser.parse_args()

port = None
if (args.port == None):
   port = 1234 
else:
    port = args.port
#print("port : ", port)

target = None
if (args.target == None):
    target = "mf" #dw
else:
    target = args.target
#print(target)



from etrimlclient.executor.executor import SqlExecutor

from etrimlclient.parser.parser import (
    ETRIMLParser,
    parse_usecols_check_shared_attributes_exist,
    parse_y_check_need_ft_only,
)


sqlExecutor = SqlExecutor()

app = Flask(__name__)

@app.route('/', methods=['POST'])
def index():
    # Parse request body for model input
    event = request.get_json(silent=True)
    #print(event)
    sql_string = None
    if ("create " in event['sql_string']):
        sql_string = event['sql_string'].replace(" model "," table ")
    else:
        sql_string = event['sql_string'].replace(" model "," ")

    print()
    print()
    print("======================================================================")
    print("REQUEST(SQL)     >>> " + sql_string)
    print("----------------------------------------------------------------------")

    #sqlExecutor = SqlExecutor()

    # prepare the parser
    parser = None
    if type(sql_string) == str:
        parser = ETRIMLParser()
        parser.parse(sql_string)
    elif type(sql_string) == ETRIMLParser:
        parser = sql_string
    else:
        print("Unrecognized SQL! Please check it!")
        exit(-1)

    sql_type = parser.get_query_type()
    #print("sql_type = ", sql_type)

    json_val = None
    if sql_type == "create":
        if (target == "mf") :
            ok, cause, val, time_cost = sqlExecutor.execute_mlflow(sql_string)
        else :
            ok, cause, val, time_cost = sqlExecutor.execute(sql_string)

        if (ok == "success") :
            result = {}
            result['result'] = ok
            result['cause'] = "success"
            result['cost'] = time_cost
            json_val = json.dumps(result)

        else :
            result = {}
            result['result'] = ok
            result['cause'] = cause
            result['cost'] = 0
            json_val = json.dumps(result)

    elif sql_type == "select":
        if (target == "mf") :
            ok, cause, val, time_cost = sqlExecutor.execute_mlflow(sql_string)
        else :
            ok, cause, val, time_cost = sqlExecutor.execute(sql_string)

        if (ok == "success") :
            result = {}
            result['result'] = ok
            result['cause'] = cause
            result['value'] = val.iloc[0][1]
            result['cost'] = time_cost
            json_val = json.dumps(result)

        else :
            result = {}
            result['result'] = ok
            result['cause'] = cause
            json_val = json.dumps(result)

    elif sql_type == "drop":
        if (target == "mf") :
            ok, cause, val, time_cost = sqlExecutor.execute_mlflow(sql_string)
        else :
            ok, cause, val, time_cost = sqlExecutor.execute(sql_string)

        result = {}
        result['result'] = ok
        result['cause'] = cause
        json_val = json.dumps(result)

    elif sql_type == "show":
        if (target == "mf") :
            ok, cause, val, time_cost = sqlExecutor.execute_mlflow(sql_string)
        else :
            ok, cause, val, time_cost = sqlExecutor.execute(sql_string)

        result = {}
        result['result'] = ok
        result['cause'] = cause
        result['value'] = val
        json_val = json.dumps(result)

    else:
        pass

     #print(json_val)

    print("RESPONSE(SQL)     >>> " + str(json_val))
    print("======================================================================")
    print()
    print()


    return json_val


if __name__ == '__main__':
    if target == "mf":
        print("Running on http://0.0.0.0:" + str(port) + " -> mlflow")
    else:
        print("Running on http://0.0.0.0:" + str(port) + " -> datawarehouse")

    # listen on all IPs
    app.run(host='0.0.0.0', port=port)

