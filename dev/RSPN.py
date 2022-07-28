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

from TrainDBBaseModel import TrainDBModel
import os
import logging
import time

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


    def train(self, real_data, table_metadata): 
        self.logger.info("learn an RSPN ensemble")

    def save(self, output_path):
        self.logger.info("save the learned model(.pkl or .pth) to the path")

    def load(self, input_path):
        self.logger.info("load the given model")

    # TODO: define the parameter types, 
    # cf. REST API: /train/{model_name}/{dataset}/{metadata}
    def train(self, model_name, dataset, dataset_metadata):
        self.logger.info("learn an RSPN ensemble and give the name to it")
        self.model_name = model_name
        train(self, dataset, dataset_metadata)

    # TODO: .pkl or .pth
    def save(self, output_path, file_type):
        if (file_type == "pkl"):
            self.logger.info("save the output as .pkl")
        else:
            self.logger.info("save the output as .pth")


    # TODO: define the parameter types, 
    # cf. REST API: /train/{model_name}/{dataset}/{metadata}
    def update(self, model_name, new_data):
        self.logger.info(f"update the {model_name} model by {new_data}")

    # TODO: define the parameter types, 
    #       see if it's compatible with the way TrainDB process AQPs
    # cf. REST API: /estimate/{query_parameters:agg_type, from, filter}
    def estimate(self, query_parameters):
        self.logger.info("get an approximated aggregation value for the query")

    def transform(self, input_model, output_model):
        self.logger.info("Transform the input .pkl into the output .pth")

