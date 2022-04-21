
from qregpy import qreg

from etrimlclient.ml import mdn


class ETRIMLReg:
    def __init__(self, config):
        #print(">>> ml > regression.py > ETRIMLReg : __init__()")

        self.reg = None
        self.config = config

    def fit(self, x, y, runtime_config):
        #print(">>> ml > regression.py > ETRIMLReg : fit()")

        reg_type = self.config.config["reg_type"]

        if reg_type == 'qreg':
            self.reg = qreg.QReg(
                base_models=["linear", "polynomial"], verbose=False).fit(x, y)
        if reg_type == 'mdn':
            self.reg = mdn.RegMdn(self.config, dim_input=1).fit(
                x, y, runtime_config)
        return self.reg
