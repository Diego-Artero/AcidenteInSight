import os
import sqlite3
import pandas as pd
import yaml
from src.utils import load_config
from pathlib import Path

base_dir = Path(__file__).resolve().parents[3]
config_path = base_dir / "config" / "config.yaml"
config = load_config(config_path)
# Loader function
def save_dataframes_to_sqlite(DB_PATH, df_dict, if_exists="replace"):
    
    with sqlite3.connect(DB_PATH) as conn:
        for table_name, df in df_dict.items():
            df.to_sql(table_name, conn, if_exists=if_exists, index=False)


def process_and_load_data(pessoas_path:Path,
                          veiculos_path:Path,
                          sinistros_path:Path,
                          ):
    try:
        
        BASE_DIR = Path(__file__).resolve().parents[3]
        DB_DIR = os.path.abspath(os.path.join(BASE_DIR, config['database']['save_path_processed_databases']))
        DB_PATH = os.path.join(DB_DIR, "acidentes_infosiga.db")
        os.makedirs(DB_DIR,exist_ok=True)

        
        df_pessoas = pd.read_csv(pessoas_path)
        df_veiculos = pd.read_csv(veiculos_path)
        df_sinistros = pd.read_csv(sinistros_path)

        
        save_dataframes_to_sqlite(
            DB_PATH,
            {
                "pessoas": df_pessoas,
                "veiculos": df_veiculos,
                "sinistros": df_sinistros
            },
            if_exists="replace"
        )
        print("DataFrame salvo como SQL Database com exito")
    except Exception as E:
        print("Erro na hora de salvar : ", E)
