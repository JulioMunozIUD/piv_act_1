import requests
import sqlite3
import pandas as pd
import traceback
from bs4 import BeautifulSoup
from datetime import datetime
from src.logger import CustomLogger
import os
import numpy as np

class HistoricalDataCollector:
    def __init__(self, db_path, csv_path):
        self.url = "https://finance.yahoo.com/quote/NVDA/history/?period1=917015400&period2=1746572858"
        self.db_path = db_path
        self.csv_path = csv_path

    def fetch_data(self):
        logger = CustomLogger("HistoricalDataCollector", "fetch_data")
        logger.info("Fetching data from Yahoo Finance...")
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(self.url, headers=headers)
        if response.status_code != 200:
            logger.error("Failed to fetch data" + traceback.format_exc())
            return None
        return response.text

    def parse_data(self, html):
        logger = CustomLogger("HistoricalDataCollector", "parse_data")
        logger.info("Parsing HTML content...")
        soup = BeautifulSoup(html, 'lxml')
        table = soup.find('table')
        rows = table.find_all('tr')

        data = []
        for row in rows[1:]:
            cols = row.find_all('td')
            if len(cols) < 6:
                continue
            try:
                parsed_row = {
                    'Date': cols[0].text.strip(),
                    'Open': cols[1].text.strip(),
                    'High': cols[2].text.strip(),
                    'Low': cols[3].text.strip(),
                    'Close': cols[4].text.strip(),
                    'Volume': cols[6].text.strip() if len(cols) > 6 else "N/A"
                }
                data.append(parsed_row)
            except Exception as e:
                logger.warning(f"Skipping row due to error: {e}")
        df = pd.DataFrame(data)
        return df

    def clean_data(self, df):
        logger = CustomLogger("HistoricalDataCollector", "clean_data")
        logger.info("Cleaning data...")

        try:
            for col in ['Open', 'High', 'Low', 'Close']:
                df[col] = df[col].str.replace(',', '').str.replace('$', '').astype(float)

            df['Volume'] = df['Volume'].replace('-', np.nan)
            df['Volume'] = df['Volume'].str.replace(',', '')
            df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')

            df['Date'] = pd.to_datetime(df['Date'], errors='coerce', format='%b %d, %Y')

            initial_rows = len(df)
            df.dropna(inplace=True)
            final_rows = len(df)
            logger.info(f"Dropped {initial_rows - final_rows} incomplete rows.")

            return df
        except Exception as e:
            logger.error(f"Error while cleaning data: {e}")
            return pd.DataFrame()

    def save_to_db(self, df):
        logger = CustomLogger("HistoricalDataCollector", "save_to_db")
        logger.info("Saving data to SQLite database...")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        if os.path.exists(self.db_path):
            logger.info(f"Overwriting existing database at {self.db_path}")
        else:
            logger.info(f"Creating new database at {self.db_path}")

        conn = sqlite3.connect(self.db_path)
        df.to_sql('historical_data', conn, if_exists='replace', index=False)
        conn.close()
        logger.info(f"Saved {len(df)} rows to database.")

    def save_to_csv(self, df):
        logger = CustomLogger("HistoricalDataCollector", "save_to_csv")
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)

        if os.path.exists(self.csv_path):
            os.remove(self.csv_path)
            logger.info(f"Overwriting existing CSV at {self.csv_path}")
        else:
            logger.info(f"Creating new CSV at {self.csv_path}")

        try:
            df.to_csv(self.csv_path, index=False, encoding='utf-8')
            logger.info(f"CSV saved successfully with {len(df)} rows.")
        except Exception as e:
            logger.error(f"Failed to save CSV: {e}"+ traceback.format_exc())

    def run(self):
        logger = CustomLogger("HistoricalDataCollector", "run")
        html = self.fetch_data()
        if html:
            df = self.parse_data(html)
            if not df.empty:
                df = self.clean_data(df)
                if not df.empty:
                    self.save_to_db(df)
                    self.save_to_csv(df)
                else:
                    logger.warning("Data cleaning resulted in an empty dataset.")
            else:
                logger.warning("No data parsed from HTML.")
        else:
            logger.error("HTML content was empty.")

