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

Refer to https://github.com/traindb-project/traindb-ml/blob/main/install-script/install_traindb-ml.sh

## Restful API service testing

1. cd server
2. python callee.py
	- 2-1. create model: 소스(caller.py)를 아래와 같이 변경 또는 python caller.py -sql "SQL create 명령 문자열" 을 통해 근사 질의 처리 ML 모델 훈련/생성
		* sql_string = "create model instacart_order_product_600k (add_to_cart_order real, reordered real) from instacart_order_product_600k.csv method uniform size 1000"
		* model 생성 완료되면, mlruns/0/ 디렉토리 아래 mlflow용 모델이 생성됨
			* 예:  ./mlruns/0/1e619001eca046c7960499c06fe365b0/
				* 여기서, 1e619001eca046c7960499c06fe365b0 --> runid 
	- 2-2. select model: 소스(caller.py)를 아래와 같이 변경 또는 python caller.py -sql "SQL select 문자열" 통해 근사 질의 처리 ML 모델 호출/추론 (아래 3단계. mlflow serving 이후 실행) 
		* sql_string = "select model avg (add_to_cart_order real) from instacart_order_product_600k where 0.9 <= reordered <= 1.0"
3. mlflow models serve -m ~/mlruns/0/{runid}/artifacts/model -h 0.0.0.0 -p 8003 –no-conda
	- example: runid가 '3b8e1398b973434e9affee956aefaffb'인 경우
	$ mlflow models serve -m ./mlruns/0/1e619001eca046c7960499c06fe365b0/artifacts/model -h 0.0.0.0 -p 8003 --no-conda
4. python caller.py 
	- SQL 문을 문자열로 전달하려면, '-sql' 옵션 후, SQL 문자열을 포함
		* python caller.py -sql "select model avg (add_to_cart_order real) from instacart_order_product_600k where 0.9 <= reordered <= 1.0"


## MLflow API deployging & serving 

1. mlflow models serve -m ./mlruns/0/{runid}/artifacts/model -h 0.0.0.0 -p 8003 --no-conda

## Java client example
- https://github.com/traindb-project/traindb-ml/blob/main/restapi-client/JavaRestClientTest.java 

## Training data path
- put .csv files for training to traindb-ml/server/etrimlwarehouse/ folder
- csv file example: https://github.com/traindb-project/traindb-ml/blob/main/server/etrimlwarehouse/instacart_order_product_600k.csv


