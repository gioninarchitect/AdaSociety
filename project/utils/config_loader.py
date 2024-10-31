import json
import os.path

from .config import Config


class ConfigLoader:
    def __init__(
        self,
        main_config_path='./config/main.json',
        default_config_dir='',
    ):
        self.config = Config()
        self.config['main'] = self.load_config(main_config_path)
        for k, v in self.config['main'].items():
            if k == '__COMMENT__':
                continue
            print(v)
            if os.path.isfile(v):
                self.config[k] = self.load_config(v)
            else:
                import warnings
                warnings.warn(f'Config[{k}]: `{v}` does not exist!')

    @property
    def task(self):
        return self.config['task']

    @property
    def render(self):
        return self.config['render']

    def load_config(self, config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
