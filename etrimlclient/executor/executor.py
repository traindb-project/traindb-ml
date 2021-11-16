import os
import os.path
import warnings
from datetime import datetime
from multiprocessing import set_start_method as set_start_method_cpu
import csv
import shutil

import dill
import numpy as np
import pandas as pd
import torch
from torch.multiprocessing import set_start_method as set_start_method_torch

from etrimlclient.catalog.catalog import ETRIMLModelCatalog
from etrimlclient.executor.queryenginemdn import (
    MdnQueryEngine,
    MdnQueryEngineGoGs,
    MdnQueryEngineNoRange,
    MdnQueryEngineNoRangeCategorical,
    MdnQueryEngineNoRangeCategoricalOneModel,
    MdnQueryEngineRangeNoCategorical,
    MdnQueryEngineXCategorical,
    MdnQueryEngineXCategoricalOneModel,
    QueryEngineFrequencyTable,
)
from etrimlclient.io.sampling import ETRIMLSampling
from etrimlclient.ml.modeltrainer import GroupByModelTrainer, KdeModelTrainer
from etrimlclient.parser.parser import (
    ETRIMLParser,
    parse_usecols_check_shared_attributes_exist,
    parse_y_check_need_ft_only,
)
from etrimlclient.tools.dftools import (
    get_group_count_from_df,
    get_group_count_from_summary_file,
    get_group_count_from_table,
)
from etrimlclient.tools.running_parameters import RUNTIME_CONF, EtrimlConfig
from etrimlclient.tools.variables import Slave, UseCols

import mlflow
import mlflow.pyfunc
import numpy as np
from mlflow.pyfunc import PythonModel
from sklearn.base import clone
import cloudpickle
from sys import version_info
import requests
import json

PYTHON_VERSION = "{major}.{minor}.{micro}".format(major=version_info.major,
                                                  minor=version_info.minor,
                                                  micro=version_info.micro)

