import logging.config
import os

import ruamel.yaml as yaml


def init():
    default_path = os.path.join(os.path.dirname(__file__), 'default_logging_config.yaml')
    path = os.getenv('LOG_CFG', default_path)
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
