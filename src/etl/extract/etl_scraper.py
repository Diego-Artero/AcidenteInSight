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

# Garantir que a pasta de download exista
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Criando o perfil do Firefox para configurar o diretório de download
profile = FirefoxProfile()
profile.set_preference("browser.download.folderList", 2)
profile.set_preference("browser.download.dir", DOWNLOAD_DIR)

# Adicionando múltiplos MIME types que podem ser usados para arquivos zip
profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip, application/octet-stream, application/x-zip-compressed")
profile.set_preference("browser.download.useDownloadDir", True)
profile.set_preference("browser.download.manager.showWhenStarting", False)

# Configurar o Firefox
options = Options()
options.profile = profile

# Função para download do relatório
def download_latest_report():
    # Iniciar o serviço do GeckoDriver com o GeckoDriverManager
    geckodriver_path = GeckoDriverManager().install()
    service = Service(geckodriver_path)
    driver = webdriver.Firefox(service=service, options=options)

    try:
        driver.get(BASE_URL)
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

if __name__ == "__main__":
    download_latest_report()
