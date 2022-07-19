from kubernetes import client,config,utils

## 이 파일을 호출하는 코드는 TrainDB-Java다.
## Final goal: 이 파일을 코딩하는 것

def show_models():
    models_info = None
    # kubeflow kserve model 관리하는 부분을 참고하여 구현해 보자.

    return models_info
##############

def show_model(model_name):
    model_detail_info = None
    # kubeflow kserve model 관리하는 부분을 참고하여 구현해 보자.

    return model_detail_info
##############

class DataSource:
    # DBMS_type
    engine='mysql',
    parameters={
        "user":"root",
        "port": 3306,
        "password": "Mimzo3i-mxt@9CpThpBj",
        "host": "127.0.0.1",
        "database": "instacart",
        "table": "order_product",
    }

def training(model_type, model_name, data_source, hyperparams='hyperparams.json', ....):
    # training operator (TFJob, PyTorchJob,....) 관리하는 부분을 참고하여 구현해 보자.
    # PyTorchJob SDK를 활용해 보자.
    # 가정: 이미지는 사전에 준비되어 있다. 

    pass

def serving(model_name, query_input='query_input.json'):
    # Query Input: 추후 상세 정의 필요함

    pass

def retraining(model_name, data_source, hyperparams='hyperparams.json', .... ):
    # Model 버전관리에 내용은 향후 정리 필요함

    pass

def delete_model(model_name):
    pass


def main():

    # argParse를 이용해서, operation_type 전달 받고, 각종 json file 처리 필요함
    
    config.load_kube_config()
    k8s_client = client.ApiClient()
    
    operation_type = 'show_model'
    switch (operation_type):
    ....__annotations__


if __name__ == "__main__":
    main()