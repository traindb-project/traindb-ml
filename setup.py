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

import argparse
import sys
import os
import shutil
import logging
import numpy as np
import time

from data.schemas.instacart import gen_instacart_schema
from data.preparation.prepare_single_tables import prepare_all_tables
from train.ensemble_creation.naive import create_naive_all_split_ensemble

np.random.seed(1)

if __name__ == '__main__':

    #
    # ARGS - command-line options
    #      - should match the REST API, Knative interface
    #
    parser = argparse.ArgumentParser()

    # ARGS.REST 
    parser.add_argument('--rest_dir', default='interface/dev/', 
                        help='location of the fastapi main file')
    parser.add_argument('--rest_main', default='main', 
                        help='name of the fastapi main file. *.py')
    parser.add_argument('--rest_host', default='0.0.0.0', 
                        help='IP address of the REST API')
    parser.add_argument('--rest_port', default='8000', 
                        help='port of the REST API')

    # ARGS.DATA PREPARATION
    parser.add_argument('--dataset', default='instacart', 
                        help='dataset to be learned')
    parser.add_argument('--csv_path', default='data/files/instacart/csv/orders.csv', 
                        help='csv path for the dataset specified')
    parser.add_argument('--csv_seperator', default=',') # for tpc-ds, use '|'
    parser.add_argument('--hdf_path', default='data/files/instacart/hdf', 
                        help='csv path for the dataset specified')
    parser.add_argument('--max_rows_per_hdf_file', type=int, default=20000000)
    parser.add_argument('--hdf_sample_size', type=int, default=1000000)
    parser.add_argument('--generate_hdf', action='store_true', 
                        help='prepares hdf5 files for single tables')

    # ARGS.LEARN
    # - learn tables to create rspn ensemble, new or update
    parser.add_argument('--train', action='store_true', 
                        help='train rspns on the given dataset')
    parser.add_argument('--ensemble_strategy', default='single')
    parser.add_argument('--ensemble_path', default='model/instances')
    parser.add_argument('--pairwise_rdc_path', default=None)
    parser.add_argument('--samples_rdc_ensemble_tests', 
                        type=int, default=10000)
    parser.add_argument('--samples_per_spn', nargs='+', type=int, 
                        default=[10000000, 10000000, 2000000, 2000000],
                        help="How many samples to use for joins with n tables")
    parser.add_argument('--post_sampling_factor', nargs='+', type=int, 
                        default=[30, 30, 2, 1])
    parser.add_argument('--rdc_threshold', type=float, default=0.3,
                        help='If RDC value is smaller independence is assumed') 
    parser.add_argument('--bloom_filters', action='store_true',
                        help='Generates Bloom filters for grouping') 
    parser.add_argument('--ensemble_budget_factor', type=int, default=5)
    parser.add_argument('--ensemble_max_no_joins', type=int, default=3)
    parser.add_argument('--incremental_learning_rate', type=int, default=0)
    parser.add_argument('--incremental_condition', type=str, default=None)

    # ARGS.INFERENCE
    # - estimate an approximate value for the given aggregation query
    parser.add_argument('--estimate', help='query to be approximated')

    # ARGS.CONFIGURATION
    # - set log level
    parser.add_argument('--log_level', type=int, default=logging.DEBUG)

    # ARGS.END
    args = parser.parse_args()

    #
    # CONF - configurations for traindb-ml
    #
    # CONF.Logging 
    # - copied from deepdb's maqp.py
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

    #
    # TODO: separate this as an REST API
    # DATA_PREP
    #  - SEE: deepdb/maqp.py, schema.py
    #     prepare_all_tables(...), prepare_sample_hdf(...)
    #
    # DATA_PREP.Setup_Directories
    logger.info( "Data Preparation: Setup Directories")
    dataset_path = "data/files/" + args.dataset
    dataset_csv_path = dataset_path + "/csv/"
    dataset_hdf_path = dataset_path + "/hdf/"
    logger.info( " - Setup Directories: " )
    """
              + f" input_csv_path: {args.csv_path}"
              + f" dataset_path: {dataset_path}"
              + f" dataset_csv_path: {dataset_csv_path}"
              + f" dataset_hdf_path: {dataset_hdf_path}")
    """
    logger.info(f" - Making csv path {dataset_csv_path}")
    os.makedirs(dataset_csv_path, exist_ok=True)

    #  - extract the filename from the csv_path and make a target path
    csv_target_filename = os.path.basename(args.csv_path)
    csv_target_path = dataset_csv_path + csv_target_filename

    #  - copy the input csv file into the target path (overwrite if already exists)
    # TODO remove if exist? just like the 'hdf'?
    logger.info(f"  (Overwrite? {os.path.exists(csv_target_path)})")
    if (args.csv_path != csv_target_path) and not os.path.exists(csv_target_path):
        shutil.copy(args.csv_path, csv_target_path) 

    logger.info( "Data Preparation: Create SchemaGraph")
    logger.info(f" - Making SchemaGraphs from {dataset_csv_path}")
    table_csv_path = dataset_csv_path + '{}.csv'
    # XXX: seems like duplicated checking...
    if args.dataset == 'instacart':
        schema = gen_instacart_schema(table_csv_path)
    else:
        raise ValueError('Unknown dataset')

    #  - test
    table = schema.table_dictionary['orders']
    logger.info(f"   orders object: {table}")
    logger.info(f"   orders.table_name: {table.table_name}")
    logger.info(f"   orders.table_size: {table.table_size}")
    logger.info(f"   orders.primary_key: {table.primary_key}")
    logger.info(f"   orders.csv_file_location: {table.csv_file_location}")
    logger.info(f"   orders.attributes: {table.attributes}")
    logger.info(f"   orders.sample_rate: {table.sample_rate}")

    #  - requires: pip install tables
    logger.info( "Data Preparation: Generate HDF")
    logger.info(f" - Generate hdf files for the given csv and save into {dataset_hdf_path}")

    #  - create hdf directory
    if os.path.exists(dataset_hdf_path):
        logger.info(f" - Removing the old {dataset_hdf_path}")
        shutil.rmtree(dataset_hdf_path)
    logger.info(f" - Making new {dataset_hdf_path}")
    os.makedirs(dataset_hdf_path)

    # - prepare all tables
    #   cf. prepare_sample_hdf in join_data_preparation.py
    logger.info(f" - Prepare all tables")
    prepare_all_tables(schema, dataset_hdf_path, args.csv_seperator, max_table_data = args.max_rows_per_hdf_file)
    logger.info(f"Metadata(HDF files) successfully created")
    
    # TRAIN RSPNs - NEW or UPDATE
    logger.info(f"TRAIN RSPNs")
    logger.info(f" - create instance path (if not exists): {args.ensemble_path}")
    if not os.path.exists(args.ensemble_path):
        os.makedirs(args.ensemble_path)

    logger.info(f" - learn RSPNs by 'single' strategy")
    if args.ensemble_strategy == 'single':
        create_naive_all_split_ensemble(schema, args.hdf_path, args.samples_per_spn[0], args.ensemble_path,
                                        args.dataset, args.bloom_filters, args.rdc_threshold,
                                        args.max_rows_per_hdf_file, args.post_sampling_factor[0],
                                        incremental_learning_rate=args.incremental_learning_rate)
    
    logger.info(f"Bookmark")


    # ESTIMATE
    # TODO

    #
    # CONF.RESTAPI
    #
    # launch the fast_api (/interface/dev/main.py)
    # prerequisite: pip install fastapi uvicorn
    # testing: launch browser with "http://0.0.0.0:8000" then see hello message
    #
    #os.system('uvicorn main:app --app-dir interface/dev/ --reload --host=0.0.0.0 --port=8000')
    os.system(f"uvicorn {args.rest_main}:app --app-dir {args.rest_dir} --reload --host={args.rest_host} --port={args.rest_port}")
    sys.exit("Shutting down, bye bye!")

