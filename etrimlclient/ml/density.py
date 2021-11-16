

import numpy as np
from sklearn.neighbors import KernelDensity

from etrimlclient.ml.mdn import KdeMdn


class ETRIMLDensity:
    def __init__(self, config, kernel=None):
        #print(">>> ml > density.py > ETRIMLDensity : __init__()")

        if kernel is None:
            self.kernel = "gaussian"
        self.kde = None
        self.config = config

    def fit(self, x, groupby_attribute, runtime_config):
        #print(">>> ml > density.py > ETRIMLDensity : fit()")

        density_type = self.config.config["density_type"]

        if density_type == "kde":
            self.kde = KernelDensity(kernel=self.kernel).fit(x)
        elif density_type == "mdn":
            # print("x", x, type(x))
            groups = np.zeros(x.shape)
            # print("groups", groups)
            x = x.reshape(1, -1)[0]
            # print("x", x)
            self.kde = KdeMdn(self.config).fit(groups, x, runtime_config)
        else:
            raise Exception("unexpected density_type.")
        return self.kde
