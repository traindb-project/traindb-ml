# traindb-ml
Remote ML Model Serving Component for TrainDB

## Environment
Python 3.8 on Ubuntu 20.04

## Setting up
```
# git clone https://github.com/traindb-project/traindb-ml.git

# cd traindb-ml
// create venv or conda
(venv) #

// install dependencies. (pip == pip3) For example,
(venv) # pip install numpy pandas tables fastapi uvicorn spflow, sqlparse, psycopg2

// which is the same as the following:
//(venv) # pip install -r requirements.txt
```
## Start
```
(venv) # python3 main.py --csv_path your_dir/orders.csv
```

## For KubeFlow
- See [/interface/kubeflow](https://github.com/traindb-project/traindb-ml/tree/main/interface/kubeflow)

## License
This project is dual-licensed. Apache 2.0 is for traindb-ml, and MIT is for the RSPN codes from deepdb(https://github.com/DataManagementLab/deepdb-public)
