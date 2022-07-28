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
import logging
import time

class TSPN(TrainDBModel):
    """SPN-based model for TrainDB"""

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
    LOGGER = logging.getLogger(__name__) 

    def __init__(self):
        LOGGER.info("initialization")

    def train(self, real_data, table_metadata): 
        LOGGER.info("train a TSPN model")

    def save(self, output_path):
        LOGGER.info("save the learned model")

    def load(self, input_path):
        LOGGER.info("load the given model")

    # TODO: fix the parameter types
    def estimate(self, query):
        LOGGER.info("get an approximated aggregation value for the query")

