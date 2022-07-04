# KServe setup and testing (starting from 5 July)

- Sung-Soo Kim
- Updated: 5 July, 2022.


This page describes KServe installation and testing procedure for Kubeflow on Microk8s.
KServe is the one of the fundamental building blocks in TrainDB-ML for deploying and serving machine learning models related to approximate query processing.


## Prerequests

1. **Microk8s with Kubeflow**: you have an installed version of Kubeflow. 
  * Installation Guide: [Quick start guide to Kubeflow](https://charmed-kubeflow.io/docs/quickstart)
2. **Fundamental Concepts** of Kubeflow, Istio, KNative, KServe(or formerly KFServing)
  * You need to understand the following core concepts related to model serving in Kubeflow.
  * Since we can't delve deeply into every topic, we would like to provide you a short list of our favorite primers on Kubeflow especially serving topics.
      * [Kubeflow for Machine Learning](https://www.amazon.com/Kubeflow-Machine-Learning-Lab-Production/dp/1492050121) - Chapter 8
      * [Kubeflow Operations Guide](https://www.oreilly.com/library/view/kubeflow-operations-guide/9781492053262/) - Chapter 8 

## 0. Installing Kubeflow
We assume that you have already installed Kubeflow by using the following guide.
* Installation Guide: [Quick start guide to Kubeflow](https://charmed-kubeflow.io/docs/quickstart)


## 1. KServe Installation

KServe **Serverless installation** enables autoscaling based on request volume and supports scale down to and from zero. It also supports revision management and canary rollout based on revisions.

Kubernetes 1.20 is the minimally required version and please check the following recommended Knative, Istio versions for the corresponding Kubernetes version.

### Recommended Version Matrix

Kubernetes Version | Recommended Istio Version | Recommended Knative Version
-- | -- | --
1.20 | 1.9, 1.10, 1.11 | 0.25, 0.26, 1.0
1.21 | 1.10, 1.11 | 0.25, 0.26, 1.0
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


## 2. KServe InferenceService Testing


## Key Concepts of Model Serving and Integration for TrainDB-ML