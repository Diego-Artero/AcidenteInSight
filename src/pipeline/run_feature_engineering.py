import os
import yaml
import sqlite3
import pandas as pd
import numpy as np
from src.utils import load_config
from src.features import process_and_save_feature_dataframe_as_sql
from pathlib import Path


#configuration setup
base_dir = Path(__file__).resolve().parents[2]
config_path = base_dir / "config" / "config.yaml"

config = load_config(config_path)
base_url = config["scraping"]["base_url"]
db_path = os.path.join(base_dir, config["database"]["save_path_processed_databases"], "acidentes_infosiga.db")
feature_db_path = os.path.join(base_dir, config["database"]["save_path_processed_databases"], "featured_acidentes_infosiga.db")

conn = sqlite3.connect(db_path)

# using the stable database version: "data/databases/acidentes_infosiga.db"
df = pd.read_sql("SELECT * FROM sinistros", conn)

conn.close()

process_and_save_feature_dataframe_as_sql(feature_db_path, df, if_exists = "replace")