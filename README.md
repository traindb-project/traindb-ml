# traindb-ml

Setup
===

1. conda create -n traindb-ml python=3.7
2. conda activate traindb-ml
3. git clone https://github.com/traindb-project/traindb-ml.git
4. cd traindb-ml
5. pip install -e . 
6. pip install mlflow
7. pip install flask
8. pip install psycopg2
9. pip uninstall gensim
10. pip install gensim==3.8.3

## Restful API service testing

1. cd server
2. python callee.py
	- 2-1. create model: 소스를 아래와 같이 변경
		* sql_string = "create model instacart_order_product_600k (add_to_cart_order real, reordered real) from instacart_order_product_600k.csv method uniform size 1000"
	- 2-2. select model: 소스를 아래와 같이 변경 (아래 3단계. mlflow serving 이후 실행)
		* sql_string = "select model avg (add_to_cart_order real) from instacart_order_product_600k where 0.9 <= reordered <= 1.0"
3. mlflow models serve -m ~/mlruns/0/{runid}/artifacts/model -h 0.0.0.0 -p 8003 –no-conda
	- example: runid가 '3b8e1398b973434e9affee956aefaffb'인 경우
	$ mlflow models serve -m ./mlruns/0/1e619001eca046c7960499c06fe365b0/artifacts/model -h 0.0.0.0 -p 8003 --no-conda
4. python caller.py 


## MLflow API deployging & serving 

1. mlflow models serve -m ./mlruns/0/{runid}/artifacts/model -h 0.0.0.0 -p 8003 --no-conda