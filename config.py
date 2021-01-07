import os
import yaml


try:
    with open("config.yaml") as f:
        config = yaml.load(f, Loader=yaml.Loader)
except FileNotFoundError:
    config = {}

config.update(os.environ)

