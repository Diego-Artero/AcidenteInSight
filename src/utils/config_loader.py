import yaml

def load_config(CONFIG_PATH):
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)