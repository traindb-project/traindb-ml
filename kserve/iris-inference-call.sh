#!/usr/bin/zsh


SERVICE_HOSTNAME=$(microk8s.kubectl get inferenceservice sklearn-iris -n kserve-test -o jsonpath='{.status.url}' | cut -d "/" -f 3)
curl -v -H "Host: ${SERVICE_HOSTNAME}" \
http://localhost:8080/v1/models/sklearn-iris:predict \
-d '{ "instances": [[6.8,  2.8,  4.8,  1.4],[6.0,  3.4,  4.5,  1.6]]}'
