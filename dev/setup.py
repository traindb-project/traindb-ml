import argparse
import os
import logging
import numpy as np
import time

np.random.seed(1)

if __name__ == '__main__':

    #
    # COMMAND-LINE OPTIONS
    # should match the REST API, Knative interface
    # TODO: data preparation interfaces, csv or dbconnection to schema object
    #
    parser = argparse.ArgumentParser()

    # dataset to be used
    parser.add_argument(
        '--dataset', default='instacart', 
        help='dataset to be learned')
    # learn tables to create rspn ensemble, new or update
    parser.add_argument(
        '--train', action='store_true', 
        help='train rspns on the given dataset')
    # estimate an approximate value for the given aggregation query
    parser.add_argument('--estimate', help='query to be approximated')
    # set log level
    parser.add_argument('--log_level', type=int, default=logging.DEBUG)

    # parse arguments
    args = parser.parse_args()

    # check
    print(f"--dataset: {args.dataset}")

    #
    # LOGGING 
    # copied from deepdb's maqp.py
    #
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        level=args.log_level,
        # [%(threadName)-12.12s]
        format="%(asctime)s [%(levelname)-5.5s]  %(message)s",
        handlers=[
            logging.FileHandler(
                "logs/{}_{}.log".format(
                    args.dataset, time.strftime("%Y%m%d-%H%M%S"))),
            logging.StreamHandler()
        ])
    logger = logging.getLogger(__name__)

    # check
    print("logger")
    logger.info(f"Start")

    #
    # DATA PREPARATION
    # TODO: do something similar to the schema & HDF generation in deepdb
    # SEE: 
    #     gen_xxx_schema(csv_path), 
    #     prepare_all_tables(...), prepare_sample_hdf(...)
    #

    
    # TRAIN RSPNs - NEW or UPDATE


    # ESTIMATE


# 2022.07.26 19:38
