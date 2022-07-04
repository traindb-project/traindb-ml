from __future__ import print_function



from flask import Flask, request, jsonify
import json
import csv
import pandas as pd
from datetime import datetime, timedelta


import argparse
import os

#from tensorboardX import SummaryWriter
from torchvision import datasets, transforms
import torch
import torch.distributed as dist
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch import tensor


WORLD_SIZE = int(os.environ.get('WORLD_SIZE', 1))


app = Flask(__name__)
global_variable = 111

class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 20, 5, 1)
        self.conv2 = nn.Conv2d(20, 50, 5, 1)
        self.fc1 = nn.Linear(4*4*50, 500)
        self.fc2 = nn.Linear(500, 10)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.max_pool2d(x, 2, 2)
        x = F.relu(self.conv2(x))
        x = F.max_pool2d(x, 2, 2)
        x = x.view(-1, 4*4*50)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return F.log_softmax(x, dim=1)

MODEL = Net()

def load_model(model_name):
    model_export_dir = "/opt/mnist/models/"
    #model_name = "mnist_cnn.pt" #"/opt/mnist/models/"

    # define model : weights are randomly initiated
    global MODEL

    # load the model from the local file
    #MODEL = torch.load(model_export_dir+model_name)
    #MODEL.load_state_dict(model_export_dir+model_name)
    MODEL.load_state_dict(torch.load(model_export_dir+model_name))
    #MODEL.load_state_dict(torch.load(model_export_dir+model_name, map_location='cpu'))

    print("model load ok")


@app.route('/')
def home():
    return "Hello !!!\n"

@app.route('/test/<data>')
def test(data):
    add()
    return "data="+data+" global_variable="+str(global_variable)+"\n"

def add():
    global global_variable
    global_variable = global_variable + 111


@app.route('/predict', methods=['POST'])
def predict_json():
    #print(request.is_json)
    #print(1)
    params = request.get_json()
    #print(2)
    #print(params)
    #print(3)
    #print(params['data'])
    #print(4)
    data = params['data']
    
    #print(5)
    data = eval(data)
    #print(6)
    global MODEL
    output = MODEL(data)
    print("output:", output)


    # get predicted class
    #pred = output.argmax(dim=1, keepdim=True)
    #print(pred.item(), y.item())

    #add()
    #dic = {}
    #dic["predict"] = str(output)
    #dic["data"] = params['data']
    #dic["global_variable"] = str(global_variable)
   
    #json_str = json.dumps(dic, indent=4)
    output_str = str(output).replace("\n", "")
    json_str = jsonify(output_str)
    return json_str



if __name__=='__main__':
    print("START...")
    global_variable = 222
    load_model("mnist_cnn.pt")
    app.run(host="0.0.0.0",port=80)

