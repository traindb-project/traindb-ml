# Learned Cardinality Estimators

- Sung-Soo Kim
- Last Updted: 28 July, 2022

## Goals
* To develop new learned AQP models

To achieve this goal, we evaluate existing methods related to cardinality estimation.


We compare both traditional and ML-enhanced methods for CardEst and show a list in the following. All of these methods are originally developed and tuned on the IMDB dataset, we took much effort to fine-tune different models for the STATS datasets.

In particular, we need to extend *data-driven* models for learned approximate query processing in TrainDB.

We'll implement various functions to handle TPC-H and Instacart datasets for AQP.

We consider the following methods as baselines for AQP evaluation using cardinality estimation.

### Traditional Methods:
  - Histogram
  - Sample
  - BayesNet
  - Wander Join/XDB
    - Paper:https://www.cse.ust.hk/~yike/sigmod16.pdf
    - Code:https://github.com/InitialDLab/XDB
  - Pessimistic Cardinality Estimator:
  	- Paper:https://waltercai.github.io/assets/pessimistic-query-optimization.pdf
  	- Code:https://github.com/waltercai/pqo-opensource

### Query-Driven Methods:
  - MSCN
    - Paper:https://arxiv.org/pdf/1809.00677.pdf
    - Code:https://github.com/andreaskipf/learnedcardinalities
  - LW-XGB & LW-NN
    - Paper:http://www.vldb.org/pvldb/vol12/p1044-dutt.pdf

### Data-Driven Methods
  - Bayescard:
    - Paper:https://arxiv.org/pdf/2012.14743.pdf
    - Code:https://github.com/wuziniu/BayesCard
  - Neurocard
    - Paper:https://arxiv.org/pdf/2006.08109.pdf
    - Code:https://github.com/neurocard/neurocard
  - UAE
    - Paper:https://dl.acm.org/doi/10.1145/3448016.3452830
  - DeepDB
    - Paper:https://arxiv.org/pdf/1909.00607.pdf
    - Code:https://github.com/DataManagementLab/deepdb-public
  - FLAT:
    - Paper:https://vldb.org/pvldb/vol14/p1489-zhu.pdf
    - Code[FSPN]:https://github.com/wuziniu/FSPN

In the case of DeepDB, first, we exploit native SPN rather than PyTorch-based SPN.

If we develop the stable AQP functionality, we'll replace the native SPN with PyTorch-based SPN.