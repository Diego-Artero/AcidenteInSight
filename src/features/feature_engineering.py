import sqlite3
import pandas as pd
import pygeohash as pgh
import numpy as np
def process_and_remove_critical_cols(dataframe: pd.DataFrame) -> pd.DataFrame:

    unused_cols_to_drop = [
                    "id_sinistro",
                    "tp_veiculo_nao_disponivel",
                    "gravidade_nao_disponivel",
                    "tp_sinistro_nao_disponivel",
                    "logradouro",
                    "numero_logradouro",
                    "ano_mes_sinistro",
                    "cod_ibge"
                ]
    
    cols_to_drop_due_to_leakage = [
                "gravidade_leve", "gravidade_grave", "gravidade_ileso", "gravidade_fatal", "qtd_gravidade_fatal",
                "qtd_gravidade_grave", "qtd_gravidade_leve", "qtd_gravidade_ileso", "qtd_gravidade_nao_disponivel"
                ]
    
    processed_cols_to_drop = [
                'tp_sinistro_primario','data_sinistro','mes_sinistro', 'dia_sinistro', 'hora_sinistro', 'ano_mes_sinistro','latitude', 'longitude', 'dia_semana_num', 'dia_da_semana'
                ]

    dataframe['mes_sinistro_sin'] = np.sin(2 * np.pi * dataframe['mes_sinistro'] / 12)
    dataframe['mes_sinistro_cos'] = np.cos(2 * np.pi * dataframe['mes_sinistro'] / 12)

    dataframe['dia_sinistro_sin'] = np.sin(2 * np.pi * dataframe['dia_sinistro'] / 31)
    dataframe['dia_sinistro_cos'] = np.cos(2 * np.pi * dataframe['dia_sinistro'] / 31)

    dataframe['hora_sinistro_sin'] = np.sin(2 * np.pi * dataframe['hora_sinistro'] / 24)
    dataframe['hora_sinistro_cos'] = np.cos(2 * np.pi * dataframe['hora_sinistro'] / 24)

    mapa = {'Segunda-feira': 0, 'Terça-feira': 1, 'Quarta-feira': 2, 'Quinta-feira': 3, 'Sexta-feira': 4, 'Sábado': 5, 'Domingo': 6}
        
    dataframe['dia_semana_num'] = dataframe['dia_da_semana'].map(mapa)

    dataframe['dia_semana_sin'] = np.sin(2 * np.pi * dataframe['dia_semana_num'] / 7)
    dataframe['dia_semana_cos'] = np.cos(2 * np.pi * dataframe['dia_semana_num'] / 7)

    dataframe["geohash"] = dataframe.apply(
        lambda row: pgh.encode(row.latitude, row.longitude, precision=6),
        axis=1
    )

    mapa = {
    'SINISTRO NAO FATAL': 0,
    'SINISTRO FATAL': 1
    }

    dataframe['tipo_registro'] = dataframe['tipo_registro'].map(mapa).astype(int)

    cols_to_drop = [col for col in unused_cols_to_drop if col in dataframe.columns] + [col for col in cols_to_drop_due_to_leakage if col in dataframe.columns] +[
        col for col in processed_cols_to_drop if col in dataframe.columns] 
    
    df = dataframe.drop(columns=cols_to_drop)
    return df

def process_and_save_feature_dataframe_as_sql(feature_db_path, dataframe: pd.DataFrame, if_exists = "replace"):

    df = process_and_remove_critical_cols(dataframe)
    
    with sqlite3.connect(feature_db_path) as conn:
        df.to_sql("sinistros", con=conn, if_exists=if_exists, index=False)

    conn.close()

import yaml

def apply_feature_schema(df, schema_path="src\\features\\schema.yaml") -> pd.DataFrame:
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)

    for col in schema.get("categorical", []):
        df[col] = df[col].astype("category")

    for col in schema.get("boolean", []):
        df[col] = df[col].astype(bool)

    return df
