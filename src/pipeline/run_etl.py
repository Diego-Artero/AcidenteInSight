from src.etl.extract import download_latest_report, build_firefox_options, parse_report
from src.etl.transform import data_cleaner
from src.etl.load import save_dataframes_to_sqlite, process_and_load_data
from src.utils import load_config
from pathlib import Path
import os

base_dir = Path(__file__).resolve().parents[2]
config_path = base_dir / "config" / "config.yaml"

config = load_config(config_path)
base_url = config["scraping"]["base_url"]

download_dir = os.path.join(base_dir, config["scraping"]["save_path"])
processed_relative = config["scraping"]["save_path_processed"] 
processed_dir = os.path.join(base_dir, processed_relative)
unzipped_dir = os.path.join(processed_dir, "unzipped")
formatted_dir = os.path.join(processed_dir, "formatted")

browser_options = build_firefox_options(download_dir=download_dir)
download_latest_report(base_url=base_url, options=browser_options)

parse_report(download_dir=download_dir, unzipped_dir=unzipped_dir, formatted_dir=formatted_dir)