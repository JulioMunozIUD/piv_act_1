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
        self.url = "https://finance.yahoo.com/quote/NVDA/history/?period1=917015400&period2=1746855116"
        self.db_path = db_path
        self.csv_path = csv_path

    def fetch_data(self):
        logger = CustomLogger(self.__class__.__name__, 'fetch_data')
        logger.info("Fetching data from Yahoo Finance...")

        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            response = requests.get(self.url, headers=headers)
            if response.status_code != 200:
                logger.error(f"Failed to fetch data. Status code: {response.status_code}")
                return None
            return response.text
        except Exception as e:
            logger.error(f"Exception while fetching data: {e}", exc_info=True)
            return None

    def parse_data(self, html):
        logger = CustomLogger(self.__class__.__name__, 'parse_data')
        logger.info("Parsing HTML content...")

        try:
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

        except Exception as e:
            logger.error(f"Exception while parsing data: {e}", exc_info=True)
            return pd.DataFrame()


    def clean_data(self, df):
        logger = CustomLogger(self.__class__.__name__, 'clean_data')
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
            logger.error(f"Error while cleaning data: {e}", exc_info=True)
            return pd.DataFrame()


    def save_to_db(self, df):
        logger = CustomLogger(self.__class__.__name__, 'save_to_db')

        logger.info("Saving data to SQLite database...")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historical_data (
                    Date TEXT PRIMARY KEY,
                    Open REAL,
                    High REAL,
                    Low REAL,
                    Close REAL,
                    Volume REAL
                )
            ''')

            existing_dates = pd.read_sql_query("SELECT Date FROM historical_data", conn)
            existing_dates['Date'] = pd.to_datetime(existing_dates['Date'], errors='coerce')
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

            df = df[~df['Date'].isin(existing_dates['Date'])]

            if not df.empty:
                logger.info(f"Inserting {len(df)} new records into the database.")
                df.to_sql('historical_data', conn, if_exists='append', index=False)
            else:
                logger.info("No new data to insert into the database.")

        except Exception as e:
            logger.error(f"Failed to save data to database: {e}", exc_info=True)
        finally:
            conn.close()



    def save_to_csv(self, df):
        logger = CustomLogger(self.__class__.__name__, 'save_to_csv')

        try:
            os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)

            if os.path.exists(self.csv_path):
                existing_df = pd.read_csv(self.csv_path, parse_dates=['Date'], dayfirst=True)
                existing_df['Date'] = pd.to_datetime(existing_df['Date'], errors='coerce')
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

                combined_df = pd.concat([existing_df, df])
                combined_df.drop_duplicates(subset='Date', keep='last', inplace=True)

                logger.info(f"Merged with existing CSV, keeping {len(combined_df)} unique records.")
            else:
                combined_df = df
                logger.info("Creating new CSV with fresh data.")

            combined_df.to_csv(self.csv_path, index=False)
            logger.info("CSV saved successfully.")

        except Exception as e:
            logger.error(f"Failed to save CSV: {e}", exc_info=True)



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

