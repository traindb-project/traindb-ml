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

## Summary

I summarize these procedures for serving PyTorch models as the following.

0. Install Required Dependencies
1. PyTorch ML model generation (especially, pretrained resnet_18 model)
2. Model archiver file generation for torchserve
3. TorchServe configuration
4. Deploy PyTorch model with V1 REST Protocol
   * Step#1: Create the TorchServe InferenceService
   * Step#2: Model Inference
   * Step#3: Model Explanation

## Results
### Input image

This is the input image for image classification model (resnet model).

![](kitten.jpg)

This is the result of resnet model inference call. (object name with confidence rate)

```sh
(pytorch) ╭─sungsoo@z840 ~/test/torchserve-exercise
╰─$ call_model.sh
{
  "tabby": 0.4086446464061737,
  "tiger_cat": 0.35061565041542053,
  "Egyptian_cat": 0.12609602510929108,
  "lynx": 0.02332688681781292,
  "bucket": 0.011855168268084526
}
```


## 0. Install Required Dependencies

I use conda for installing the required Python packages.

Create your virtual environment with Python >= 3.8.

```sh
(base) ╭─sungsoo@lavender ~/github/traindb-ml/kserve/torchserve ‹main●›
╰─$ conda create -n torchserve python=3.8

(base) ╭─sungsoo@lavender ~/github/traindb-ml/kserve/torchserve ‹main●›
╰─$ conda activate torchserve
```

Install PyTorch according to your OS.

```sh
(torchserve) ╭─sungsoo@lavender ~/github/traindb-ml/kserve/torchserve ‹main●›
╰─$ conda install pytorch torchvision torchaudio -c pytorch
```

Torchserve requires Java JDK 11 while deploying

```bash
sudo apt install --no-install-recommends -y openjdk-11-jre-headless
```

Install torch-model-archiver and torchserve.

```sh
pip install torch-model-archiver torchserve  
```

Install Captum (Model Interpretability for PyTorch).

```sh
pip install captum
```


## 1. PyTorch ML model generation

We use the pretrained model of ResNet by executing the Python file (get_pretrained_model.py).

```sh
(torchserve) ╭─sungsoo@lavender ~/github/traindb-ml/kserve/torchserve ‹main●›
╰─$ python get_pretrained_model.py
```
[Alternative] If you perfom and finish a training phase, save the model file via PyTorch model save function.
Then you use that model. 


## 2. Model archiver file generation for torchserve

Then execute the generate_mar.sh script file.

```sh
(torchserve) ╭─sungsoo@lavender ~/github/traindb-ml/kserve/torchserve ‹main●›
╰─$ generate_mar.sh
```

Execute the serve_model.sh script file to serve the model using the archiver file.

```sh
(torchserve) ╭─sungsoo@lavender ~/github/traindb-ml/kserve/torchserve ‹main›
╰─$ serve_model.sh
```

To perform inference call testing, you can use the call_model.sh script file.

```sh
(torchserve) ╭─sungsoo@lavender ~/github/traindb-ml/kserve/torchserve ‹main›
╰─$ call_model.sh
{
  "tabby": 0.4086446464061737,
  "tiger_cat": 0.35061565041542053,
  "Egyptian_cat": 0.12609602510929108,
  "lynx": 0.02332688681781292,
  "bucket": 0.011855168268084526
}%
```



   
    	


