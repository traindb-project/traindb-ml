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

# Test code for TrainDB-ML development

import argparse
import os
import subprocess
import time
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import datasets
from torchvision import transforms

class Net(nn.Module):

    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 10, kernel_size=5)
        self.conv2 = nn.Conv2d(10, 20, kernel_size=5)
        self.conv2_drop = nn.Dropout2d()
        self.fc1 = nn.Linear(320, 50)
        self.fc2 = nn.Linear(50, 10)

    def forward(self, x):
        x = F.relu(F.max_pool2d(self.conv1(x), 2))
        x = F.relu(F.max_pool2d(self.conv2_drop(self.conv2(x)), 2))
        x = x.view(-1, 320)
        x = F.relu(self.fc1(x))
        x = F.dropout(x, training=self.training)
        x = self.fc2(x)
        return F.log_softmax(x, dim=1)


def train(model, device, train_loader, optimizer, epoch, log_interval):
    model.train()
    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.to(device), target.to(device)
        optimizer.zero_grad()
        output = model(data)
        loss = F.nll_loss(output, target)
        loss.backward()
        optimizer.step()
        if batch_idx % log_interval == 0 and batch_idx>0:
            print('Train Epoch: {}\t[{}/{}\t({:.0f}%)]\tLoss: {:.6f}'.format(
              epoch, batch_idx * len(data), len(train_loader.dataset),
              100. * batch_idx / len(train_loader), loss.item()))


def test(model, device, test_loader, epoch):
    model.eval()
    test_loss = 0
    correct = 0
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            test_loss += F.nll_loss(
              output, target, size_average=False).item()  # sum up batch loss
            pred = output.max(
              1, keepdim=True)[1]  # get the index of the max log-probability
            correct += pred.eq(target.view_as(pred)).sum().item()

        test_loss /= len(test_loader.dataset)
        print('\nTest set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
          test_loss, correct, len(test_loader.dataset),
          100. * correct / len(test_loader.dataset)))


def train_and_test(batch_size=64, epochs=1, log_interval=100, lr=0.01, model_dir=None, momentum=0.5, 
                       no_cuda=False, seed=1, test_batch_size=1000):

    use_cuda = not no_cuda and torch.cuda.is_available()
    torch.manual_seed(seed)
    device = torch.device('cuda' if use_cuda else 'cpu')
    print("Using {} for training.".format(device))

    kwargs = {'num_workers': 1, 'pin_memory': True} if use_cuda else {}
    train_loader = torch.utils.data.DataLoader(
      datasets.MNIST(
          'data',
          train=True,
          download=True,
          transform=transforms.Compose([
              transforms.ToTensor(),
              # Normalize a tensor image with mean and standard deviation
              transforms.Normalize(mean=(0.1307,), std=(0.3081,))
          ])),
      batch_size=batch_size,
      shuffle=True,
      **kwargs)
    test_loader = torch.utils.data.DataLoader(
      datasets.MNIST(
          'data',
          train=False,
          transform=transforms.Compose([
              transforms.ToTensor(),
              # Normalize a tensor image with mean and standard deviation              
              transforms.Normalize(mean=(0.1307,), std=(0.3081,))
          ])),
      batch_size=test_batch_size,
      shuffle=True,
      **kwargs)

    model = Net().to(device)
    optimizer = optim.SGD(model.parameters(), lr=lr, momentum=momentum)

    for epoch in range(1, epochs + 1):
        start_time = time.time()
        train(model, device, train_loader, optimizer, epoch, log_interval)
        print("Time taken for epoch #{}: {:.2f}s".format(epoch, time.time()-start_time))
        test(model, device, test_loader, epoch)

    if model_dir:
        model_file_name = 'torch.model'
        tmp_model_file = os.path.join('/tmp', model_file_name)
        torch.save(model.state_dict(), tmp_model_file)
        subprocess.check_call([
            'gsutil', 'cp', tmp_model_file,
            os.path.join(model_dir, model_file_name)])


if __name__ == '__main__':
    # training locally
    train_and_test()