import yaml


class Settings:
    def __init__(self, yaml_file):
        with open(yaml_file, "r") as f:
            data = yaml.safe_load(f)
            for key, value in data.items():
                setattr(self, key, value)
