import sqlite3
import pandas as pd

def process_and_remove_critical_cols(dataframe: pd.DataFrame) -> pd.DataFrame:

    unused_cols_to_drop = [
                    "id_sinistro",
                    "tp_veiculo_nao_disponivel",
                    "gravidade_nao_disponivel",
                    "tp_sinistro_nao_disponivel",
                    "logradouro",
                    "numero_logradouro",
                    "ano_mes_sinistro"
                ]
    cols_to_drop_due_to_leakage = [
                "gravidade_leve", "gravidade_grave", "gravidade_ileso", "gravidade_fatal",
                ]
    cols_to_drop = [col for col in unused_cols_to_drop if col in dataframe.columns] + [col for col in cols_to_drop_due_to_leakage if col in dataframe.columns]

    df = dataframe.drop(columns=cols_to_drop)

    return df

def process_and_save_feature_dataframe_as_sql(feature_db_path, dataframe: pd.DataFrame, if_exists = "replace"):

    df = process_and_remove_critical_cols(dataframe)
    
    with sqlite3.connect(feature_db_path) as conn:
        df.to_sql("sinistros", con=conn, if_exists=if_exists, index=False)

    conn.close()