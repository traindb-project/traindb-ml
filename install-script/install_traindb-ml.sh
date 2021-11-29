#!/bin/bash

echo "traindb-ml setup...."

conda create -n traindb-ml python=3.7
conda activate traindb-ml
git clone https://github.com/traindb-project/traindb-ml.git
cd traindb-ml
pip install -e .
pip install mlflow
pip install flask
pip install psycopg2
pip uninstall gensim
pip install gensim==3.8.3


