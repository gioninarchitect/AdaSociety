class Config(dict):
    #__getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __getattr__(self, key):
        value = self.get(key, {})
        return Config(value) if isinstance(value, dict) else value
