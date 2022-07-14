#!/usr/bin/zsh

torchserve --start --model-store model_store --models resnet-18=resnet-18.mar
