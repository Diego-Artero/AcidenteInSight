import os
import sqlite3
import pandas as pd
import yaml
from src.utils import load_config
from pathlib import Path

# Loader function
def save_dataframes_to_sqlite(DB_PATH, df_dict, if_exists="replace"):
    
    with sqlite3.connect(DB_PATH) as conn:
        for table_name, df in df_dict.items():
            df.to_sql(table_name, conn, if_exists=if_exists, index=False)


def process_and_load_data(pessoas_path, veiculos_path, sinistros_path, CONFIG_PATH):
    try:
        config = load_config(CONFIG_PATH)

        BASE_DIR = Path(__file__).resolve().parents[3]
        DB_DIR = os.path.abspath(os.path.join(BASE_DIR, config['database']['save_path_processed_databases']))
        DB_PATH = os.path.join(DB_DIR, "acidentes_infosiga.db")

        
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


if __name__ == "__main__":
    
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.yaml")

    config = load_config(CONFIG_PATH)

    CLEANED_DIR = os.path.join(BASE_DIR, config["scraping"]["save_path_processed_cleaned"])
    PESSOAS_PATH = os.path.join(CLEANED_DIR, 'pessoas.csv')
    SINISTROS_PATH = os.path.join(CLEANED_DIR, 'sinistros.csv')
    VEICULOS_PATH = os.path.join(CLEANED_DIR, 'veiculos.csv')
    
    process_and_load_data(
        PESSOAS_PATH,
        VEICULOS_PATH,
        SINISTROS_PATH,
        CONFIG_PATH
    )