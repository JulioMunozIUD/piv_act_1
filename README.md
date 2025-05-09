# NVIDIA Historical Data Collector

Este proyecto descarga datos históricos de NVIDIA (NVDA) desde Yahoo Finance y los almacena en una base de datos SQLite y un archivo CSV.

## Estructura del proyecto
```
├── .github/
│ └── workflows/
│ └── update_data.yml
├── docs/
│ └── report_entrega1
├── src/
│ ├── static/
│ │ ├── data/
│ │ │ ├── historical.db
│ │ │ └── historical.csv
│ │ └── models/
│ ├── collector.py
│ └── logger.py
├── setup.py
├── requirements.txt
├── README.md
└── main.py

```