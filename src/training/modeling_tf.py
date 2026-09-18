
import os
import sqlite3
from pathlib import Path
 
import joblib
import numpy as np
import pandas as pd
import yaml
import tensorflow as tf
from tensorflow.keras import layers, Model, callbacks
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
)
 
from src.utils import load_config
from src.features import apply_feature_schema
 
# ---------------------------------------------------------------------------
# Configuração / carregamento dos dados (mesmo padrão de modeling.py)
# ---------------------------------------------------------------------------
base_dir = Path(__file__).resolve().parents[2]
config_path = base_dir / "config" / "config.yaml"
schema_path = base_dir / "src" / "features" / "schema.yaml"
 
config = load_config(config_path)
 
featured_db_path = os.path.join(
    base_dir,
    config["database"]["save_path_processed_databases"],
    "featured_acidentes_infosiga.db",
)
 
with sqlite3.connect(featured_db_path) as conn:
    df = pd.read_sql("SELECT * FROM sinistros", conn)
 
df = apply_feature_schema(df, schema_path=str(schema_path))
 
TARGET = "tipo_registro"
 
with open(schema_path, "r", encoding="utf-8") as f:
    schema = yaml.safe_load(f)
 
CATEGORICAL_COLS = schema.get("categorical", [])
BOOLEAN_COLS = schema.get("boolean", [])
NUMERIC_COLS = [
    c for c in df.columns if c not in CATEGORICAL_COLS + BOOLEAN_COLS + [TARGET]
]
 
print("Categóricas:", CATEGORICAL_COLS)
print("Booleanas:", BOOLEAN_COLS)
print("Numéricas:", NUMERIC_COLS)
 
# Colunas categóricas: garante string Python "pura" (object), tratando
# ausentes ANTES da conversão para string.
#
# Nota de compatibilidade: a partir do pandas 3.x, `.astype(str)` passou a
# devolver o dtype nullable "string" (StringArray) por padrão — e nesse
# dtype um valor ausente continua sendo um NaN de verdade (float), não a
# string literal "nan". Um `.replace({"nan": ...})` feito depois do
# astype(str) não pega esses casos, e o tf.data acaba recebendo um float
# dentro de uma coluna que deveria ser só string, o que quebra com
# "Unsupported object type float" ao montar o tf.data.Dataset. Por isso
# tratamos o ausente ANTES (via `.where`) e, em `build_feature_dict`,
# forçamos numpy puro com `.to_numpy(dtype=object)` — isso neutraliza o
# comportamento independente da versão do pandas instalada.
for col in CATEGORICAL_COLS:
    df[col] = df[col].astype(object).where(df[col].notna(), "DESCONHECIDO").map(str)
 
# ---------------------------------------------------------------------------
# Divisão one-hot x embedding, por cardinalidade observada nos dados
# ---------------------------------------------------------------------------
ONE_HOT_MAX_CARDINALITY = 15  # acima disso, usa embedding
 
cardinalities = {c: df[c].nunique() for c in CATEGORICAL_COLS}
EMBEDDING_COLS = [c for c, n in cardinalities.items() if n > ONE_HOT_MAX_CARDINALITY]
ONE_HOT_COLS = [c for c, n in cardinalities.items() if n <= ONE_HOT_MAX_CARDINALITY]
 
print("Colunas com embedding:", {c: cardinalities[c] for c in EMBEDDING_COLS})
print("Colunas com one-hot:", {c: cardinalities[c] for c in ONE_HOT_COLS})
 
# ---------------------------------------------------------------------------
# Split treino / validação / teste
# ---------------------------------------------------------------------------
X = df.drop(columns=[TARGET])
y = df[TARGET].astype(np.float32)
 
TEST_SIZE = config["ml"].get("test_size", 0.2)
RANDOM_STATE = config["ml"].get("random_state", 42)
 
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
)
X_train, X_val, y_train, y_val = train_test_split(
    X_train, y_train, test_size=0.1, random_state=RANDOM_STATE, stratify=y_train
)
 
