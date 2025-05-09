from src.collector import HistoricalDataCollector


if __name__ == "__main__":
    db_path = "src/static/data/historical.db"
    csv_path = "src/static/data/historical.csv"

    collector = HistoricalDataCollector(db_path, csv_path)
    collector.run()