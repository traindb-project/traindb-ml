from kubernetes import client,config,utils

def main():
    config.load_kube_config()
    k8s_client = client.ApiClient()
    yaml_file = 'examples/configmap-demo-pod.yml'
    utils.create_from_yaml(k8s_client,yaml_file,verbose=True)

if __name__ == "__main__":
    main()
