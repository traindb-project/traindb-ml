# KServe setup and testing (starting from 5 July)

- Sung-Soo Kim
- Updated: 5 July, 2022.


This page describes KServe installation and testing procedure for Kubeflow on Microk8s.

If you're acquainted with Kubeflow, you're probably familiar with KFServing, the platform's model server, and inference engine. The KFServing project was renamed KServe in September 2021.

KServe is the one of the fundamental building blocks in TrainDB-ML for deploying and serving machine learning models related to approximate query processing.


## Requirements

1. **Microk8s with Kubeflow**: you have an installed version of Kubeflow. 
  * Installation Guide: [Quick start guide to Kubeflow](https://charmed-kubeflow.io/docs/quickstart)
2. **Fundamental Concepts** of Kubeflow, Istio, KNative, and KServe(or formerly KFServing)
  * You need to understand the following core concepts related to model serving in Kubeflow.
  * Since we can't delve deeply into every topic, we would like to provide you a short list of our favorite primers on Kubeflow especially serving topics.
      * [Kubeflow for Machine Learning](https://www.amazon.com/Kubeflow-Machine-Learning-Lab-Production/dp/1492050121) - Chapter 8
      * [Kubeflow Operations Guide](https://www.oreilly.com/library/view/kubeflow-operations-guide/9781492053262/) - Chapter 8 

## 0. Installing Kubeflow
We assume that you have already installed Kubeflow by using the following guide.
* Installation Guide: [Quick start guide to Kubeflow](https://charmed-kubeflow.io/docs/quickstart)

You can check the installation status using the following commands ('microk8s inspect').

```sh
(base) ╭─sungsoo@z840 ~
╰─$ microk8s inspect
[sudo] password for sungsoo:
Inspecting Certificates
Inspecting services
  Service snap.microk8s.daemon-cluster-agent is running
  Service snap.microk8s.daemon-containerd is running
  Service snap.microk8s.daemon-apiserver-kicker is running
  Service snap.microk8s.daemon-kubelite is running
  Copy service arguments to the final report tarball
Inspecting AppArmor configuration
Gathering system information
  Copy processes list to the final report tarball
  Copy snap list to the final report tarball
  Copy VM name (or none) to the final report tarball
  Copy disk usage information to the final report tarball
  Copy memory usage information to the final report tarball
  Copy server uptime to the final report tarball
  Copy current linux distribution to the final report tarball
  Copy openSSL information to the final report tarball
  Copy network configuration to the final report tarball
Inspecting kubernetes cluster
  Inspect kubernetes cluster
Inspecting juju
  Inspect Juju
Inspecting kubeflow
  Inspect Kubeflow
```


## 1. KServe Installation

KServe **Serverless installation** enables autoscaling based on request volume and supports scale down to and from zero. It also supports revision management and canary rollout based on revisions.

Kubernetes 1.20 is the minimally required version and please check the following recommended Knative, Istio versions for the corresponding Kubernetes version.

KServe exploits the major components, as shown in the following diagram.

![Kserve architecture diagram](https://cdn.thenewstack.io/media/2022/02/d0a028b8-kserve-1024x515.jpg)

### Recommended Version Matrix

Kubernetes Version | Recommended Istio Version | Recommended Knative Version
-- | -- | --
1.20 | 1.9, 1.10, 1.11 | 0.25, 0.26, 1.0
**1.21** | 1.10, **1.11** | 0.25, 0.26, **1.0**
1.22 | 1.11, 1.12 | 0.25, 0.26, 1.0

### Major Components Installation

1. [Install Istio](https://kserve.github.io/website/master/admin/serverless/#1-install-istio)

Please refer to the [Istio install guide](https://knative.dev/docs/admin/install/installing-istio).

2. [Install Knative Serving](https://kserve.github.io/website/master/admin/serverless/#2-install-knative-serving)

Please refer to [Knative Serving install guide](https://knative.dev/docs/admin/install/serving/install-serving-with-yaml/).

**Note**  If you are looking to use PodSpec fields such as nodeSelector, affinity or tolerations which are now supported in the v1beta1 API spec, you need to turn on the corresponding [feature flags](https://knative.dev/docs/admin/serving/feature-flags) in your Knative configuration.

3. [Install Cert Manager](https://kserve.github.io/website/master/admin/serverless/#3-install-cert-manager)

The minimally required Cert Manager version is 1.3.0 and you can refer to [Cert Manager](https://cert-manager.io/docs/installation/).

**Note** Cert manager is required to provision webhook certs for production grade installation, alternatively you can run self signed certs generation script.

4. [Install KServe](https://kserve.github.io/website/master/admin/serverless/#4-install-kserve)

```sh
kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.8.0/kserve.yaml
```

5. [Install KServe Built-in ClusterServingRuntimes](https://kserve.github.io/website/master/admin/serverless/#5-install-kserve-built-in-clusterservingruntimes)

```sh
kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.8.0/kserve-runtimes.yaml
```
**Note**  ClusterServingRuntimes are required to create InferenceService for built-in model serving runtimes with KServe v0.8.0 or higher.

### Practice : Components Installation

I performed the KServe installation as the following versions in the recommended version matrix.

```sh
export ISTIO_VERSION=1.11.0
export KNATIVE_VERSION=knative-v1.0.0
export KSERVE_VERSION=v0.8.0
export CERT_MANAGER_VERSION=v1.3.0
```
#### 1. Install Istio

To install Istio without *sidecar injection*:

```sh
istioctl install -y
```

```sh
(base) ╭─sungsoo@z840 ~/kubeflow/istio-1.11.0
╰─$ bin/istoctl install
zsh: no such file or directory: bin/istoctl
(base) ╭─sungsoo@z840 ~/kubeflow/istio-1.11.0
╰─$ bin/istioctl install                                                                                                                                        127 ↵
This will install the Istio 1.11.0 default profile with ["Istio core" "Istiod" "Ingress gateways"] components into the cluster. Proceed? (y/N) y
✔ Istio core installed
✔ Istiod installed
✔ Ingress gateways installed
✔ Installation complete
Thank you for installing Istio 1.11.  Please take a few minutes to tell us about your install/upgrade experience!  https://forms.gle/kWULBRjUv7hHci7T6
```
istio 관련 pod가 제대로 실행되었는지 확인한다.

```sh
(base) ╭─sungsoo@z840 ~
╰─$ k get pods -A -w
istio-system                    istiod-75d5bf4676-tvztm                            1/1     Running   0          28s
istio-system                    istio-ingressgateway-85fbdd86f7-pl2lc              1/1     Running   0          23
```

#### 2. Install Knative Serving

Knative is a serverless solution built on Kubernetes that is open source and managed by Google. Therefore, it is not tied to any cloud service and may be deployed locally if necessary.

####  Install Knative

이제 Knative를 설치해 보자.

아래 명령어을 통해, Knative 버전 1.0을 설치한다.

```sh
kubectl apply --filename https://github.com/knative/serving/releases/download/knative-v1.0.0/serving-crds.yaml
kubectl apply --filename https://github.com/knative/serving/releases/download/knative-v1.0.0/serving-core.yaml
kubectl apply --filename https://github.com/knative/net-istio/releases/download/knative-v1.0.0/release.yaml
```

#### 3. Install Cert Manager

```sh
kubectl apply --validate=false -f https://github.com/jetstack/cert-manager/releases/download/v1.3.0/cert-manager.yaml
kubectl wait --for=condition=available --timeout=600s deployment/cert-manager-webhook -n cert-manager
```

#### 4. Install KServe

```sh
kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.8.0/kserve.yaml
kubectl wait --for=condition=ready pod -l control-plane=kserve-controller-manager -n kserve --timeout=300s
```

#### 5. Install KServe built-in servingruntimes

```sh
kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.8.0/kserve-runtimes.yaml
```

#### 6. 설치 상태 확인

앞의 모든 내용을 실행 후, 설치가 제대로 되어있는지 POD 상태를 확인한다.

```sh
(base) ╭─sungsoo@z840 ~
╰─$ k get pods -A -w                  
NAMESPACE                       NAME                                               READY   STATUS    RESTARTS   AGE
kube-system                     calico-kube-controllers-f7868dd95-5qvc5            1/1     Running   0          22h
kube-system                     coredns-7f9c69c78c-sjtf5                           1/1     Running   0          22h
kube-system                     calico-node-d72j4                                  1/1     Running   0          22h

... 중간 생략

traindb-ml                      ml-pipeline-visualizationserver-569ccd5d86-jcmvn   1/1     Running   0          20h
traindb-ml                      ml-pipeline-ui-artifact-77dfb58d8b-lf8rt           1/1     Running   0          20h
istio-system                    istiod-75d5bf4676-tvztm                            1/1     Running   0          10m
istio-system                    istio-ingressgateway-85fbdd86f7-pl2lc              1/1     Running   0          9m55s
knative-serving                 autoscaler-6c8884d6ff-k9rkf                        1/1     Running   0          5m7s
knative-serving                 activator-68b7698d74-cn24l                         1/1     Running   0          5m8s
knative-serving                 controller-76cf997d95-95xmz                        1/1     Running   0          5m7s
knative-serving                 domain-mapping-57fdbf97b-j6sqf                     1/1     Running   0          5m6s
knative-serving                 domainmapping-webhook-66c5f7d596-h9qzf             1/1     Running   0          5m6s
knative-serving                 webhook-7df8fd847b-2wskb                           1/1     Running   0          5m5s
knative-serving                 net-istio-controller-544874485d-8n5xz              1/1     Running   0          2m58s
knative-serving                 net-istio-webhook-695d588d65-wq7mp                 1/1     Running   0          2m58s
cert-manager                    cert-manager-cainjector-655d695d74-czptn           1/1     Running   0          2m19s
cert-manager                    cert-manager-76b7c557d5-b8hl2                      1/1     Running   0          2m18s
cert-manager                    cert-manager-webhook-7955b9bb97-7pv7v              1/1     Running   0          2m18s
kserve                          kserve-controller-manager-0                        2/2     Running   0          72s
```
설치했던 모든 POD가 정상적으로 시작 (READY) 되었으면 성공이다!

Kserve가 어떻게 실행되었는지 세부내용을 있는지 확인해 보자.

```sh
(base) ╭─sungsoo@z840 ~
╰─$ k describe pod kserve-controller-manager-0 -n kserve
Name:         kserve-controller-manager-0
Namespace:    kserve
Priority:     0
Node:         z840/129.254.187.182
Start Time:   Thu, 07 Jul 2022 06:39:14 +0900
Labels:       control-plane=kserve-controller-manager

... 중간 생략

Events:
  Type     Reason       Age                    From               Message
  ----     ------       ----                   ----               -------
  Normal   Scheduled    4m36s                  default-scheduler  Successfully assigned kserve/kserve-controller-manager-0 to z840
  Warning  FailedMount  4m36s (x2 over 4m36s)  kubelet            MountVolume.SetUp failed for volume "cert" : secret "kserve-webhook-server-cert" not found
  Normal   Pulling      4m33s                  kubelet            Pulling image "kserve/kserve-controller:v0.8.0"
  Normal   Pulled       4m26s                  kubelet            Successfully pulled image "kserve/kserve-controller:v0.8.0" in 7.872368634s
  Normal   Created      4m25s                  kubelet            Created container manager
  Normal   Started      4m25s                  kubelet            Started container manager
  Normal   Pulling      4m25s                  kubelet            Pulling image "gcr.io/kubebuilder/kube-rbac-proxy:v0.8.0"
  Normal   Pulled       4m19s                  kubelet            Successfully pulled image "gcr.io/kubebuilder/kube-rbac-proxy:v0.8.0" in 5.875500128s
  Normal   Created      4m19s                  kubelet            Created container kube-rbac-proxy
  Normal   Started      4m19s                  kubelet            Started container kube-rbac-proxy
```


## 2. KServe InferenceService Testing

* Article Source: [First InferenceService](https://kserve.github.io/website/get_started/first_isvc/)

### Run your first InferenceService

In this tutorial, you will deploy a ScikitLearn InferenceService.

This inference service loads a simple iris ML model, send a list of attributes and print the prediction for the class of iris plant."

Since your model is being deployed as an InferenceService, not a raw Kubernetes Service, you just need to provide the trained model and it gets some super powers out of the box 🚀.

**1. Create test InferenceService**

```YAML
apiVersion: "serving.kserve.io/v1beta1"
kind: "InferenceService"
metadata:
  name: "sklearn-iris"
spec:
  predictor:
    sklearn:
      storageUri: "gs://kfserving-samples/models/sklearn/iris"
```

Once you've created your YAML file (named something like "sklearn.yaml"):

```sh
kubectl create namespace kserve-test
kubectl apply -f sklearn.yaml -n kserve-test
```

You can verify the deployment of this inference service as follows.
```
(base) ╭─sungsoo@z840 ~
╰─$ k get pods -A -w
NAMESPACE                       NAME                                               READY   STATUS    RESTARTS   AGE
...중간 생략
kserve-test                     sklearn-iris-predictor-default-00001-deployment-7958c8bfddv68k9   0/2     Pending   0          2s
kserve-test                     sklearn-iris-predictor-default-00001-deployment-7958c8bfddv68k9   0/2     Pending   0          3s
kserve-test                     sklearn-iris-predictor-default-00001-deployment-7958c8bfddv68k9   0/2     Init:0/1   0          3s
kserve-test                     sklearn-iris-predictor-default-00001-deployment-7958c8bfddv68k9   0/2     Init:0/1   0          8s
kserve-test                     sklearn-iris-predictor-default-00001-deployment-7958c8bfddv68k9   0/2     Init:0/1   0          41s
kserve-test                     sklearn-iris-predictor-default-00001-deployment-7958c8bfddv68k9   0/2     PodInitializing   0          51s
kserve-test                     sklearn-iris-predictor-default-00001-deployment-7958c8bfddv68k9   1/2     Running           0          97s
kserve-test                     sklearn-iris-predictor-default-00001-deployment-7958c8bfddv68k9   2/2     Running           0          98s
```

**2. Check InferenceService status.**

```sh
kubectl get inferenceservices sklearn-iris -n kserve-test
NAME           URL                                                 READY   PREV   LATEST   PREVROLLEDOUTREVISION   LATESTREADYREVISION                    AGE
sklearn-iris   http://sklearn-iris.kserve-test.example.com         True           100                              sklearn-iris-predictor-default-47q2g   7d23h
```

If your DNS contains example.com please consult your admin for configuring DNS or using [custom domain](https://knative.dev/docs/serving/using-a-custom-domain).

**3. Determine the ingress IP and ports**

Execute the following command to determine if your kubernetes cluster is running in an environment that supports external load balancers

```sh
(base) ╭─sungsoo@z840 ~
╰─$ kubectl get svc istio-ingressgateway -n istio-system
NAME                   TYPE           CLUSTER-IP       EXTERNAL-IP    PORT(S)                                      AGE
istio-ingressgateway   LoadBalancer   10.152.183.253   10.64.140.44   15021:30083/TCP,80:30621/TCP,443:31180/TCP   97m
```
or @microk8s with kubeflow

```sh
(base) ╭─sungsoo@z840 ~
╰─$ kubectl get svc istio-ingressgateway -n kubeflow
NAME                   TYPE           CLUSTER-IP       EXTERNAL-IP    PORT(S)                                                                                                                                                                   AGE
istio-ingressgateway   LoadBalancer   10.152.183.189   10.64.140.43   15020:30524/TCP,80:32346/TCP,443:30625/TCP,15029:32677/TCP,15030:31221/TCP,15031:30365/TCP,15032:32761/TCP,15443:30695/TCP,15011:32155/TCP,8060:30589/TCP,853:31558/TCP   23h
```

#### Load Balancer
If the EXTERNAL-IP value is set, your environment has an external load balancer that you can use for the ingress gateway.

```sh
export INGRESS_HOST=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
export INGRESS_PORT=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http2")].port}')
```

or @microk8s with kubeflow

```sh
export INGRESS_HOST=$(kubectl -n kubeflow get service istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
export INGRESS_PORT=$(kubectl -n kubeflow get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http2")].port}')
```


#### Node Port
If the EXTERNAL-IP value is none (or perpetually pending), your environment does not provide an external load balancer for the ingress gateway. In this case, you can access the gateway using the service’s node port.

```sh
# GKE
export INGRESS_HOST=worker-node-address
# Minikube
export INGRESS_HOST=$(minikube ip)
# Other environment(On Prem)
export INGRESS_HOST=$(kubectl get po -l istio=ingressgateway -n istio-system -o jsonpath='{.items[0].status.hostIP}')
export INGRESS_PORT=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http2")].nodePort}')
```

#### Port Forward
Alternatively you can do Port Forward for testing purpose

```sh
INGRESS_GATEWAY_SERVICE=$(kubectl get svc --namespace istio-system --selector="app=istio-ingressgateway" --output jsonpath='{.items[0].metadata.name}')
kubectl port-forward --namespace istio-system svc/${INGRESS_GATEWAY_SERVICE} 8080:80
# start another terminal
export INGRESS_HOST=localhost
export INGRESS_PORT=8080
```

## Key Concepts of Model Serving and Integration for TrainDB-ML