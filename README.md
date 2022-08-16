# traindb-ml
Remote ML Model Serving Component for TrainDB

## Setting up
```
git clone https://github.com/traindb-project/traindb-ml.git
cd traindb-ml
(create venv or conda)
# install dependencies. for example,
pip install numpy pandas fastapi uvicorn
```
## Start
```
python3 setup.py --csv_path your_dir/orders.csv
```

## For KubeFlow
- See /interface/kubeflow

## License
This project is dual-licensed. Apache 2.0 is for traindb-ml, and MIT is for the RSPN codes from deepdb(https://github.com/DataManagementLab/deepdb-public)
