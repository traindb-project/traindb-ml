"""
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

from model.types.TrainDBBaseModel import TrainDBModel
import os
import logging
import time
import requests

class RSPN(TrainDBModel):
    """SPN-based model for TrainDB"""

    def __init__(self):
        self.model_name = "rspn"

        # setup logger
        os.makedirs('logs', exist_ok=True)
        # copied from deepdb's maqp.py
        logging.basicConfig(
            # level=args.log_level,
            # [%(threadName)-12.12s]
            format="%(asctime)s [%(levelname)-5.5s]  %(message)s",
            handlers=[
                logging.FileHandler(
                    "logs/{}_{}.log".format(
                    __name__, time.strftime("%Y%m%d-%H%M%S"))),
                logging.StreamHandler()
                ])
        self.logger = logging.getLogger(__name__)
        self.logger.info("initialization")


    def train(self, url, model_name, dataset_path):
        """
        call the REST API: /train
        :param url: default, http://0.0.0.0:8000/train
        :param model_name: name of model(or dataset to be learned)
        :param dataset_path: location of the dataset (e.g., ~/mydataset/orders.csv)
        :returns: path of the generated model(.pkl) if suceess
        """
        self.logger.info(f"learn the {model_name} in {dataset_path}")
        #url = 'http://0.0.0.0:8000/train/'
        #model_name = 'instacart'
        #dataset_path = '~/Projects/datasets/instacart/orders.csv'

        self.model_name = model_name
        self.dataset_path = dataset_path

        payload = {'dataset':model_name, 'csv_path':dataset_path}
        response = requests.post(url, json=payload)
        result = response.json()
        self.logger.info(f"response status:{response.status_code}")
        if (response.status_code == requests.codes.ok):
            self.model_path = result['Created']
            self.logger.info(f"generated an RSPN ensemble in {self.model_path}.")
        
        return self.model_path

    # TODO:  
    def update(self, model_name, new_data):
        """
        call the REST API: /update
        :param url: default, http://0.0.0.0:8000/docs
        :param model_name: name of model(or dataset to be learned)
        :param dataset_path: location of the dataset (e.g., ~/mydataset/orders.csv)
        :returns: path of the generated model(.pkl) if suceess
        """
        self.logger.info(f"update the {model_name} model by {new_data}")

    def estimate(self, url, query, dataset, model_path, show_confidence_intervals):
        """
        call the REST API: /estimate
        :param url: default, http://0.0.0.0:8000/estimate/
        :param query: an SQL statement with aggregations to be approximated
        :param dataset: name of model(or dataset previously learned)
        :param model_path: location of the learned model
        :param show_confidence_intervals: yes or no
        :returns: estimated value with confidence intervals
        """
        self.logger.info("get an approximated aggregation value for {query}")
        #query = 'SELECT COUNT(*) FROM orders'
        #dataset = 'instacart' 
        #model_path = 'model/instances/ensemble_single_instacart_10000000.pkl' 
        #show_confidence_intervals = 'true'
        payload = {'query':query,                      
                   'dataset':dataset,                  
                   'ensemble_location':model_path,     
                   'show_confidence_intervals':show_confidence_intervals}

        response = requests.get(url, params=payload)
        result = response.json()
        self.logger.info(f"response status:{response.status_code}")
        if (response.status_code == requests.codes.ok):
            return result['Estimated Value']
        
        return result

    def train(self, real_data, table_metadata): 
        self.logger.info("learn an RSPN ensemble")

    def save(self, output_path):
        self.logger.info("save the learned model(.pkl or .pth) to the path")

    def load(self, input_path):
        self.logger.info("load the given model")

    def save(self, output_path, file_type):
        self.logger.info("save the output ")


    def transform(self, input_model, output_model):
        self.logger.info("Transform the input .pkl into the output .pth")

