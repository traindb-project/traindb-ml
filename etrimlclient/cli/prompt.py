import json
import os
from cmd import Cmd

from etrimlclient.executor.executor import SqlExecutor

config = {
    'warehousedir': 'etrimlwarehouse',
    'verbose': 'True',
    'b_show_latency': 'True',
    'backend_server': 'None',
    'epsabs': 10.0,
    'epsrel': 0.1,
    'mesh_grid_num': 20,
    'limit': 30,
    'csv_split_char': ',',
    "num_epoch": 400,
    "reg_type": "mdn",
}


class ETRIMLPrompt(Cmd):
    def __init__(self):
        super(ETRIMLPrompt, self).__init__()
        self.prompt = 'etrimlclient> '
        self.intro = "Welcome to ETRIML: a model-based AQP engine! Type exit to exit!"
        self.query = ""

        # deal with configuration file
        if os.path.exists('config.json'):
            print("Configuration file loaded.")
            self.config = json.load(open('config.json'))
        else:
            print("Configuration file config.json does not exist! use default values")
            self.config = config
            json.dump(self.config, open('config.json', 'w'))
        self.verbose = self.config['verbose']
        self.b_show_latency = self.config['b_show_latency']

        # deal with warehouse
        if os.path.exists("etrimlwarehouse"):
            print("warehouse is initialized.")
        else:
            print("warehouse does not exists, so initialize one.")
            os.mkdir("etrimlwarehouse")

        self.sqlExecutor = SqlExecutor()

    # print the exit message.
    def do_exit(self, inp):
        '''exit the application.'''
        print("ETRIML closed successfully.")
        return True

    def do_select(self, inp):
        # print("TrainDB select statement is called.")
        # self.default(inp=inp)
        # print(f'# input query: {inp}')
        self.query = 'select '+ inp.split(";")[0]
        # print("Executing query >>> " + self.query + "...")
        # self.query += inp.split(";")[0]
        self.sqlExecutor.execute(self.query)
        # self.sqlExecutor.execute("select count(pm25 real) from mdl")

    def do_create(self, inp):
        # print("TrainDB create statement is called.")
        # self.default(inp=inp)
        # print(f'# input query: {inp}')
        self.query = 'create '+ inp
        self.sqlExecutor.execute(self.query)
        # self.sqlExecutor.execute("create table mdl1(pm25 real, PRES real) from pm25.csv  method uniform size 100")

            
    # process the query
    def default(self, inp):
        if ";" not in inp:
            self.query = self.query + inp + " "
        else:
            self.query += inp.split(";")[0]
            # if self.config['verbose']:
            #     print("Executing query >>> " + self.query + "...")

            # query execution goes here
            # -------------------------------------------->>
            # check if query begins with 'bypass', if so use backend server, otherwise use etriml to give a prediction
            if self.query.lstrip()[0:6].lower() == 'bypass':
                print("Bypass ETRIML, use the backend server instead.")
                # go to the backend server
            else:
                # sqlExecutor = SqlExecutor(config)
                # print(self.query)
                # self.query.replace(";",'')
                self.sqlExecutor.execute(self.query)

                # self.sqlExecutor.execute("create table mdl1(pm25 real, PRES real) from pm25.csv  method uniform size 100")
                # self.sqlExecutor.execute("select count(pm25 real) from mdl1 where PRES between 1000 and 1020")
                # sqlExecutor.execute("select sum(pm25 real) from mdl where PRES between 1000 and 1020")
                # sqlExecutor.execute("select avg(pm25 real) from mdl where PRES between 1000 and 1020")
                # self.sqlExecutor.execute("create table ss(ss_list_price real, ss_wholesale_cost real) from store_sales.dat  method uniform size 10000 group by ss_store_sk")
                # self.sqlExecutor.execute("select count(ss_list_price) from ss where ss_wholesale_cost between 1 and 100 group by ss_store_sk")

            # <<--------------------------------------------

            # restore the query for the next coming query
            self.query = ""

    # deal with KeyboardInterrupt caused by ctrl+c
    def cmdloop(self, intro=None):
        print(self.intro)
        while True:
            try:
                super(ETRIMLPrompt, self).cmdloop(intro="")
                break
            except KeyboardInterrupt:
                # self.do_exit("")
                print("ETRIML closed successfully.")
                return True

    do_EOF = do_exit


if __name__ == "__main__":
    p = ETRIMLPrompt()
    p.cmdloop()
