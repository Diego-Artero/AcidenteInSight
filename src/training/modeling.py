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
from sklearn.metrics import classification_report, confusion_matrix, f1_score, precision_recall_curve
from pathlib import Path
import lightgbm as lgb
from src.utils import load_config
from src.features import apply_feature_schema

#configuration setup
base_dir = Path(__file__).resolve().parents[2]
config_path = base_dir / "config" / "config.yaml"

config = load_config(config_path)


feature_db_path = os.path.join(base_dir, config["database"]["save_path_processed_databases"], "featured_acidentes_infosiga.db")
                               
conn = sqlite3.connect(feature_db_path)
df = pd.read_sql("SELECT * FROM sinistros", conn)
conn.close()
df = apply_feature_schema(df)

TARGET = "tipo_registro"

X = df.drop(columns=[TARGET])
y = df[TARGET]
print(X.dtypes)
print(X)
categorical_features = [
    col for col in X.columns
    if X[col].dtype.name == "category"
]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


train_data = lgb.Dataset(
    X_train,
    label=y_train,
    categorical_feature=categorical_features,
    free_raw_data=False
)

test_data = lgb.Dataset(
    X_test,
    label=y_test,
    categorical_feature=categorical_features,
    free_raw_data=False
)


params = {
    "objective": "binary",
    "metric": ["binary_logloss", "auc"],
    "boosting_type": "gbdt",

    "learning_rate": 0.05,
    "num_leaves": 63,
    "max_depth": -1,

    "min_data_in_leaf": 50,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 5,

    "lambda_l1": 0.1,
    "lambda_l2": 0.1,
    "scale_pos_weight": 165016 / 6063,
    "verbosity": -1,
    "seed": 42
}


model = lgb.train(
    params,
    train_data,
    num_boost_round=100,
    valid_sets=[train_data, test_data],
    valid_names=["train", "valid"],
    callbacks=[
        lgb.early_stopping(stopping_rounds=90),
        lgb.log_evaluation(period=90)
    ]
)




y_pred_proba = model.predict(X_test)

precision, recall, thresholds = precision_recall_curve(y_test, y_pred_proba)
f1 = 2 * (precision * recall) / (precision + recall + 1e-9)
best_threshold = thresholds[f1.argmax()]

print(best_threshold)

y_pred = (y_pred_proba >= best_threshold).astype(int)

print("\nRelatório de Classificação:")
print(classification_report(y_test, y_pred))

print("ROC-AUC:", roc_auc_score(y_test, y_pred_proba))

joblib.dump(model, config['ml']['models_save_path'])

print("Modelo salvo com sucesso.")