import os
import zipfile
import pandas as pd
import yaml
from pathlib import Path
from src.utils import load_config

BASE_DIR = Path(__file__).resolve().parents[3]
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"

config = load_config(CONFIG_PATH)

raw_relative = config["scraping"]["save_path"] 
DOWNLOAD_DIR = os.path.join(BASE_DIR, raw_relative)

''
processed_relative = config["scraping"]["save_path_processed"] 
PROCESSED_DIR = os.path.join(BASE_DIR, processed_relative)
UNZIPPED_DIR = os.path.join(PROCESSED_DIR, "unzipped")
FORMATTED_DIR = os.path.join(PROCESSED_DIR, "formatted")

def extract_zip(zip_path, extract_dir):
    
    #Extrai o conteúdo do arquivo ZIP para o diretório especificado.
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    print(f"Arquivos extraídos para: {extract_dir}")

def parse_report(file_path):
    
    #Lê o arquivo de relatório (CSV ou Excel) e retorna um DataFrame.
    
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path, encoding='latin1', delimiter=';')
    elif file_path.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"Formato de arquivo não suportado: {file_path}")
    return df

if __name__ == "__main__":
    # O arquivo ZIP baixado deve estar na pasta raw
    zip_file = os.path.join(DOWNLOAD_DIR, "dados_infosiga.zip")
    
    # Extrair o ZIP
    extract_zip(zip_file, UNZIPPED_DIR)
    
    # Formatar corretamente os arquivos recém unzippados
    pessoas_2015_file_path = os.path.join(UNZIPPED_DIR, "pessoas_2015-2021.csv")
    pessoas_2022_file_path = os.path.join(UNZIPPED_DIR, "pessoas_2022-2025.csv")
    sinistros_2015_file_path = os.path.join(UNZIPPED_DIR, "sinistros_2015-2021.csv")
    sinistros_2022_file_path = os.path.join(UNZIPPED_DIR, "sinistros_2022-2025.csv")
    veiculos_2015_file_path = os.path.join(UNZIPPED_DIR, "veiculos_2015-2021.csv")
    veiculos_2022_file_path = os.path.join(UNZIPPED_DIR, "veiculos_2022-2025.csv")
    
    pessoas_file_path_list = [pessoas_2015_file_path, pessoas_2022_file_path]
    sinistros_file_path_list = [sinistros_2015_file_path, sinistros_2022_file_path]
    veiculos_file_path_list = [veiculos_2015_file_path, veiculos_2022_file_path]
    file_path_lists = [pessoas_file_path_list, 
                      sinistros_file_path_list,
                      veiculos_file_path_list]
    
    try:
        os.makedirs(FORMATTED_DIR, exist_ok=True)
        for file_path_list in file_path_lists:
            df = pd.DataFrame()
            for file_path in file_path_list:
                dfaux = parse_report(file_path)
                print("Preview dos dados:")
                print(dfaux.head())
                df = pd.concat([df, dfaux], ignore_index=True)
            
            if file_path_list == pessoas_file_path_list:
                output_file = os.path.join(FORMATTED_DIR, "pessoas.csv")
            elif file_path_list == sinistros_file_path_list:
                output_file = os.path.join(FORMATTED_DIR, "sinistros.csv")
            elif file_path_list == veiculos_file_path_list:
                output_file = os.path.join(FORMATTED_DIR, "veiculos.csv")
            # Salvar o DataFrame processado
         
            df.to_csv(output_file, index=False)
            

            print(f"Relatório processado salvo em: {FORMATTED_DIR}")
    except Exception as e:
        print(f"Erro ao processar o arquivo: {e}")
