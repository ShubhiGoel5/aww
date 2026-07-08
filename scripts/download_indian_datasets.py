import os
import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

DATASETS = [
    {
        "name": "indian_constitution.json",
        "url": "https://raw.githubusercontent.com/Yash-Handa/The_Constitution_Of_India/main/COI.json",
        "type": "constitution"
    },
    {
        "name": "indian_penal_code.json",
        "url": "https://raw.githubusercontent.com/civictech-India/Indian-Law-Penal-Code-Json/master/ipc.json",
        "type": "act"
    }
]

def download_datasets():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    for ds in DATASETS:
        file_path = os.path.join(DATA_DIR, ds["name"])
        logger.info(f"Downloading {ds['name']} from {ds['url']}...")
        try:
            response = requests.get(ds["url"], timeout=30)
            response.raise_for_status()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
                
            logger.info(f"Successfully saved {ds['name']} to {file_path}")
        except Exception as e:
            logger.error(f"Failed to download {ds['name']}: {e}")

if __name__ == "__main__":
    download_datasets()
