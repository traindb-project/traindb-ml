# PyTorch Model Serving (starting from 14 July)

- Sung-Soo Kim
- Updated: 14 July, 2022.

* Related Article: [KServe setup and testing](https://github.com/traindb-project/traindb-ml/tree/main/kserve)
	* PyTorch 모델 적용

### References

* [Deploy PyTorch model with TorchServe InferenceService](https://kserve.github.io/website/master/modelserving/v1beta1/torchserve/)
* [Sample commands to create a resnet-18 eager mode model archive, register it on TorchServe and run image prediction](https://github.com/pytorch/serve/tree/master/examples/image_classifier/resnet_18)

---

This page describes major procedure for serving PyTorch models.

I summarize these procedures as the following.

0. Install Required Dependencies
1. PyTorch ML model generation (especially, pretrained resnet_18 model)
2. Model archiver file generation for torchserve
3. TorchServe configuration
4. Deploy PyTorch model with V1 REST Protocol
   * Step#1: Create the TorchServe InferenceService
   * Step#2: Model Inference
   * Step#3: Model Explanation

   
   
   

   
    	


