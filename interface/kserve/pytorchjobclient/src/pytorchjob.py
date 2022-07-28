#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Test code for TrainDB-ML initial developement

from kubernetes.client import V1PodTemplateSpec
from kubernetes.client import V1ObjectMeta
from kubernetes.client import V1PodSpec
from kubernetes.client import V1Container
from kubernetes.client import V1ResourceRequirements

from kubeflow.training import constants
from kubeflow.training import utils
from kubeflow.training import V1ReplicaSpec
# from kubeflow.training import KubeflowOrgV1PyTorchJob
# from kubeflow.training import KubeflowOrgV1PyTorchJobSpec
from kubeflow.training import V1PyTorchJob
from kubeflow.training import V1PyTorchJobSpec
from kubeflow.training import PyTorchJobClient


container = V1Container(
name="pytorch",
image="gcr.io/kubeflow-ci/pytorch-dist-mnist-test:v1.0",
args=["--backend","gloo"],
)

print('# Container: ', container)

master = V1ReplicaSpec(
replicas=1,
restart_policy="OnFailure",
template=V1PodTemplateSpec(
    spec=V1PodSpec(
    containers=[container]
    )
)
)

print('# Master: ', master)


worker = V1ReplicaSpec(
replicas=1,
restart_policy="OnFailure",
template=V1PodTemplateSpec(
    spec=V1PodSpec(
    containers=[container]
    )
)
)

print('# Worker: ', worker)


pytorchjob = V1PyTorchJob(
api_version="kubeflow.org/v1",
kind="PyTorchJob",
metadata=V1ObjectMeta(name="mnist", namespace='traindb-ml'),
spec=V1PyTorchJobSpec(
    run_policy="None",
    pytorch_replica_specs={"Master": master,
                            "Worker": worker}
)
)

print('# PyTorchJob: ', pytorchjob)

pytorchjob_client = PyTorchJobClient()
pytorchjob_client.create(pytorchjob)
# pytorchjob_client.get('mnist', namespace='kubeflow')