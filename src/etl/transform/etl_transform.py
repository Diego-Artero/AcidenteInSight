import os
import pandas as pd
import yaml
from src.utils import load_config
from pathlib import Path

# Project root
BASE_DIR = Path(__file__).resolve().parents[3]

# Config path setup
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.yaml")
config = load_config(CONFIG_PATH)

# Directories

CLEANED_DIR = os.path.join(BASE_DIR, config["scraping"]["save_path_processed_cleaned"])
os.makedirs(CLEANED_DIR,exist_ok=True)
FORMATTED_DIR = os.path.join(BASE_DIR, config["scraping"]["save_path_processed_formatted"])
PESSOAS_PATH = os.path.join(FORMATTED_DIR, 'pessoas.csv')
SINISTROS_PATH = os.path.join(FORMATTED_DIR, 'sinistros.csv')
VEICULOS_PATH = os.path.join(FORMATTED_DIR, 'veiculos.csv')
PATHS = [PESSOAS_PATH,SINISTROS_PATH,VEICULOS_PATH]

def data_cleaner(paths:list[Path]):
    for PATH in paths:
        try:
            anos_remove= [2014, 2015, 2016, 2017, 2018]
            if PATH == PESSOAS_PATH:
                df = pd.read_csv(PATH)
                df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
                df['data_sinistro'] = pd.to_datetime(df['data_sinistro'], errors='coerce',dayfirst=True)
                
                df = df[df['tipo_veiculo_vitima'] != 'NAO DISPONIVEL']
                df = df[~df['ano_sinistro'].isin(anos_remove)]

            elif PATH == VEICULOS_PATH:

                df = pd.read_csv(PATH)
                df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
                df = df[df['tipo_veiculo'] != 'NAO DISPONIVEL']
                df = df[~df['ano_sinistro'].isin(anos_remove)]
            else:

                df = pd.read_csv(PATH)
                df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')

                df['data_sinistro'] = pd.to_datetime(df['data_sinistro'], errors='coerce',dayfirst=True)
                df['hora_sinistro'] = pd.to_datetime(df['hora_sinistro'], format='%H:%M', errors='coerce').dt.hour + \
                                      pd.to_datetime(df['hora_sinistro'], format='%H:%M', errors='coerce').dt.minute / 60
                df['hora_sinistro'] = df['hora_sinistro'].fillna(df['hora_sinistro'].median())

                df = df[df['tipo_registro'] != "NOTIFICACAO"]
                df = df[~df['ano_sinistro'].isin(anos_remove)]
                
                df['latitude'] = pd.to_numeric(
                df['latitude'].str.replace(',', '.', regex=False),
                errors='coerce'
                )

                df['longitude'] = pd.to_numeric(
                df['longitude'].str.replace(',', '.', regex=False),
                errors='coerce'
                )

                df = df.dropna(subset=['latitude', 'longitude'])
                df = df[
                df['latitude'].between(-90, 90) &
                df['longitude'].between(-180, 180)
                ]
            output_file = os.path.join(CLEANED_DIR, os.path.basename(PATH))
            df.to_csv(output_file, index=False)

        except Exception as e:
            print(f"Error at cleaning DataFrames: {e}")
            
if __name__ == '__main__':
    data_cleaner(PATHS)