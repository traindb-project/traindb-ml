
class ETRIMLModelCatalog:
    def __init__(self):
        #print(">>> catalog > catalog.py > ETRIMLModelCatalog : __init__()")
        self.model_catalog = {}

    def add_model_wrapper(self, model_wrapper, runtime_config):
        #print(">>> catalog > catalog.py > ETRIMLModelCatalog : add_model_wrapper()")

        if hasattr(model_wrapper, 'groupby_value'):        # using regression and kde
            if model_wrapper.groupby_value is None:
                self.model_catalog[model_wrapper.init_pickle_file_name(runtime_config
                                                                       )] = model_wrapper
            else:
                self.model_catalog[model_wrapper.dir] = model_wrapper.models
        else:  # using kde
            self.model_catalog[model_wrapper.init_pickle_file_name(runtime_config)
                               ] = model_wrapper