print("Treino:", X_train.shape, "Validação:", X_val.shape, "Teste:", X_test.shape)
 
 
def build_feature_dict(X_df: pd.DataFrame) -> dict:
    """Converte um DataFrame em um dict de arrays no formato esperado
    pelos Inputs do Keras (uma coluna por chave, shape (-1, 1)).
 
    Usa to_numpy(dtype=object) para as categóricas (em vez de `.values`)
    para forçar numpy puro e evitar que ExtensionArrays do pandas
    (Categorical/StringArray) cheguem ao tf.data.Dataset — ver nota sobre
    o pandas 3.x logo acima."""
    feats = {}
    for col in CATEGORICAL_COLS:
        feats[col] = X_df[col].to_numpy(dtype=object).reshape(-1, 1)
    for col in BOOLEAN_COLS + NUMERIC_COLS:
        feats[col] = X_df[col].fillna(0).to_numpy(dtype=np.float32).reshape(-1, 1)
    return feats
 
 
def make_dataset(X_df: pd.DataFrame, y_arr: pd.Series, shuffle: bool = False, batch_size: int = 1024) -> tf.data.Dataset:
    features = build_feature_dict(X_df)
    ds = tf.data.Dataset.from_tensor_slices((features, y_arr.values.astype(np.float32)))
    if shuffle:
        ds = ds.shuffle(buffer_size=len(X_df), seed=RANDOM_STATE)
    return ds.batch(batch_size).prefetch(tf.data.AUTOTUNE)
 
 
BATCH_SIZE = 1024
train_ds = make_dataset(X_train, y_train, shuffle=True, batch_size=BATCH_SIZE)
val_ds = make_dataset(X_val, y_val, batch_size=BATCH_SIZE)
test_ds = make_dataset(X_test, y_test, batch_size=BATCH_SIZE)
 
 
def embedding_dim(cardinality: int) -> int:
    """Heurística prática (similar à usada pelo fast.ai) para o tamanho do
    embedding: cresce devagar com a cardinalidade e satura em 50."""
    return int(min(50, round(1.6 * cardinality ** 0.56)))
 
 
# ---------------------------------------------------------------------------
# Definição da arquitetura (Keras Functional API)
# ---------------------------------------------------------------------------
inputs = {}
branches = []
 
# --- Embeddings (alta cardinalidade) ---
for col in EMBEDDING_COLS:
    vocab = sorted(X_train[col].unique().tolist())
    emb_dim = embedding_dim(len(vocab))
 
    inp = layers.Input(shape=(1,), name=col, dtype=tf.string)
    lookup = layers.StringLookup(vocabulary=vocab, mask_token=None, oov_token="[UNK]")
    idx = lookup(inp)
    emb = layers.Embedding(
        input_dim=lookup.vocabulary_size(), output_dim=emb_dim, name=f"emb_{col}"
    )(idx)
    emb = layers.Flatten()(emb)
 
    inputs[col] = inp
    branches.append(emb)
 
# --- One-hot (baixa cardinalidade) ---
for col in ONE_HOT_COLS:
    vocab = sorted(X_train[col].unique().tolist())
 
    inp = layers.Input(shape=(1,), name=col, dtype=tf.string)
    lookup = layers.StringLookup(
        vocabulary=vocab, mask_token=None, oov_token="[UNK]", output_mode="one_hot"
    )
    oh = lookup(inp)  # shape (batch, len(vocab) + 1) -- já "achatado"
 
    inputs[col] = inp
    branches.append(oh)
 
# --- Booleanos (já são 0/1, entram direto) ---
for col in BOOLEAN_COLS:
    inp = layers.Input(shape=(1,), name=col, dtype=tf.float32)
    inputs[col] = inp
    branches.append(inp)
 
