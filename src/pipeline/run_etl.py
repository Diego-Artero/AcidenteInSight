from src.etl.extract import download_latest_report, build_firefox_options, parse_report
from src.etl.transform import data_cleaner
from src.etl.load import save_dataframes_to_sqlite, process_and_load_data
from src.utils import load_config
from pathlib import Path
import os

#configuration setup
base_dir = Path(__file__).resolve().parents[2]
config_path = base_dir / "config" / "config.yaml"

config = load_config(config_path)
base_url = config["scraping"]["base_url"]

#extract directories
download_dir = os.path.join(base_dir, config["scraping"]["save_path"])
processed_relative = config["scraping"]["save_path_processed"] 
processed_dir = os.path.join(base_dir, processed_relative)
unzipped_dir = os.path.join(processed_dir, "unzipped")
formatted_dir = os.path.join(processed_dir, "formatted")

#transform paths
pessoas_path = os.path.join(formatted_dir, 'pessoas.csv')
sinistros_path = os.path.join(formatted_dir, 'sinistros.csv')
veiculos_path = os.path.join(formatted_dir, 'veiculos.csv')
paths = [pessoas_path,sinistros_path,veiculos_path]

#1.ETL
#1.1 Extraction
#1.1.1 Scraping
#browser_options = build_firefox_options(download_dir=download_dir)
#download_latest_report(base_url=base_url, options=browser_options)
#1.1.2 Parsing
#parse_report(download_dir=download_dir, unzipped_dir=unzipped_dir, formatted_dir=formatted_dir)

#1.2 Transform
data_cleaner(paths=paths)
