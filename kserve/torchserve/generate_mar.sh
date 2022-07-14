#!/usr/bin/zsh

torch-model-archiver --model-name resnet-18 --version 1.0 --model-file ./model.py --serialized-file resnet-18.pt --handler image_classifier --extra-files ./index_to_name.json

