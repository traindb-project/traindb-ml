# PyTorchJobClient SDK for Model Training (Not started yet)

- Sung-Soo Kim
- Updated: 14 July, 2022.

* Related Article: [KServe setup and testing](https://github.com/traindb-project/traindb-ml/tree/main/kserve)
	* PyTorch 모델 적용

### References

* [PyTorchJobClient](https://github.com/kubeflow/pytorch-operator/blob/master/sdk/python/docs/PyTorchJobClient.md)
* [Sample for Kubeflow PyTorchJob SDK](https://notebook.community/kubeflow/pytorch-operator/sdk/python/examples/kubeflow-pytorchjob-sdk)

---

This page describes the method for PyTorch ML model training using Python SDK (PyTorchJobClient).

PyTorchJob is a Kubernetes custom resource to run PyTorch training jobs on Kubernetes. The Kubeflow implementation of PyTorchJob is in training-operator.

## Summary

I summarize these procedures for training models using PyTorchJobClient SDK as the following.

0. Install Required Dependencies
1. Defining a PyTorchJob
2. Creating a PyTorchJob
3. Checking the PyTorchJob Status
4. [Optional] Deleting the PyTorchJob






   
   
   

   
    	


