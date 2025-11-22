import os
import pandas as pd
import yaml

# Project root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Config path setup
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.yaml")

def load_config(CONFIG_PATH = CONFIG_PATH):
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

config = load_config(CONFIG_PATH)

# Directories

CLEANED_DIR = os.path.join(BASE_DIR, config["scraping"]["save_path_processed_cleaned"])
FORMATTED_DIR = os.path.join(BASE_DIR, config["scraping"]["save_path_processed_formatted"])
PESSOAS_PATH = os.path.join(FORMATTED_DIR, 'pessoas.csv')
SINISTROS_PATH = os.path.join(FORMATTED_DIR, 'sinistros.csv')
VEICULOS_PATH = os.path.join(FORMATTED_DIR, 'veiculos.csv')
PATHS = [PESSOAS_PATH,SINISTROS_PATH,VEICULOS_PATH]

def data_cleaner(PATHS):
    for PATH in PATHS:
        try:
            if PATH == PESSOAS_PATH:
                df = pd.read_csv(PATH)
                df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
                df = df[df['gravidade_lesao'] != 'NÃO DISPONIVEL']

            elif PATH == VEICULOS_PATH:
                df = pd.read_csv(PATH)
                df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
                df = df[df['tipo_veiculo'] != 'NAO DISPONIVEL']

            else:
                df = pd.read_csv(PATH)
                df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')

                cols_to_drop = [
                    "id_sinistro",
                    "tp_veiculo_nao_disponivel",
                    "gravidade_nao_disponivel",
                    "tp_sinistro_nao_disponivel",
                    "logradouro",
                    "numero_logradouro",
                    "ano_mes_sinistro"
                ]
                
                cols_to_drop = [col for col in cols_to_drop if col in df.columns]
                anos_remover = [2014, 2015, 2016, 2017, 2018]

                cols_to_drop_due_to_leakage = [
                "gravidade_leve", "gravidade_grave", "gravidade_ileso", "gravidade_fatal",
                ]

                df = df.drop(columns=cols_to_drop)
                df = df.drop(columns=cols_to_drop_due_to_leakage)
                df = df[df['tipo_registro'] != "NOTIFICACAO"]
                df = df[~df['ano_sinistro'].isin(anos_remover)]
            output_file = os.path.join(CLEANED_DIR, os.path.basename(PATH))
            df.to_csv(output_file, index=False)
        except Exception as e:
            print(f"Error at cleaning DataFrames: {e}")
            
if __name__ == '__main__':
    data_cleaner(PATHS)