class SqlExecutor:
    """
    This is the executor for the SQL query.
    """

    def __init__(self):
        #print(">>> executor > executor.py > SqlExecutor : __init__()")

        self.parser = None
        self.config = EtrimlConfig()  # model-related configuration
        self.runtime_config = RUNTIME_CONF
        self.last_config = None
        self.model_catalog = ETRIMLModelCatalog()
        self.init_slaves()
        self.init_model_catalog()
        self.save_sample = False
        self.n_total_records = None
        self.use_kde = True

    def init_model_catalog(self):
        #print(">>> executor > executor.py > SqlExecutor : init_model_catalog()")

        # search the warehouse, and add all available models.
        n_model = 0
        t1 = datetime.now()
        for file_name in os.listdir(self.config.get_config()["warehousedir"]):
            # load simple models
            if file_name.endswith(self.runtime_config["model_suffix"]):
                if n_model == 0:
                    print("start loading pre-existing models.")

                with open(
                    self.config.get_config()["warehousedir"] + "/" + file_name, "rb"
                ) as f:
                    model = dill.load(f)
                self.model_catalog.model_catalog[
                    file_name
                    # model.init_pickle_file_name(self.runtime_config)
                ] = model
                n_model += 1

        if n_model > 0:
            print("Loaded " + str(n_model) + " models.", end=" ")
            if self.runtime_config["b_show_latency"]:
                t2 = datetime.now()
                print("time cost ", (t2 - t1).total_seconds(), "s")
            else:
                print()

    def init_slaves(self):
        #print(">>> executor > executor.py > SqlExecutor : init_slaves()")
        file_name = os.path.join(self.config.config["warehousedir"], "slaves")
        if os.path.exists(file_name) and os.path.getsize(file_name) > 0:
            with open(file_name, "r") as f:
                for line in f:
                    if "#" not in line:
                        self.runtime_config["slaves"].add(Slave(line))
            if self.runtime_config["v"]:
                print(
                    "Cluster mode is on, slaves are "
                    + self.runtime_config["slaves"].to_string()
                )
        else:
            if self.runtime_config["v"]:
                print("Local mode is on, as no slaves are provided.")

    def execute(self, sql):
        #print(">>> executor > executor.py > SqlExecutor : execute()")

        # prepare the parser
        if type(sql) == str:
            self.parser = ETRIMLParser()
            self.parser.parse(sql)
        elif type(sql) == ETRIMLParser:
            self.parser = sql
        else:
            print("Unrecognized SQL! Please check it!")
            return "fail", "Unrecognized SQL! Please check it!", None, None
            #exit(-1)

        # execute the query
        if self.parser.if_nested_query():
            warnings.warn("Nested query is currently not supported!")
            return "fail", "Nested query is currently not supported!", None, None
        else:
            sql_type = self.parser.get_query_type()
            if sql_type == "create":  # process create query
                # initialize the configure for each model creation.
                if self.last_config:
                    self.config = self.last_config
                else:
                    self.config = EtrimlConfig()
                # DDL, create the model as requested
                mdl = self.parser.get_ddl_model_name()
                tbl = self.parser.get_from_name()

                # remove unnecessary charactor '
                tbl = tbl.replace("'", "")
                if os.path.isfile(tbl):  # the absolute path is provided
                    original_data_file = tbl
                else:  # the file is in the warehouse direcotry                    
                    original_data_file = (
                        self.config.get_config()["warehousedir"] + "/" + tbl
                    )
                
                if os.path.isfile(original_data_file):  
                    print()
                else:      
                    return "fail", "No such file(" + tbl + ").", None, None

                    
                yheader = self.parser.get_y()
                xheader_continous, xheader_categorical = self.parser.get_x()

                ratio = self.parser.get_sampling_ratio()
                method = self.parser.get_sampling_method()
                table_header = self.config.get_config()["table_header"]

                if table_header is not None:
                    table_header = table_header.split(
                        self.config.get_config()["csv_split_char"]
                    )
                if xheader_continous:  # there is no continuous attribute
                    if self.parser.if_model_need_filter():
                        self.config.set_parameter("accept_filter", True)

                # make samples
                if not self.parser.if_contain_groupby():  # if group by is not involved
                    sampler = ETRIMLSampling(
                        headers=table_header,
                        usecols={
                            "y": yheader,
                            "x_continous": xheader_continous,
                            "x_categorical": xheader_categorical,
                            "gb": None,
                        },
                        n_jobs=self.runtime_config["n_jobs"],
                        mdl_name=mdl,
                        warehouse=self.config.get_config()["warehousedir"]
                    )
                else:
                    groupby_attribute = self.parser.get_groupby_value()

                    # print("yheader", yheader)
                    # print("xheader_continous", xheader_continous)
                    # print("xheader_categorical", xheader_categorical)
                    # print("groupby_attribute", xheader_categorical)

                    sampler = ETRIMLSampling(
                        headers=table_header,
                        usecols={
                            "y": yheader,
                            "x_continous": xheader_continous,
                            "x_categorical": xheader_categorical,
                            "gb": groupby_attribute,
                        },
                        n_jobs=self.runtime_config["n_jobs"],
                        mdl_name=mdl,
                        warehouse=self.config.get_config()["warehousedir"]
                    )

                if os.path.exists(
                    os.path.join(
                        self.config.get_config()["warehousedir"],
                        mdl + self.runtime_config["model_suffix"],
                    )
                ):
                    print(
                        "Model {0} exists in the warehouse, please use"
                        " another model name to train it.".format(mdl)
                    )
                    return "fail", "Model {0} exists in the warehouse, please use another model name to train it.".format(mdl), None, None

                print("Start creating model " + mdl)
                time1 = datetime.now()

                # if method.lower() == "uniform":
                if self.save_sample:
                    sampler.make_sample(
                        original_data_file,
                        ratio,
                        method,
                        split_char=self.config.get_config()["csv_split_char"],
                        file2save=self.config.get_config()["warehousedir"]
                        + "/"
                        + mdl
                        + ".csv",
                        num_total_records=self.n_total_records,
                    )
                else:
                    sampler.make_sample(
                        original_data_file,
                        ratio,
                        method,
                        split_char=self.config.get_config()["csv_split_char"],
                        num_total_records=self.n_total_records,
                    )
                
                if self.runtime_config["sampling_only"]:
                    print("sample is generated and saved, end.")
                    return

                if not self.parser.if_contain_groupby():  # if group by is not involved
                    sampler.sample.sampledf["dummy_gb"] = "dummy"
                    sampler.sample.usecols = {
                        "y": yheader,
                        "x_continous": xheader_continous,
                        "x_categorical": xheader_categorical,
                        "gb": "dummy_gb",
                    }
                    n_total_point, xys = sampler.get_groupby_frequency_data()
                    # if not n_total_point['if_contain_x_categorical']:
                    n_total_point.pop("if_contain_x_categorical")
                    kdeModelWrapper = KdeModelTrainer(
                        mdl,
                        tbl,
                        xheader_continous[0],
                        yheader,
                        groupby_attribute=["dummy_gb"],
                        groupby_values=list(n_total_point.keys()),
                        n_total_point=n_total_point,
                        x_min_value=-np.inf,
                        x_max_value=np.inf,
                        config=self.config.copy(),
                    ).fit_from_df(
                        xys["data"], self.runtime_config, network_size="large"
                    )

                    qe_mdn = MdnQueryEngine(kdeModelWrapper, config=self.config.copy())

                    qe_mdn.serialize2warehouse(
                        self.config.get_config()["warehousedir"], self.runtime_config
                    )
                    self.model_catalog.add_model_wrapper(qe_mdn, self.runtime_config)

                else:  # if group by is involved in the query
                    if self.config.get_config()["reg_type"] == "qreg":
                        xys = sampler.getyx(yheader, xheader_continous)
                        n_total_point = get_group_count_from_table(
                            original_data_file,
                            groupby_attribute,
                            sep=self.config.get_config()["csv_split_char"],
                            headers=table_header,
                        )

                        n_sample_point = get_group_count_from_df(xys, groupby_attribute)
                        groupby_model_wrapper = GroupByModelTrainer(
                            mdl,
                            tbl,
                            xheader_continous,
                            yheader,
                            groupby_attribute,
                            n_total_point,
                            n_sample_point,
                            x_min_value=-np.inf,
                            x_max_value=np.inf,
                            config=self.config.copy(),
                        ).fit_from_df(xys, self.runtime_config)
                        groupby_model_wrapper.serialize2warehouse(
                            self.config.get_config()["warehousedir"]
                            + "/"
                            + groupby_model_wrapper.dir
                        )
                        self.model_catalog.model_catalog[
                            groupby_model_wrapper.dir
                        ] = groupby_model_wrapper.models
                    else:  # "mdn"
                        if method.lower() == "uniform":
                            xys = sampler.getyx(
                                yheader, xheader_continous, groupby=groupby_attribute
                            )

                            if isinstance(ratio, str):
                                frequency_file = (
                                    self.config.get_config()["warehousedir"]
                                    + "/"
                                    + ratio
                                )
                                if os.path.exists(frequency_file):
                                    n_total_point = get_group_count_from_summary_file(
                                        frequency_file, sep=","
                                    )
                                    (
                                        n_total_point_sample,
                                        xys,
                                    ) = sampler.get_groupby_frequency_data()
                                    n_total_point[
                                        "if_contain_x_categorical"
                                    ] = n_total_point_sample["if_contain_x_categorical"]
                                else:
                                    raise FileNotFoundError(
                                        "scaling factor should come from the "
                                        + ratio
                                        + " in the warehouse folder, as"
                                        " stated in the SQL. However, the file is not found."
                                    )
                            else:
                                (
                                    n_total_point,
                                    xys,
                                ) = sampler.get_groupby_frequency_data()

                                # for cases when the data file is treated as a sample, we need to scale up the frequency for each group.
                                if ratio > 1:
                                    file_size = sampler.n_total_point
                                    ratio = float(ratio) / file_size
                                # if 0 < ratio < 1:
                                scaled_n_total_point = {}
                                if "if_contain_x_categorical" in n_total_point:
                                    scaled_n_total_point[
                                        "if_contain_x_categorical"
                                    ] = n_total_point.pop("if_contain_x_categorical")
                                if "categorical_distinct_values" in n_total_point:
                                    scaled_n_total_point[
                                        "categorical_distinct_values"
                                    ] = n_total_point.pop("categorical_distinct_values")
                                if "x_categorical_columns" in n_total_point:
                                    scaled_n_total_point[
                                        "x_categorical_columns"
                                    ] = n_total_point.pop("x_categorical_columns")
                                for key in n_total_point:
                                    # print("key", key, n_total_point[key])

                                    if not isinstance(n_total_point[key], dict):
                                        scaled_n_total_point[key] = (
                                            n_total_point[key] / ratio
                                        )
                                    else:
                                        scaled_n_total_point[key] = {}
                                        for sub_key in n_total_point[key]:
                                            scaled_n_total_point[key][sub_key] = (
                                                n_total_point[key][sub_key] / ratio
                                            )
                                n_total_point = scaled_n_total_point
                                # print("scaled_n_total_point", scaled_n_total_point)
                        elif method.lower() == "stratified":
                            pass
                        else:
                            raise TypeError("unexpected method")

                        # no continuous x attributes, which means there is not range predicate on continuous attribute
                        if not xheader_continous:
                            # use one model to support all categorical attribute
                            if self.config.config["one_model"]:
                                qe = MdnQueryEngineNoRangeCategoricalOneModel(
                                    self.config.copy()
                                )
                                usecols = {
                                    "y": yheader,
                                    "x_continous": xheader_continous,
                                    "x_categorical": xheader_categorical,
                                    "gb": groupby_attribute,
                                }
                                if method.lower() == "uniform":
                                    useCols = UseCols(usecols)

                                    # get the training data from samples.
                                    (
                                        gbs,
                                        xs,
                                        ys,
                                    ) = useCols.get_gb_x_y_cols_for_one_model()
                                    (
                                        gbs_data,
                                        xs_data,
                                        ys_data,
                                    ) = sampler.sample.get_columns_from_original_sample(
                                        gbs, xs, ys
                                    )
                                    n_total_point = sampler.sample.get_frequency_of_categorical_columns_for_gbs(
                                        groupby_attribute, xheader_categorical
                                    )

                                    scaled_n_total_point = {}
                                    for key in n_total_point:
                                        scaled_n_total_point[key] = {}
                                        for sub_key in n_total_point[key]:
                                            scaled_n_total_point[key][sub_key] = (
                                                n_total_point[key][sub_key] / ratio
                                            )
                                    n_total_point = scaled_n_total_point

                                    qe.fit(
                                        mdl,
                                        tbl,
                                        gbs_data,
                                        xs_data,
                                        ys_data,
                                        n_total_point,
                                        usecols=usecols,
                                        runtime_config=self.runtime_config,
                                    )

                                elif method.lower() == "stratified":
                                    # check if this query could be served by frequency table only.

                                    b_ft_only = parse_y_check_need_ft_only(usecols)
                                    # print("b_ft_only", b_ft_only)
                                    if b_ft_only:
                                        # print("to implement")
                                        n_total_point = sampler.sample.get_ft()
                                        # print("ft", n_total_point)
                                        qe = QueryEngineFrequencyTable(
                                            self.config.copy()
                                        )
                                        qe.fit(
                                            mdl,
                                            tbl,
                                            None,
                                            None,
                                            None,
                                            n_total_point,
                                            usecols=usecols,
                                            runtime_config=self.runtime_config,
                                        )
                                        # exit()

                                    else:
                                        (
                                            gbs_data,
                                            xs_data,
                                            ys_data,
                                        ) = (
                                            sampler.sample.get_categorical_features_label()
                                        )
                                        n_total_point = sampler.sample.get_ft()

                                        qe.fit(
                                            mdl,
                                            tbl,
                                            gbs_data,
                                            xs_data,
                                            ys_data,
                                            n_total_point,
                                            usecols=usecols,
                                            runtime_config=self.runtime_config,
                                        )
                                qe.serialize2warehouse(
                                    self.config.get_config()["warehousedir"],
                                    self.runtime_config,
                                )
                                self.model_catalog.add_model_wrapper(
                                    qe, self.runtime_config
                                )
                            else:  # train seperate models for each categorical attribute
                                usecols = {
                                    "y": yheader,
                                    "x_continous": xheader_continous,
                                    "x_categorical": xheader_categorical,
                                    "gb": groupby_attribute,
                                }

                                if (
                                    not xheader_categorical
                                ):  # For WHERE clause without categorical equality
                                    n_total_point.pop("if_contain_x_categorical")
                                    qe_mdn = MdnQueryEngineNoRange(
                                        config=self.config.copy()
                                    )
                                    qe_mdn.fit(
                                        mdl,
                                        tbl,
                                        xys["data"],
                                        n_total_point,
                                        usecols,
                                        self.runtime_config,
                                    )
                                else:  # For WHERE clause with categorical equality
                                    qe_mdn = MdnQueryEngineNoRangeCategorical(
                                        config=self.config.copy()
                                    )
                                    qe_mdn.fit(
                                        mdl,
                                        tbl,
                                        xys,
                                        n_total_point,
                                        usecols,
                                        self.runtime_config,
                                    )
                                qe_mdn.serialize2warehouse(
                                    self.config.get_config()["warehousedir"],
                                    self.runtime_config,
                                )
                                self.model_catalog.add_model_wrapper(
                                    qe_mdn, self.runtime_config
                                )
                        else:
                            if method.lower() == "uniform":
                                if not n_total_point["if_contain_x_categorical"]:
                                    if not self.config.get_config()["b_use_gg"]:
                                        n_total_point.pop("if_contain_x_categorical")
                                        kdeModelWrapper = KdeModelTrainer(
                                            mdl,
                                            tbl,
                                            xheader_continous[0],
                                            yheader,
                                            groupby_attribute=groupby_attribute,
                                            groupby_values=list(n_total_point.keys()),
                                            n_total_point=n_total_point,
                                            x_min_value=-np.inf,
                                            x_max_value=np.inf,
                                            config=self.config.copy(),
                                        ).fit_from_df(
                                            xys["data"],
                                            self.runtime_config,
                                            network_size=None,
                                        )

                                        qe_mdn = MdnQueryEngine(
                                            kdeModelWrapper, config=self.config.copy()
                                        )
                                        qe_mdn.serialize2warehouse(
                                            self.config.get_config()["warehousedir"],
                                            self.runtime_config,
                                        )
                                        self.model_catalog.add_model_wrapper(
                                            qe_mdn, self.runtime_config
                                        )

                                    else:
                                        queryEngineBundle = MdnQueryEngineGoGs(
                                            config=self.config.copy()
                                        ).fit(
                                            xys["data"],
                                            groupby_attribute,
                                            n_total_point,
                                            mdl,
                                            tbl,
                                            xheader_continous[0],
                                            yheader,
                                            self.runtime_config,
                                        )

                                        self.model_catalog.add_model_wrapper(
                                            queryEngineBundle, self.runtime_config
                                        )
                                        queryEngineBundle.serialize2warehouse(
                                            self.config.get_config()["warehousedir"],
                                            self.runtime_config,
                                        )
                                else:  # x has categorical attributes
                                    # if not self.config.get_config()["b_use_gg"]:
                                    # use a single model to support categorical conditions.
                                    if self.config.config["one_model"]:
                                        qe = MdnQueryEngineXCategoricalOneModel(
                                            self.config.copy()
                                        )
                                        usecols = {
                                            "y": yheader,
                                            "x_continous": xheader_continous,
                                            "x_categorical": xheader_categorical,
                                            "gb": groupby_attribute,
                                        }
                                        useCols = UseCols(usecols)

                                        # get the training data from samples.
                                        (
                                            gbs,
                                            xs,
                                            ys,
                                        ) = useCols.get_gb_x_y_cols_for_one_model()
                                        (
                                            gbs_data,
                                            xs_data,
                                            ys_data,
                                        ) = sampler.sample.get_columns_from_original_sample(
                                            gbs, xs, ys
                                        )
                                        n_total_point = sampler.sample.get_frequency_of_categorical_columns_for_gbs(
                                            groupby_attribute, xheader_categorical
                                        )

                                        scaled_n_total_point = {}
                                        for key in n_total_point:
                                            scaled_n_total_point[key] = {}
                                            for sub_key in n_total_point[key]:
                                                scaled_n_total_point[key][sub_key] = (
                                                    n_total_point[key][sub_key] / ratio
                                                )
                                        n_total_point = scaled_n_total_point

                                        qe.fit(
                                            mdl,
                                            tbl,
                                            gbs_data,
                                            xs_data,
                                            ys_data,
                                            n_total_point,
                                            usecols=usecols,
                                            runtime_config=self.runtime_config,
                                        )
                                    else:
                                        qe = MdnQueryEngineXCategorical(
                                            self.config.copy()
                                        )
                                        qe.fit(
                                            mdl,
                                            tbl,
                                            xys,
                                            n_total_point,
                                            usecols={
                                                "y": yheader,
                                                "x_continous": xheader_continous,
                                                "x_categorical": xheader_categorical,
                                                "gb": groupby_attribute,
                                            },
                                            runtime_config=self.runtime_config,
                                        )
                                        qe.serialize2warehouse(
                                            self.config.get_config()["warehousedir"],
                                            self.runtime_config,
                                        )
                                        self.model_catalog.add_model_wrapper(
                                            qe, self.runtime_config
                                        )

                                    qe.serialize2warehouse(
                                        self.config.get_config()["warehousedir"],
                                        self.runtime_config,
                                    )
                                    self.model_catalog.add_model_wrapper(
                                        qe, self.runtime_config
                                    )
                            elif method.lower() == "stratified":
                                if xheader_categorical:
                                    (
                                        gbs_data,
                                        xs_data,
                                        ys_data,
                                    ) = sampler.sample.get_categorical_features_label()
                                    n_total_point = sampler.sample.get_ft()
                                    usecols = {
                                        "y": yheader,
                                        "x_continous": xheader_continous,
                                        "x_categorical": xheader_categorical,
                                        "gb": groupby_attribute,
                                    }
                                    xs_data = xs_data.reshape(1, -1)[0]

                                    qe = MdnQueryEngineXCategoricalOneModel(
                                        self.config.copy()
                                    )

                                    qe.fit(
                                        mdl,
                                        tbl,
                                        gbs_data,
                                        xs_data,
                                        ys_data,
                                        n_total_point,
                                        usecols=usecols,
                                        runtime_config=self.runtime_config,
                                    )
                                    qe.serialize2warehouse(
                                        self.config.get_config()["warehousedir"],
                                        self.runtime_config,
                                    )
                                    self.model_catalog.add_model_wrapper(
                                        qe, self.runtime_config
                                    )
                                else:  # contain range, but not equality
                                    (
                                        gbs_data,
                                        xs_data,
                                        ys_data,
                                    ) = sampler.sample.get_categorical_features_label()
                                    n_total_point = sampler.sample.get_ft()
                                    # print("n_total_point", n_total_point)
                                    usecols = {
                                        "y": yheader,
                                        "x_continous": xheader_continous,
                                        "x_categorical": xheader_categorical,
                                        "gb": groupby_attribute,
                                    }
                                    xs_data = xs_data.reshape(1, -1)[0]

                                    qe = MdnQueryEngineRangeNoCategorical(
                                        self.config.copy()
                                    )
                                    qe.fit(
                                        mdl,
                                        tbl,
                                        gbs_data,
                                        xs_data,
                                        ys_data,
                                        n_total_point,
                                        usecols=usecols,
                                        runtime_config=self.runtime_config,
                                    )
                                    qe.serialize2warehouse(
                                        self.config.get_config()["warehousedir"],
                                        self.runtime_config,
                                    )
                                    self.model_catalog.add_model_wrapper(
                                        qe, self.runtime_config
                                    )

                            else:
                                raise TypeError("unexpected sampling method.")
                time2 = datetime.now()
                t = (time2 - time1).seconds
                if self.runtime_config["b_show_latency"]:
                    print("time cost: " + str(t) + "s.")
                print("------------------------")

                # rest config
                self.last_config = None
                return "success", "success", None, t


            elif sql_type == "select":  # process SELECT query
                start_time = datetime.now()
                predictions = None
                # DML, provide the prediction using models
                mdl = self.parser.get_from_name()

                print(f'# model name: {mdl}')
                print(f'# function return: {self.parser.get_dml_aggregate_function_and_variable()}')

                gb_to_print, [
                    func,
                    yheader,
                    distinct_condition,
                    temp,
                ] = self.parser.get_dml_aggregate_function_and_variable()


                # for query with WHERE clause containing range selector
                if (
                    self.parser.if_where_exists()
                    and self.parser.get_dml_where_categorical_equal_and_range()[2]
                ):

                    print("OK")
                    where_conditions = (
                        self.parser.get_dml_where_categorical_equal_and_range()
                    )

                    if (
                        mdl + self.runtime_config["model_suffix"] 
                        not in self.model_catalog.model_catalog
                    ):
                        print("Model " + mdl + " does not exist.")
                        return "fail", "Model " + mdl + " does not exist.", None, None

                    model = self.model_catalog.model_catalog[
                        mdl + self.runtime_config["model_suffix"]
                    ]
                    x_header_density = model.density_column

                    [x_lb, x_ub] = [
                        where_conditions[2][x_header_density][i] for i in [0, 1]
                    ]
                    filter_etriml = dict(where_conditions[2])
                    filter_etriml = [
                        filter_etriml[next(iter(filter_etriml))][i] for i in [0, 1]
                    ]

                    print("func : ", func)
                    print("x_lb : ", x_lb)
                    print("x_ub : ", x_ub)
                    # print("where_conditions : ", where_conditions)
                    print("filter_etriml : ", filter_etriml)

                    predictions = model.predicts(
                        func,
                        x_lb,
                        x_ub,
                        where_conditions,
                        self.runtime_config,
                        groups=None,
                        filter_etriml=filter_etriml,
                    )

                elif func == "var":
                    print("var!!")
                    model = self.model_catalog.model_catalog[
                        mdl + self.runtime_config["model_suffix"]
                    ]
                    x_header_density = model.density_column
                    predictions = model.predicts(
                        "var", runtime_config=self.runtime_config
                    )
                    # return predictions
                else:  # for query without WHERE range selector clause
                    print("OK")
                    where_conditions = (
                        self.parser.get_dml_where_categorical_equal_and_range()
                    )
                    if (
                        mdl + self.runtime_config["model_suffix"]
                        not in self.model_catalog.model_catalog
                    ):
                        print("Model " + mdl + " does not exist.")
                        return
                    model = self.model_catalog.model_catalog[
                        mdl + self.runtime_config["model_suffix"]
                    ]
                    predictions = model.predicts(
                        func,
                        None,
                        None,
                        where_conditions,
                        self.runtime_config,
                        groups=None,
                        filter_etriml=None,
                    )

                if self.runtime_config["b_print_to_screen"]:
                    # print(predictions.to_csv(sep=',', index=False))  # sep='\t'
                    print(predictions.to_string(index=False))  # max_rows=5

                if self.runtime_config["result2file"]:
                    predictions.to_csv(self.runtime_config["result2file"],header=False, sep=',', index=False, quoting=csv.QUOTE_NONE, quotechar="",  escapechar=" ")
                    # print(predictions.to_csv(sep=',', index=False))  # sep='\t'
                    # with open(self.runtime_config["result2file"],'w') as f:
                    #     out = 
                    #     f.write(predictions.to_string(index=False))  # max_rows=5

                time_cost = None
                if self.runtime_config["b_show_latency"]:
                    end_time = datetime.now()
                    time_cost = (end_time - start_time).total_seconds()
                    print("Time cost: %.4fs." % time_cost)
                print("------------------------")
                return "success", "success", predictions, time_cost

            elif sql_type == "set":  # process SET query
                if self.last_config:
                    self.config = self.last_config
                else:
                    self.config = EtrimlConfig()
                try:
                    key, value = self.parser.get_set_variable_value()
                    if key in self.config.get_config():
                        # check variable value before assignment
                        if key.lower() == "encoder":
                            value = value.lower()
                            if value not in ["onehot", "binary", "embedding"]:
                                value = "binary"
                                print(
                                    "encoder is not set to a proper value, use default encoding type: binary."
                                )

                        self.config.get_config()[key] = value
                        print("OK, " + key + " is updated.")
                    else:  # if variable is within runtime_config
                        # check if "device" is set. we need to make usre when GPU is not availabe, cpu is used instead.
                        if key.lower() == "device":
                            value = value.lower()
                            if value in ["cpu", "gpu"]:
                                if torch.cuda.is_available():
                                    if value == "gpu":
                                        value = "cuda:0"
                                        try:
                                            set_start_method_torch("spawn")
                                        except RuntimeError:
                                            print(
                                                "Fail to set start method as spawn for pytorch multiprocessing, "
                                                + "use default in advance. (see queryenginemdn "
                                                "for more info.)"
                                            )
                                    else:
                                        set_start_method_cpu("spawn")
                                    if self.runtime_config["v"]:
                                        print("device is set to " + value)
                                else:
                                    if value == "gpu":
                                        print("GPU is not available, use CPU instead")
                                        value = "cpu"
                                    if value == "cpu":
                                        if self.runtime_config["v"]:
                                            print("device is set to " + value)
                            else:
                                print("Only GPU or CPU is supported.")
                                return

                        self.runtime_config[key] = value
                        if key in self.runtime_config:
                            print("OK, " + key + " is updated.")
                        else:
                            print("OK, local variable " + key + " is defined.")
                except TypeError:
                    # self.parser.get_set_variable_value() does not return correctly
                    print("Parameter is not changed. Please check your SQL!")

                # save the config
                self.last_config = self.config
                return

            elif sql_type == "drop":  # process DROP query
                model_name = self.parser.drop_get_model()
                model_path = os.path.join(
                    self.config.get_config()["warehousedir"],
                    model_name + self.runtime_config["model_suffix"],
                )
                if os.path.isfile(model_path):
                    os.remove(model_path)
                    print("OK. model is dropped.")
                    return "success", "success", None, None
                else:
                    print("Model does not exist!")
                    return "fail", "Model does not exist!", None, None

            elif sql_type == "show":
                print("OK")
                t_start = datetime.now()
                if self.runtime_config["b_print_to_screen"]:
                    for key in self.model_catalog.model_catalog:
                        print(key.replace(self.runtime_config["model_suffix"], ""))

                val = ""
                for key in self.model_catalog.model_catalog:
                    val = val + key.replace(self.runtime_config["model_suffix"], "") + "\t"

                print(val)
                if self.runtime_config["v"]:
                    t_end = datetime.now()
                    time_cost = (t_end - t_start).total_seconds()
                    print("Time cost: %.4fs." % time_cost)
                
                return "success",  None, val, None

            else:
                print("Unsupported query type, please check your SQL.")
                return

    def execute_mlflow(self, sql):
        #print(">>> executor > executor.py > SqlExecutor : execute_mlflow()")

        # prepare the parser
        if type(sql) == str:
            self.parser = ETRIMLParser()
            self.parser.parse(sql)
        elif type(sql) == ETRIMLParser:
            self.parser = sql
        else:
            print("Unrecognized SQL! Please check it!")
            return "fail", "Unrecognized SQL! Please check it!", None, None
            #exit(-1)

        # execute the query
        if self.parser.if_nested_query():
            warnings.warn("Nested query is currently not supported!")
            return "fail", "Nested query is currently not supported!", None, None
        else:
            sql_type = self.parser.get_query_type()
            if sql_type == "create":  # process create query
                # initialize the configure for each model creation.
                if self.last_config:
                    self.config = self.last_config
                else:
                    self.config = EtrimlConfig()
                # DDL, create the model as requested
                mdl = self.parser.get_ddl_model_name()
                tbl = self.parser.get_from_name()

                # remove unnecessary charactor '
                tbl = tbl.replace("'", "")
                if os.path.isfile(tbl):  # the absolute path is provided
                    original_data_file = tbl
                else:  # the file is in the warehouse direcotry
                    original_data_file = (
                        self.config.get_config()["warehousedir"] + "/" + tbl
                    )

                if os.path.isfile(original_data_file):  
                    print()
                else:      
                    return "fail", "No such file(" + tbl + ").", None, None

                yheader = self.parser.get_y()

                xheader_continous, xheader_categorical = self.parser.get_x()

                ratio = self.parser.get_sampling_ratio()
                method = self.parser.get_sampling_method()
                table_header = self.config.get_config()["table_header"]

                if table_header is not None:
                    table_header = table_header.split(
                        self.config.get_config()["csv_split_char"]
                    )
                if xheader_continous:  # there is no continuous attribute
                    if self.parser.if_model_need_filter():
                        self.config.set_parameter("accept_filter", True)

                # make samples
                if not self.parser.if_contain_groupby():  # if group by is not involved
                    sampler = ETRIMLSampling(
                        headers=table_header,
                        usecols={
                            "y": yheader,
                            "x_continous": xheader_continous,
                            "x_categorical": xheader_categorical,
                            "gb": None,
                        },
                        n_jobs=self.runtime_config["n_jobs"],
                        mdl_name=mdl,
                        warehouse=self.config.get_config()["warehousedir"]
                    )
                else:
                    groupby_attribute = self.parser.get_groupby_value()

                    # print("yheader", yheader)
                    # print("xheader_continous", xheader_continous)
                    # print("xheader_categorical", xheader_categorical)
                    # print("groupby_attribute", xheader_categorical)

                    sampler = ETRIMLSampling(
                        headers=table_header,
                        usecols={
                            "y": yheader,
                            "x_continous": xheader_continous,
                            "x_categorical": xheader_categorical,
                            "gb": groupby_attribute,
                        },
                        n_jobs=self.runtime_config["n_jobs"],
                        mdl_name=mdl,
                        warehouse=self.config.get_config()["warehousedir"]
                    )

                if os.path.exists(
                    os.path.join(
                        self.config.get_config()["warehousedir"],
                        mdl + self.runtime_config["model_suffix"],
                    )
                ):
                    print(
                        "Model {0} exists in the warehouse, please use"
                        " another model name to train it.".format(mdl)
                    )
                    return "fail", "Model {0} exists in the warehouse, please use another model name to train it.".format(mdl), None, None

                print("Start creating model " + mdl)
                time1 = datetime.now()

                # if method.lower() == "uniform":
                if self.save_sample:
                    sampler.make_sample(
                        original_data_file,
                        ratio,
                        method,
                        split_char=self.config.get_config()["csv_split_char"],
                        file2save=self.config.get_config()["warehousedir"]
                        + "/"
                        + mdl
                        + ".csv",
                        num_total_records=self.n_total_records,
                    )
                else:
                    sampler.make_sample(
                        original_data_file,
                        ratio,
                        method,
                        split_char=self.config.get_config()["csv_split_char"],
                        num_total_records=self.n_total_records,
                    )
                
                if self.runtime_config["sampling_only"]:
                    print("sample is generated and saved, end.")
                    return

                if not self.parser.if_contain_groupby():  # if group by is not involved
                    print ("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX create begin mlflow")
                    with mlflow.start_run(run_name="etriml") as run:
                        run_id = run.info.run_id
                        #print("mlflow run_id : ", run_id)
                        sampler.sample.sampledf["dummy_gb"] = "dummy"
                        sampler.sample.usecols = {
                            "y": yheader,
                            "x_continous": xheader_continous,
                            "x_categorical": xheader_categorical,
                            "gb": "dummy_gb",
                        }
                        n_total_point, xys = sampler.get_groupby_frequency_data()
                        # if not n_total_point['if_contain_x_categorical']:
                        n_total_point.pop("if_contain_x_categorical")
                        kdeModelWrapper = KdeModelTrainer(
                            mdl,
                            tbl,
                            xheader_continous[0],
                            yheader,
                            groupby_attribute=["dummy_gb"],
                            groupby_values=list(n_total_point.keys()),
                            n_total_point=n_total_point,
                            x_min_value=-np.inf,
                            x_max_value=np.inf,
                            config=self.config.copy(),
                        ).fit_from_df(
                            xys["data"], self.runtime_config, network_size="large"
                        )

                        qe_mdn = MdnQueryEngine(kdeModelWrapper, config=self.config.copy())
                        #print("qe_mdn \n", qe_mdn )
                        qe_mdn.serialize2warehouse(
                            self.config.get_config()["warehousedir"], self.runtime_config
                        )
                        self.model_catalog.add_model_wrapper(qe_mdn, self.runtime_config)

                        mlflow.log_param("alpha", 0.1)
                        mlflow.log_param("l1_ratio", 500)
                        mlflow.log_metric("rmse", 0.11)
                        mlflow.log_metric("r2", 0.22)
                        mlflow.log_metric("mae", 0.33)
                        
                        #model_x=None
                        #with open(self.config.get_config()["warehousedir"] + "/" + mdl + self.runtime_config["model_suffix"], "rb") as f:
                        #    model_x = dill.load(f)
                        #print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", type(model_x))

                        shutil.copy(self.config.get_config()["warehousedir"] + '/'+ mdl+ self.runtime_config["model_suffix"], './etriml_model.pth')

                        etriml_model_path = "etriml_model.pth"
                        artifacts = {"etriml_model": etriml_model_path}
                        mlflow_pyfunc_model_path = "etriml_mlflow_pyfunc"
                        #mlflow.pyfunc.save_model(path=mlflow_pyfunc_model_path, python_model=model_x, artifacts=artifacts)    
                        mlflow.pyfunc.save_model(
                            path=mlflow_pyfunc_model_path,
                            python_model=qe_mdn,
                            code_path=None, #['etrimlmlflowwrapper.py'],
                            artifacts=artifacts,
                            conda_env = {
                                'channels': ['defaults'],
                                'dependencies': [
                                  'python={}'.format(PYTHON_VERSION),
                                  'pip',
                                  {
                                    'pip': [
                                      'mlflow',
                                      'cloudpickle=={}'.format(cloudpickle.__version__),
                                    ],
                                  },
                                ],
                                'name': 'etriml_env'
                            }
                        )

                        shutil.copytree(mlflow_pyfunc_model_path, './mlruns/0/' + run_id + '/artifacts/model')
                        #mlflow.log_artifact("model")
                        #shutil.rmtree(mlflow_pyfunc_model_path)

                    print ("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX create end mlflow")
                else:  # if group by is involved in the query
                    if self.config.get_config()["reg_type"] == "qreg":
                        xys = sampler.getyx(yheader, xheader_continous)
                        n_total_point = get_group_count_from_table(
                            original_data_file,
                            groupby_attribute,
                            sep=self.config.get_config()["csv_split_char"],
                            headers=table_header,
                        )

                        n_sample_point = get_group_count_from_df(xys, groupby_attribute)
                        groupby_model_wrapper = GroupByModelTrainer(
                            mdl,
                            tbl,
                            xheader_continous,
                            yheader,
                            groupby_attribute,
                            n_total_point,
                            n_sample_point,
                            x_min_value=-np.inf,
                            x_max_value=np.inf,
                            config=self.config.copy(),
                        ).fit_from_df(xys, self.runtime_config)
                        groupby_model_wrapper.serialize2warehouse(
                            self.config.get_config()["warehousedir"]
                            + "/"
                            + groupby_model_wrapper.dir
                        )
                        self.model_catalog.model_catalog[
                            groupby_model_wrapper.dir
                        ] = groupby_model_wrapper.models
                    else:  # "mdn"
                        if method.lower() == "uniform":
                            xys = sampler.getyx(
                                yheader, xheader_continous, groupby=groupby_attribute
                            )

                            if isinstance(ratio, str):
                                frequency_file = (
                                    self.config.get_config()["warehousedir"]
                                    + "/"
                                    + ratio
                                )
                                if os.path.exists(frequency_file):
                                    n_total_point = get_group_count_from_summary_file(
                                        frequency_file, sep=","
                                    )
                                    (
                                        n_total_point_sample,
                                        xys,
                                    ) = sampler.get_groupby_frequency_data()
                                    n_total_point[
                                        "if_contain_x_categorical"
                                    ] = n_total_point_sample["if_contain_x_categorical"]
                                else:
                                    raise FileNotFoundError(
                                        "scaling factor should come from the "
                                        + ratio
                                        + " in the warehouse folder, as"
                                        " stated in the SQL. However, the file is not found."
                                    )
                            else:
                                (
                                    n_total_point,
                                    xys,
                                ) = sampler.get_groupby_frequency_data()

                                # for cases when the data file is treated as a sample, we need to scale up the frequency for each group.
                                if ratio > 1:
                                    file_size = sampler.n_total_point
                                    ratio = float(ratio) / file_size
                                # if 0 < ratio < 1:
                                scaled_n_total_point = {}
                                if "if_contain_x_categorical" in n_total_point:
                                    scaled_n_total_point[
                                        "if_contain_x_categorical"
                                    ] = n_total_point.pop("if_contain_x_categorical")
                                if "categorical_distinct_values" in n_total_point:
                                    scaled_n_total_point[
                                        "categorical_distinct_values"
                                    ] = n_total_point.pop("categorical_distinct_values")
                                if "x_categorical_columns" in n_total_point:
                                    scaled_n_total_point[
                                        "x_categorical_columns"
                                    ] = n_total_point.pop("x_categorical_columns")
                                for key in n_total_point:
                                    # print("key", key, n_total_point[key])

                                    if not isinstance(n_total_point[key], dict):
                                        scaled_n_total_point[key] = (
                                            n_total_point[key] / ratio
                                        )
                                    else:
                                        scaled_n_total_point[key] = {}
                                        for sub_key in n_total_point[key]:
                                            scaled_n_total_point[key][sub_key] = (
                                                n_total_point[key][sub_key] / ratio
                                            )
                                n_total_point = scaled_n_total_point
                                # print("scaled_n_total_point", scaled_n_total_point)
                        elif method.lower() == "stratified":
                            pass
                        else:
                            raise TypeError("unexpected method")

                        # no continuous x attributes, which means there is not range predicate on continuous attribute
                        if not xheader_continous:
                            # use one model to support all categorical attribute
                            if self.config.config["one_model"]:
                                qe = MdnQueryEngineNoRangeCategoricalOneModel(
                                    self.config.copy()
                                )
                                usecols = {
                                    "y": yheader,
                                    "x_continous": xheader_continous,
                                    "x_categorical": xheader_categorical,
                                    "gb": groupby_attribute,
                                }
                                if method.lower() == "uniform":
                                    useCols = UseCols(usecols)

                                    # get the training data from samples.
                                    (
                                        gbs,
                                        xs,
                                        ys,
                                    ) = useCols.get_gb_x_y_cols_for_one_model()
                                    (
                                        gbs_data,
                                        xs_data,
                                        ys_data,
                                    ) = sampler.sample.get_columns_from_original_sample(
                                        gbs, xs, ys
                                    )
                                    n_total_point = sampler.sample.get_frequency_of_categorical_columns_for_gbs(
                                        groupby_attribute, xheader_categorical
                                    )

                                    scaled_n_total_point = {}
                                    for key in n_total_point:
                                        scaled_n_total_point[key] = {}
                                        for sub_key in n_total_point[key]:
                                            scaled_n_total_point[key][sub_key] = (
                                                n_total_point[key][sub_key] / ratio
                                            )
                                    n_total_point = scaled_n_total_point

                                    qe.fit(
                                        mdl,
                                        tbl,
                                        gbs_data,
                                        xs_data,
                                        ys_data,
                                        n_total_point,
                                        usecols=usecols,
                                        runtime_config=self.runtime_config,
                                    )

                                elif method.lower() == "stratified":
                                    # check if this query could be served by frequency table only.

                                    b_ft_only = parse_y_check_need_ft_only(usecols)
                                    # print("b_ft_only", b_ft_only)
                                    if b_ft_only:
                                        # print("to implement")
                                        n_total_point = sampler.sample.get_ft()
                                        # print("ft", n_total_point)
                                        qe = QueryEngineFrequencyTable(
                                            self.config.copy()
                                        )
                                        qe.fit(
                                            mdl,
                                            tbl,
                                            None,
                                            None,
                                            None,
                                            n_total_point,
                                            usecols=usecols,
                                            runtime_config=self.runtime_config,
                                        )
                                        # exit()

                                    else:
                                        (
                                            gbs_data,
                                            xs_data,
                                            ys_data,
                                        ) = (
                                            sampler.sample.get_categorical_features_label()
                                        )
                                        n_total_point = sampler.sample.get_ft()

                                        qe.fit(
                                            mdl,
                                            tbl,
                                            gbs_data,
                                            xs_data,
                                            ys_data,
                                            n_total_point,
                                            usecols=usecols,
                                            runtime_config=self.runtime_config,
                                        )
                                qe.serialize2warehouse(
                                    self.config.get_config()["warehousedir"],
                                    self.runtime_config,
                                )
                                self.model_catalog.add_model_wrapper(
                                    qe, self.runtime_config
                                )
                            else:  # train seperate models for each categorical attribute
                                usecols = {
                                    "y": yheader,
                                    "x_continous": xheader_continous,
                                    "x_categorical": xheader_categorical,
                                    "gb": groupby_attribute,
                                }

                                if (
                                    not xheader_categorical
                                ):  # For WHERE clause without categorical equality
                                    n_total_point.pop("if_contain_x_categorical")
                                    qe_mdn = MdnQueryEngineNoRange(
                                        config=self.config.copy()
                                    )
                                    qe_mdn.fit(
                                        mdl,
                                        tbl,
                                        xys["data"],
                                        n_total_point,
                                        usecols,
                                        self.runtime_config,
                                    )
                                else:  # For WHERE clause with categorical equality
                                    qe_mdn = MdnQueryEngineNoRangeCategorical(
                                        config=self.config.copy()
                                    )
                                    qe_mdn.fit(
                                        mdl,
                                        tbl,
                                        xys,
                                        n_total_point,
                                        usecols,
                                        self.runtime_config,
                                    )
                                qe_mdn.serialize2warehouse(
                                    self.config.get_config()["warehousedir"],
                                    self.runtime_config,
                                )
                                self.model_catalog.add_model_wrapper(
                                    qe_mdn, self.runtime_config
                                )
                        else:
                            if method.lower() == "uniform":
                                if not n_total_point["if_contain_x_categorical"]:
                                    if not self.config.get_config()["b_use_gg"]:
                                        n_total_point.pop("if_contain_x_categorical")
                                        kdeModelWrapper = KdeModelTrainer(
                                            mdl,
                                            tbl,
                                            xheader_continous[0],
                                            yheader,
                                            groupby_attribute=groupby_attribute,
                                            groupby_values=list(n_total_point.keys()),
                                            n_total_point=n_total_point,
                                            x_min_value=-np.inf,
                                            x_max_value=np.inf,
                                            config=self.config.copy(),
                                        ).fit_from_df(
                                            xys["data"],
                                            self.runtime_config,
                                            network_size=None,
                                        )

                                        qe_mdn = MdnQueryEngine(
                                            kdeModelWrapper, config=self.config.copy()
                                        )
                                        qe_mdn.serialize2warehouse(
                                            self.config.get_config()["warehousedir"],
                                            self.runtime_config,
                                        )
                                        self.model_catalog.add_model_wrapper(
                                            qe_mdn, self.runtime_config
                                        )

                                    else:
                                        queryEngineBundle = MdnQueryEngineGoGs(
                                            config=self.config.copy()
                                        ).fit(
                                            xys["data"],
                                            groupby_attribute,
                                            n_total_point,
                                            mdl,
                                            tbl,
                                            xheader_continous[0],
                                            yheader,
                                            self.runtime_config,
                                        )

                                        self.model_catalog.add_model_wrapper(
                                            queryEngineBundle, self.runtime_config
                                        )
                                        queryEngineBundle.serialize2warehouse(
                                            self.config.get_config()["warehousedir"],
                                            self.runtime_config,
                                        )
                                else:  # x has categorical attributes
                                    # if not self.config.get_config()["b_use_gg"]:
                                    # use a single model to support categorical conditions.
                                    if self.config.config["one_model"]:
                                        qe = MdnQueryEngineXCategoricalOneModel(
                                            self.config.copy()
                                        )
                                        usecols = {
                                            "y": yheader,
                                            "x_continous": xheader_continous,
                                            "x_categorical": xheader_categorical,
                                            "gb": groupby_attribute,
                                        }
                                        useCols = UseCols(usecols)

                                        # get the training data from samples.
                                        (
                                            gbs,
                                            xs,
                                            ys,
                                        ) = useCols.get_gb_x_y_cols_for_one_model()
                                        (
                                            gbs_data,
                                            xs_data,
                                            ys_data,
                                        ) = sampler.sample.get_columns_from_original_sample(
                                            gbs, xs, ys
                                        )
                                        n_total_point = sampler.sample.get_frequency_of_categorical_columns_for_gbs(
                                            groupby_attribute, xheader_categorical
                                        )

                                        scaled_n_total_point = {}
                                        for key in n_total_point:
                                            scaled_n_total_point[key] = {}
                                            for sub_key in n_total_point[key]:
                                                scaled_n_total_point[key][sub_key] = (
                                                    n_total_point[key][sub_key] / ratio
                                                )
                                        n_total_point = scaled_n_total_point

                                        qe.fit(
                                            mdl,
                                            tbl,
                                            gbs_data,
                                            xs_data,
                                            ys_data,
                                            n_total_point,
                                            usecols=usecols,
                                            runtime_config=self.runtime_config,
                                        )
                                    else:
                                        qe = MdnQueryEngineXCategorical(
                                            self.config.copy()
                                        )
                                        qe.fit(
                                            mdl,
                                            tbl,
                                            xys,
                                            n_total_point,
                                            usecols={
                                                "y": yheader,
                                                "x_continous": xheader_continous,
                                                "x_categorical": xheader_categorical,
                                                "gb": groupby_attribute,
                                            },
                                            runtime_config=self.runtime_config,
                                        )
                                        qe.serialize2warehouse(
                                            self.config.get_config()["warehousedir"],
                                            self.runtime_config,
                                        )
                                        self.model_catalog.add_model_wrapper(
                                            qe, self.runtime_config
                                        )

                                    qe.serialize2warehouse(
                                        self.config.get_config()["warehousedir"],
                                        self.runtime_config,
                                    )
                                    self.model_catalog.add_model_wrapper(
                                        qe, self.runtime_config
                                    )
                            elif method.lower() == "stratified":
                                if xheader_categorical:
                                    (
                                        gbs_data,
                                        xs_data,
                                        ys_data,
                                    ) = sampler.sample.get_categorical_features_label()
                                    n_total_point = sampler.sample.get_ft()
                                    usecols = {
                                        "y": yheader,
                                        "x_continous": xheader_continous,
                                        "x_categorical": xheader_categorical,
                                        "gb": groupby_attribute,
                                    }
                                    xs_data = xs_data.reshape(1, -1)[0]

                                    qe = MdnQueryEngineXCategoricalOneModel(
                                        self.config.copy()
                                    )

                                    qe.fit(
                                        mdl,
                                        tbl,
                                        gbs_data,
                                        xs_data,
                                        ys_data,
                                        n_total_point,
                                        usecols=usecols,
                                        runtime_config=self.runtime_config,
                                    )
                                    qe.serialize2warehouse(
                                        self.config.get_config()["warehousedir"],
                                        self.runtime_config,
                                    )
                                    self.model_catalog.add_model_wrapper(
                                        qe, self.runtime_config
                                    )
                                else:  # contain range, but not equality
                                    (
                                        gbs_data,
                                        xs_data,
                                        ys_data,
                                    ) = sampler.sample.get_categorical_features_label()
                                    n_total_point = sampler.sample.get_ft()
                                    # print("n_total_point", n_total_point)
                                    usecols = {
                                        "y": yheader,
                                        "x_continous": xheader_continous,
                                        "x_categorical": xheader_categorical,
                                        "gb": groupby_attribute,
                                    }
                                    xs_data = xs_data.reshape(1, -1)[0]

                                    qe = MdnQueryEngineRangeNoCategorical(
                                        self.config.copy()
                                    )
                                    qe.fit(
                                        mdl,
                                        tbl,
                                        gbs_data,
                                        xs_data,
                                        ys_data,
                                        n_total_point,
                                        usecols=usecols,
                                        runtime_config=self.runtime_config,
                                    )
                                    qe.serialize2warehouse(
                                        self.config.get_config()["warehousedir"],
                                        self.runtime_config,
                                    )
                                    self.model_catalog.add_model_wrapper(
                                        qe, self.runtime_config
                                    )

                            else:
                                raise TypeError("unexpected sampling method.")
                time2 = datetime.now()
                t = (time2 - time1).seconds
                print()
                if self.runtime_config["b_show_latency"]:
                    print("time cost: " + str(t) + "s.")
                print()

                print("**********************************************************")
                print("**********************************************************")
                print(">>> MLFLOW RUN_ID  : ", run_id, "<<<")
                print("**********************************************************")
                print("**********************************************************")
                print()
                print()
                print("======================================================================")

                # rest config
                self.last_config = None
                return "success", "success", None, t

            elif sql_type == "select":  # process SELECT query

                start_time = datetime.now()
                predictions = None
                # DML, provide the prediction using models
                mdl = self.parser.get_from_name()

                print(f'# model name: {mdl}')
                print(f'# function return: {self.parser.get_dml_aggregate_function_and_variable()}')

                gb_to_print, [
                    func,
                    yheader,
                    distinct_condition,
                    temp,
                ] = self.parser.get_dml_aggregate_function_and_variable()


                # for query with WHERE clause containing range selector
                if (
                    self.parser.if_where_exists()
                    and self.parser.get_dml_where_categorical_equal_and_range()[2]
                ):
                    #print("OK1")

                    where_conditions = (
                        self.parser.get_dml_where_categorical_equal_and_range()
                    )
                    if (
                        mdl + self.runtime_config["model_suffix"] 
                        not in self.model_catalog.model_catalog
                    ):
                        print("Model " + mdl + " does not exist.")
                        return "fail", "Model " + mdl + " does not exist.", None, None


                    model = self.model_catalog.model_catalog[
                        mdl + self.runtime_config["model_suffix"]
                    ]

                    x_header_density = model.density_column

                    [x_lb, x_ub] = [
                        where_conditions[2][x_header_density][i] for i in [0, 1]
                    ]
                    filter_etriml = dict(where_conditions[2])
                    filter_etriml = [
                        filter_etriml[next(iter(filter_etriml))][i] for i in [0, 1]
                    ]

                    print("======================================================================")
                    print("PARAMETERS")
                    print("----------------------------------------------------------------------")
                    print("func\t: ", func)
                    print("x_lb\t: ", x_lb)
                    print("x_ub\t: ", x_ub)
                    print("where\t: ", where_conditions)
                    print("filter\t: ", filter_etriml)

                    #predictions = model.predicts(
                    #    func,
                    #    x_lb,
                    #    x_ub,
                    #   where_conditions,
                    #    self.runtime_config,
                    #    groups=None,
                    #    filter_etriml=filter_etriml,
                    #)
                    #print("predictions : ", predictions)
                    #print("111type(predictions) : ", type(predictions))

                    #host = '127.0.0.1'
                    #port = '8003'

                    url = 'http://127.0.0.1:8003/invocations'

                    headers = {
                        'Content-Type': 'application/json',
                    }

                    # Load training and test datasets
                    from sys import version_info

                    x_test = [func, x_lb, x_ub, where_conditions, self.runtime_config, None, filter_etriml]
                    #print("x_test : ", x_test)
                    # test_data is a Pandas dataframe with data for testing the ML model
                    import pandas as pd
                    model_input = pd.DataFrame(x_test)
                    #print("model_input : ", model_input)

                    http_data = model_input .to_json(orient='split')
                    #print("http_data : ", http_data)

                    res = requests.post(url=url, headers=headers, data=http_data)

                    #print("res : ", str(res))
                    #print(f'res: {res.text}')
                    lst_A = json.loads(res.text)
                    predictions = pd.DataFrame(lst_A)
                    #print("predictions : \n", predictions)
                    #print("222type(predictions) : ", type(predictions))

                    print("======================================================================")
                    print("RESULT")
                    print("----------------------------------------------------------------------")
                elif func == "var":
                    print("var!!")
                    model = self.model_catalog.model_catalog[
                        mdl + self.runtime_config["model_suffix"]
                    ]
                    x_header_density = model.density_column
                    predictions = model.predicts(
                        "var", runtime_config=self.runtime_config
                    )
                    # return predictions
                else:  # for query without WHERE range selector clause
                    print("OK3")
                    where_conditions = (
                        self.parser.get_dml_where_categorical_equal_and_range()
                    )
                    if (
                        mdl + self.runtime_config["model_suffix"]
                        not in self.model_catalog.model_catalog
                    ):
                        print("Model " + mdl + " does not exist.")
                        return
                    model = self.model_catalog.model_catalog[
                        mdl + self.runtime_config["model_suffix"]
                    ]
                    predictions = model.predicts(
                        func,
                        None,
                        None,
                        where_conditions,
                        self.runtime_config,
                        groups=None,
                        filter_etriml=None,
                    )


                if self.runtime_config["b_print_to_screen"]:
                    # print(predictions.to_csv(sep=',', index=False))  # sep='\t'
                    print(predictions.to_string(index=False))  # max_rows=5

                if self.runtime_config["result2file"]:
                    predictions.to_csv(self.runtime_config["result2file"],header=False, sep=',', index=False, quoting=csv.QUOTE_NONE, quotechar="",  escapechar=" ")
                    # print(predictions.to_csv(sep=',', index=False))  # sep='\t'
                    # with open(self.runtime_config["result2file"],'w') as f:
                    #     out = 
                    #     f.write(predictions.to_string(index=False))  # max_rows=5

                time_cost = None
                if self.runtime_config["b_show_latency"]:
                    end_time = datetime.now()
                    time_cost = (end_time - start_time).total_seconds()
                    print("----------------------------------------------------------------------")
                    print("time cost: %.4fs." % time_cost)
                    print("======================================================================")

                return "success", "success", predictions, time_cost

            elif sql_type == "set":  # process SET query
                if self.last_config:
                    self.config = self.last_config
                else:
                    self.config = EtrimlConfig()
                try:
                    key, value = self.parser.get_set_variable_value()
                    if key in self.config.get_config():
                        # check variable value before assignment
                        if key.lower() == "encoder":
                            value = value.lower()
                            if value not in ["onehot", "binary", "embedding"]:
                                value = "binary"
                                print(
                                    "encoder is not set to a proper value, use default encoding type: binary."
                                )

                        self.config.get_config()[key] = value
                        print("OK, " + key + " is updated.")
                    else:  # if variable is within runtime_config
                        # check if "device" is set. we need to make usre when GPU is not availabe, cpu is used instead.
                        if key.lower() == "device":
                            value = value.lower()
                            if value in ["cpu", "gpu"]:
                                if torch.cuda.is_available():
                                    if value == "gpu":
                                        value = "cuda:0"
                                        try:
                                            set_start_method_torch("spawn")
                                        except RuntimeError:
                                            print(
                                                "Fail to set start method as spawn for pytorch multiprocessing, "
                                                + "use default in advance. (see queryenginemdn "
                                                "for more info.)"
                                            )
                                    else:
                                        set_start_method_cpu("spawn")
                                    if self.runtime_config["v"]:
                                        print("device is set to " + value)
                                else:
                                    if value == "gpu":
                                        print("GPU is not available, use CPU instead")
                                        value = "cpu"
                                    if value == "cpu":
                                        if self.runtime_config["v"]:
                                            print("device is set to " + value)
                            else:
                                print("Only GPU or CPU is supported.")
                                return

                        self.runtime_config[key] = value
                        if key in self.runtime_config:
                            print("OK, " + key + " is updated.")
                        else:
                            print("OK, local variable " + key + " is defined.")
                except TypeError:
                    # self.parser.get_set_variable_value() does not return correctly
                    print("Parameter is not changed. Please check your SQL!")

                # save the config
                self.last_config = self.config
                return

            elif sql_type == "drop":  # process DROP query
                model_name = self.parser.drop_get_model()
                model_path = os.path.join(
                    self.config.get_config()["warehousedir"],
                    model_name + self.runtime_config["model_suffix"],
                )
                if os.path.isfile(model_path):
                    os.remove(model_path)
                    print("OK. model is dropped.")
                    return "success", "success", None, None
                else:
                    print("Model does not exist!")
                    return "fail", "Model does not exist!", None, None

            elif sql_type == "show":
                print("OK")
                t_start = datetime.now()
                if self.runtime_config["b_print_to_screen"]:
                    for key in self.model_catalog.model_catalog:
                        print(key.replace(self.runtime_config["model_suffix"], ""))

                val = ""
                for key in self.model_catalog.model_catalog:
                    val = val + key.replace(self.runtime_config["model_suffix"], "") + "\t"

                print(val)
                if self.runtime_config["v"]:
                    t_end = datetime.now()
                    time_cost = (t_end - t_start).total_seconds()
                    print("Time cost: %.4fs." % time_cost)
                
                return "success",  None, val, None

            else:
                print("Unsupported query type, please check your SQL.")
                return

    def set_table_counts(self, dic):
        #print(">>> executor > executor.py > SqlExecutor : set_table_counts()")

        self.n_total_records = dic
