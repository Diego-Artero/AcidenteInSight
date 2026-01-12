import os
import yaml
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from pathlib import Path
import lightgbm as lgb
from src.utils import load_config

#configuration setup
base_dir = Path(__file__).resolve().parents[2]
config_path = base_dir / "config" / "config.yaml"

config = load_config(config_path)

feature_db_path = os.path.join(base_dir, config["database"]["save_path_processed_databases"], "featured_acidentes_infosiga.db")
                               
conn = sqlite3.connect(feature_db_path)
df = pd.read_sql("SELECT * FROM sinistros", conn)
conn.close()

print(df['tipo_registro'].unique())