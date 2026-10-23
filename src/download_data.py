from copy import error
from pathlib import Path
from datetime import datetime, timezone, timedelta

import pandas as pd
import requests

from logger_config import get_logger
logger = get_logger("food_price_watch.download")

# Public HDX dataset link
url = (
    "https://data.humdata.org/dataset/"
    "ea251823-8694-47b4-82d0-7d27f00e8aba/resource/"
    "9a842d72-0d7d-4922-ad0e-eb8106c1ab0e/download/"
    "wfp_food_prices_phl.csv"
)

data_dir = Path("data")
data_dir.mkdir(parents=True, exist_ok=True)

raw_file = data_dir / "wfp_food_prices_phl.csv"
temp_file = data_dir / "wfp_food_prices_phl.tmp"

#Function to download the csv file from the url and save it to the data directory. 
# It also validates the download by checking if the file is empty or if it has less than 2 columns. 
# If the download is successful, it replaces the existing file with the new one.
def main():

    try:
        with requests.get(url, stream=True, timeout=(15, 120)) as response:
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            total_bytes = 0

            with temp_file.open("wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        file.write(chunk)
                        total_bytes += len(chunk)

        # Validate the download before replacing the existing file.
        if total_bytes == 0:
            raise ValueError("Downloaded file is empty.")


        df_val = pd.read_csv(temp_file, nrows=5)

        if df_val.empty or len(df_val.columns) < 2:
            raise ValueError("Downloaded content does not look like a CSV.")

        temp_file.replace(raw_file)

        # Load the CSV into a DataFrame.
        df = pd.read_csv(raw_file, low_memory=False)

        logger.info(
            "Stage 1/4: Download completed | rows=%d | status=%s",
            len(df),
            "success",
        )

        return {
            "status": "success",
            "rows": len(df),
            "dataframe": df,
            "message": "Dataset downloaded and loaded successfully",
        }

    except (requests.RequestException, ValueError, pd.errors.ParserError) as e:

        return {
            "status": "failed",
            "rows": 0,
            "dataframe": None,
            "message": str(e),
        }