# --- Numéricas (normalização aprendida a partir do treino, dentro do grafo) ---
for col in NUMERIC_COLS:
    inp = layers.Input(shape=(1,), name=col, dtype=tf.float32)
    norm = layers.Normalization(name=f"norm_{col}")
    # IMPORTANTE: adapt() precisa receber os dados já no formato (-1, 1),
    # senão o Normalization aprende estatísticas por posição em vez de por
    # feature, e o shape de saída fica incompatível com o resto da rede.
    norm.adapt(X_train[col].fillna(0).values.reshape(-1, 1).astype(np.float32))
    x = norm(inp)
 
    inputs[col] = inp
    branches.append(x)
 
# --- Corpo denso ---
x = layers.Concatenate(name="concat_features")(branches)
 
x = layers.Dense(256, activation="relu")(x)
x = layers.BatchNormalization()(x)
x = layers.Dropout(0.3)(x)
 
x = layers.Dense(128, activation="relu")(x)
x = layers.BatchNormalization()(x)
x = layers.Dropout(0.2)(x)
 
x = layers.Dense(64, activation="relu")(x)
x = layers.Dropout(0.1)(x)
 
output = layers.Dense(1, activation="sigmoid", name=TARGET)(x)
 
model = Model(inputs=inputs, outputs=output, name="AcidenteInSight_NN")
 
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
    loss="binary_crossentropy",
    metrics=[
        tf.keras.metrics.AUC(name="auc"),
        tf.keras.metrics.Precision(name="precision"),
        tf.keras.metrics.Recall(name="recall"),
    ],
)
 
model.summary()
 
# ---------------------------------------------------------------------------
# Peso de classe (dataset desbalanceado: poucos sinistros fatais)
# Equivalente ao scale_pos_weight usado no LightGBM (modeling.py), mas
# calculado dinamicamente a partir do split de treino em vez de fixo.
# ---------------------------------------------------------------------------
neg, pos = np.bincount(y_train.astype(int))
class_weight = {0: 1.0, 1: neg / pos}
print("class_weight:", class_weight)
 
# ---------------------------------------------------------------------------
# Treinamento
# ---------------------------------------------------------------------------
models_dir = os.path.join(base_dir, os.path.dirname(config["ml"]["models_save_path"]))
os.makedirs(models_dir, exist_ok=True)
tf_model_path = os.path.join(models_dir, "tensorflow_model.keras")
 
training_callbacks = [
    callbacks.EarlyStopping(monitor="val_auc", mode="max", patience=10, restore_best_weights=True),
    callbacks.ModelCheckpoint(tf_model_path, monitor="val_auc", mode="max", save_best_only=True),
    callbacks.ReduceLROnPlateau(monitor="val_auc", mode="max", factor=0.5, patience=5, min_lr=1e-6),
]
 
history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=100,
    class_weight=class_weight,
    callbacks=training_callbacks,
    verbose=2,
)
 
# ---------------------------------------------------------------------------
# Avaliação (mesmo critério de threshold de modeling.py: melhor F1)
# ---------------------------------------------------------------------------
y_pred_proba = model.predict(test_ds).ravel()
 
precision, recall, thresholds = precision_recall_curve(y_test, y_pred_proba)
f1 = 2 * (precision * recall) / (precision + recall + 1e-9)
best_threshold = thresholds[f1.argmax()]
print("Melhor threshold (F1):", best_threshold)
 
y_pred = (y_pred_proba >= best_threshold).astype(int)
 
print("\nRelatório de Classificação:")
print(classification_report(y_test, y_pred))
 
print("Matriz de Confusão:\n", confusion_matrix(y_test, y_pred))
print("ROC-AUC:", roc_auc_score(y_test, y_pred_proba))
 
# ---------------------------------------------------------------------------
# Persistência
# ---------------------------------------------------------------------------
model.save(tf_model_path)
joblib.dump(
    {"threshold": float(best_threshold)},
    os.path.join(models_dir, "tensorflow_model_threshold.joblib"),
)
 
print(f"Modelo salvo em {tf_model_path}")
 
