from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
from src.utils import load_config
from pathlib import Path
import time
import os
import yaml

BASE_DIR = Path(__file__).resolve().parents[3]
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"

config = load_config(CONFIG_PATH)
BASE_URL = config["scraping"]["base_url"]
DOWNLOAD_DIR = os.path.join(BASE_DIR, config["scraping"]["save_path"])


def build_firefox_options(download_dir: Path) -> Options:
                         
    os.makedirs(download_dir, exist_ok=True)
    profile = FirefoxProfile()
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.dir", str(download_dir))
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
    profile.set_preference("browser.download.useDownloadDir", True)
    profile.set_preference("browser.download.manager.showWhenStarting", False)

    options = Options()
    
    options.profile = profile
    return options

# Scraping Function
def download_latest_report(
        base_url: str,
        options: Options,

):

    # Iniciar o serviço do GeckoDriver com o GeckoDriverManager
    geckodriver_path = GeckoDriverManager().install()
    service = Service(geckodriver_path)
    driver = webdriver.Firefox(service=service, options=options)

    try:
        driver.get(base_url)
        wait = WebDriverWait(driver, 4)  # Espera dinâmica de até 4 segundos

        # Encontrar e clicar no botão "Dados Abertos"
        dados_abertos_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div[2]/div/div[2]/section/p[1]/a")))
        dados_abertos_btn.click()
        print("Download dos Dados iniciado...")

        # Esperar alguns segundos para garantir que o download termine
        time.sleep(10)

    except Exception as e:
        print(f"Erro ao baixar o relatório: {e}")

    finally:
        driver.quit()

