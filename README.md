# traindb-ml
Remote ML Model Serving Component for TrainDB

## Setting up
```
git clone https://github.com/traindb-project/traindb-ml.git
cd traindb-ml
(create venv or conda)
pip install numpy pandas fastapi
```
## Start
```
python3 setup.py --csv_path your_dir/orders.csv
```

## For KubeFlow
- See /interface/kubeflow
