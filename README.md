# traindb-ml
Remote ML Model Serving Component for TrainDB

## Environment
Python 3.8 on Ubuntu 20.04

## Setting up
1. Download the codes.
```
# git clone https://github.com/traindb-project/traindb-ml.git
# cd traindb-ml
```
2. (Option) Create a virtual environment (using venv or conda).
  - For venv: (See:https://docs.python.org/3/library/venv.html)
    ```
    # python3 -m venv venv 
    # source venv/bin/activate
    (venv) #
    ```

3. Install dependencies. For example,
```
(venv) # pip install numpy pandas tables fastapi uvicorn spflow, sqlparse, psycopg2
// Here 'pip' means 'pip3', and it's the same as the following:
// (venv) # pip install -r requirements.txt
```
## Launching a REST API for devel/testing (using Fast API)
1. Execute the main.py. The default host address and port (http://0.0.0.0:8000) will be applied if no args specified.
```
(venv) # python3 main.py

 // For setting up your own address/port (e.g., http://127.0.0.1:8080):
 // (venv) # python3 main.py --rest_host 127.0.0.1 --rest_port 8080
```

2. Open a web browser and go to the address you specified.
(For default setting: http://0.0.0.0:8000/docs)

![rest-all](https://user-images.githubusercontent.com/24988105/186081280-72055d03-0a09-4bb3-b180-33613db8a0a0.png)

## Training
1. Select the '/train/{dataset}' and click 'Try it out'.
2. Input arguments and click 'execute'. 
   - dataset: name of the dataset, which will be used a prefix of the learned model name
   - csv_path: training data, which must be in the server directory
   
     (upload and remote URL are not yet supported)
   For example:

![rest-train](https://user-images.githubusercontent.com/24988105/186081940-7d956310-beb3-44ed-9a22-d45c51e3f9ee.png)

## Estimation (AQP)
1. Select the '/estimate/{dataset}' and click 'Try it out'.
2. Input arguments and click 'execute'.
   - query: an SQL statement to be approximated. e.g., SELECT COUNT(*) FROM orders
   
     (currently COUNT, SUM, AVG are supported)
     (The table name(orders) should match the csv name(orders.csv))
   - dataset: name of the dataset you learned
   - ensemble_location: location of the learned model, which must be in the server filesystem.
   
     (upload or remote URL are not supported yet)
   - show_confidence_intervals: yes/no
   
   For example:

![rest-estimate](https://user-images.githubusercontent.com/24988105/186082214-d900bff1-fe35-49df-811a-bee561a1fc72.png)

## Using KubeFlow
- See [/interface/kubeflow](https://github.com/traindb-project/traindb-ml/tree/main/interface/kubeflow)

## License
This project is dual-licensed. Apache 2.0 is for traindb-ml, and MIT is for the RSPN codes from deepdb(https://github.com/DataManagementLab/deepdb-public)

